"""
24/7 Cloud Autopilot Runner (GitHub Actions + GitHub CDN + Zapier MCP / Direct YouTube API).

Runs headless in CI (or locally) with zero paid infrastructure:
  1. Refreshes real-time US trending SEO + `<id>_seo.txt` for pending videos.
  2. Reconciles live channel uploads (`playlistItems`) into `upload_queue.json`.
  3. Uploads pending `READY_FOR_UPLOAD` videos via direct YouTube API (if `YOUTUBE_TOKEN_JSON` is set)
     or via Zapier MCP Streamable HTTP serving renders directly from `raw.githubusercontent.com`.
  4. Handles Zapier free/trial daily throttle gracefully (exits 0 so state & Telegram summary persist).
  5. Syncs analytics (when OAuth token exists) and regenerates HTML + Markdown dashboards.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from analytics_sync import sync_live
from realtime_seo import refresh_queue
from refresh_dashboard import main as refresh_dashboards
from repo_paths import AUTO_DIR, resolve_repo_path, to_raw_github_url
from telegram_logger import send_telegram
from zapier_asset_server import mark_uploaded

UPLOAD_Q = AUTO_DIR / "data" / "upload_queue.json"
TOPIC_Q = AUTO_DIR / "data" / "30day_topic_queue.json"
CHANNEL_CFG = AUTO_DIR / "data" / "channel_config.json"
PAUSE_SENTINEL = AUTO_DIR / "logs" / "PAUSE_UPLOADS"
IST = timezone(timedelta(hours=5, minutes=30))

DEFAULT_ZAPIER_URL = "https://mcp.zapier.com/api/v1/connect"
DEFAULT_CONNECTION_ID = "0223131b-a753-821b-a6ed-3cf66ef41b3e"
_YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_WATCH_ID_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})")


class ZapierError(RuntimeError):
    """Base error for Zapier MCP calls."""


class ZapierThrottledError(ZapierError):
    """Raised when Zapier rejects an action due to rate limit / free-tier throttle."""


def _is_throttle_text(text: str) -> bool:
    low = (text or "").lower()
    return any(tok in low for tok in ("throttled", "without retry", "rate limit", "too many requests", "http 429"))


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def _parse_mcp_body(raw_text: str, content_type: str) -> dict:
    """Parse Streamable HTTP MCP response whether returned as SSE events or plain JSON."""
    text = (raw_text or "").strip()
    if not text:
        return {}
    if "text/event-stream" in (content_type or "").lower() or text.startswith("event:") or "\ndata:" in text:
        last_payload: dict | None = None
        data_lines: list[str] = []
        for line in text.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
            elif not line.strip() and data_lines:
                blob = "\n".join(data_lines).strip()
                data_lines = []
                if blob and blob != "[DONE]":
                    last_payload = json.loads(blob)
        if data_lines:
            blob = "\n".join(data_lines).strip()
            if blob and blob != "[DONE]":
                last_payload = json.loads(blob)
        if last_payload is not None:
            return last_payload
    return json.loads(text)


class ZapierMcpClient:
    """Minimal pure-stdlib MCP Streamable HTTP client for Zapier MCP."""

    def __init__(self, token: str, mcp_url: str = DEFAULT_ZAPIER_URL, timeout_sec: int = 180):
        self.token = token.strip()
        self.mcp_url = mcp_url.strip()
        self.timeout_sec = timeout_sec
        self.session_id: str | None = None
        self._req_id = 0

    def _post_rpc(self, payload: dict, timeout_sec: int | None = None) -> dict:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "BabyBeatsCloudAutopilot/1.0",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        req = urllib.request.Request(self.mcp_url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec or self.timeout_sec) as resp:
                sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
                if sid:
                    self.session_id = sid.strip()
                ctype = resp.headers.get("Content-Type", "")
                raw = resp.read().decode("utf-8", errors="replace")
                return _parse_mcp_body(raw, ctype)
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429 or _is_throttle_text(err_body):
                raise ZapierThrottledError(f"HTTP {exc.code}: {err_body[:300]}") from exc
            raise ZapierError(f"HTTP {exc.code}: {err_body[:400]}") from exc

    def initialize(self) -> None:
        self._req_id += 1
        resp = self._post_rpc(
            {
                "jsonrpc": "2.0",
                "id": self._req_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "babybeats-cloud-autopilot", "version": "1.0"},
                },
            },
            timeout_sec=30,
        )
        if "error" in resp:
            raise ZapierError(f"Initialize failed: {resp['error']}")
        try:
            self._post_rpc({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, timeout_sec=15)
        except Exception:
            pass

    def call_tool(self, tool_name: str, arguments: dict, timeout_sec: int | None = None) -> tuple[dict | list | str, str]:
        if not self.session_id:
            self.initialize()
        self._req_id += 1
        resp = self._post_rpc(
            {
                "jsonrpc": "2.0",
                "id": self._req_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            },
            timeout_sec=timeout_sec or self.timeout_sec,
        )
        if "error" in resp:
            msg = json.dumps(resp["error"])
            if _is_throttle_text(msg):
                raise ZapierThrottledError(msg)
            raise ZapierError(msg)

        result = resp.get("result", {})
        parts = [c.get("text", "") for c in result.get("content", []) if isinstance(c, dict) and c.get("text")]
        raw_text = "\n".join(parts).strip()
        if result.get("isError") or _is_throttle_text(raw_text):
            if _is_throttle_text(raw_text):
                raise ZapierThrottledError(raw_text[:400])
            raise ZapierError(raw_text[:500] or "Unknown Zapier tool error")

        parsed: dict | list | str = raw_text
        if raw_text:
            try:
                parsed = json.loads(raw_text)
            except Exception:
                parsed = raw_text
        if isinstance(parsed, dict) and parsed.get("errors"):
            err_s = json.dumps(parsed["errors"])
            if _is_throttle_text(err_s):
                raise ZapierThrottledError(err_s[:400])
        return parsed, raw_text


def _extract_video_id(obj: object, raw_text: str = "") -> str | None:
    """Recursively locate a 11-character YouTube video ID inside a Zapier response."""
    if isinstance(obj, dict):
        for key in ("id", "videoId", "video_id"):
            val = obj.get(key)
            if isinstance(val, str) and _YT_ID_RE.match(val.strip()):
                return val.strip()
        for val in obj.values():
            found = _extract_video_id(val)
            if found:
                return found
    elif isinstance(obj, list):
        for elem in obj:
            found = _extract_video_id(elem)
            if found:
                return found
    m = _WATCH_ID_RE.search(raw_text or "")
    if m:
        return m.group(1)
    return None


def _extract_playlist_payload(parsed: object) -> dict:
    """Unwrap nested Zapier _zap_raw_request response into a YouTube playlistItems dict."""
    if not isinstance(parsed, dict):
        return {}
    if "items" in parsed:
        return parsed
    for key in ("results", "data", "body", "response"):
        sub = parsed.get(key)
        if isinstance(sub, list) and sub and isinstance(sub[0], dict):
            nested = _extract_playlist_payload(sub[0])
            if nested:
                return nested
        elif isinstance(sub, dict):
            nested = _extract_playlist_payload(sub)
            if nested:
                return nested
    return {}


def sync_from_channel(client: ZapierMcpClient, connection_id: str) -> dict:
    """Pull live playlistItems from YouTube and reconcile local upload/topic queues."""
    cfg = json.loads(CHANNEL_CFG.read_text(encoding="utf-8")) if CHANNEL_CFG.exists() else {}
    uq = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    ch_id = uq.get("channel_id") or cfg.get("channel_id") or ""
    if not ch_id.startswith("UC"):
        return {"synced": 0, "remote_count": 0}
    uploads_playlist = "UU" + ch_id[2:]

    remote_items: list[dict] = []
    page_token: str | None = None
    for _ in range(5):
        qs = {"part": "snippet,status", "playlistId": uploads_playlist, "maxResults": "50"}
        if page_token:
            qs["pageToken"] = page_token
        parsed, _ = client.call_tool(
            "execute_zapier_read_action",
            {
                "selected_api": "YouTubeV4CLIAPI",
                "action": "_zap_raw_request",
                "tool_name": "youtube_make_api_get_request",
                "connection_id": connection_id,
                "params": {
                    "url": "https://www.googleapis.com/youtube/v3/playlistItems",
                    "querystring": qs,
                    "fail_on_errors": False,
                },
            },
            timeout_sec=45,
        )
        payload = _extract_playlist_payload(parsed)
        remote_items.extend(payload.get("items", []))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    by_vid: dict[str, dict] = {}
    by_norm: dict[str, dict] = {}
    for rit in remote_items:
        snip = rit.get("snippet") or {}
        st = rit.get("status") or {}
        vid = (snip.get("resourceId") or {}).get("videoId") or ""
        if not vid:
            continue
        rec = {
            "video_id": vid,
            "title": snip.get("title", ""),
            "privacy": st.get("privacyStatus", "private"),
            "published_at": snip.get("publishedAt"),
        }
        by_vid[vid] = rec
        norm = _norm_title(rec["title"])
        if norm:
            by_norm[norm] = rec

    updated_ids: list[str] = []
    tq = json.loads(TOPIC_Q.read_text(encoding="utf-8")) if TOPIC_Q.exists() else {"topics": []}
    topics_by_id = {t["id"]: t for t in tq.get("topics", [])}

    for it in uq.get("items", []):
        matched = by_vid.get(it.get("youtube_video_id") or "")
        if not matched:
            cand_norms = [_norm_title(it.get("title", ""))]
            seo_p = resolve_repo_path(it.get("seo_path", ""))
            if seo_p.exists():
                try:
                    seo = json.loads(seo_p.read_text(encoding="utf-8"))
                    cand_norms.append(_norm_title(seo.get("selected_title", "")))
                    for c in seo.get("title_candidates", []):
                        cand_norms.append(_norm_title(c))
                except Exception:
                    pass
            for cn in cand_norms:
                if cn and cn in by_norm:
                    matched = by_norm[cn]
                    break
        if not matched:
            continue

        new_status = "UPLOADED" if matched["privacy"] == "public" else ("SCHEDULED" if it.get("publish_at") else "UPLOADED_PRIVATE")
        changed = (
            it.get("youtube_video_id") != matched["video_id"]
            or it.get("status") != new_status
        )
        if changed:
            it["youtube_video_id"] = matched["video_id"]
            it["youtube_url"] = f"https://www.youtube.com/watch?v={matched['video_id']}"
            it["status"] = new_status
            it.setdefault("upload_method", "zapier_mcp")
            updated_ids.append(f"{it['id']}->{new_status}")
            if it.get("format") == "short" and it.get("topic_id") in topics_by_id:
                tp = topics_by_id[it["topic_id"]]
                tp["status"] = new_status.lower()
                tp["youtube_video_id"] = matched["video_id"]
                tp["youtube_url"] = it["youtube_url"]

    if updated_ids:
        UPLOAD_Q.write_text(json.dumps(uq, indent=2, ensure_ascii=False), encoding="utf-8")
        if TOPIC_Q.exists():
            TOPIC_Q.write_text(json.dumps(tq, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"remote_count": len(remote_items), "reconciled": updated_ids}


def verify_url_accessible(url: str, timeout_sec: int = 15) -> tuple[bool, str]:
    """Check raw GitHub CDN URL serves 200 before calling Zapier upload."""
    for method, headers in (
        ("HEAD", {"User-Agent": "BabyBeatsCloudAutopilot/1.0"}),
        ("GET", {"Range": "bytes=0-0", "User-Agent": "BabyBeatsCloudAutopilot/1.0"}),
    ):
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if 200 <= resp.status < 300:
                    return True, f"{method} {resp.status}"
        except urllib.error.HTTPError as exc:
            if exc.code in (405, 501) and method == "HEAD":
                continue
            return False, f"{method} {exc.code}"
        except Exception as exc:
            if method == "HEAD":
                continue
            return False, str(exc)
    return False, "unreachable"


def build_zapier_params(item: dict, repo: str | None = None, branch: str | None = None) -> dict:
    """Build YouTube upload parameters backed by raw.githubusercontent.com HTTPS asset URLs."""
    seo = json.loads(resolve_repo_path(item["seo_path"]).read_text(encoding="utf-8"))
    yt_cfg = seo.get("youtube_settings", {})
    video_url = to_raw_github_url(item["video_path"], repo=repo, branch=branch)

    params: dict = {
        "title": seo["selected_title"][:100],
        "description": seo["description"],
        "tags": seo["tags"][:15],
        "video": video_url,
        "category_id": str(yt_cfg.get("category_id", "27")),
        "made_for_kids": bool(yt_cfg.get("made_for_kids", True)),
        "default_language": yt_cfg.get("default_language", "en"),
        "default_audio_language": yt_cfg.get("default_audio_language", "en-US"),
        "privacy_status": "private",
        "license": "youtube",
        "embeddable": True,
        "notify_subscribers": True,
        "public_stats_viewable": True,
    }

    if os.environ.get("YOUTUBE_CUSTOM_THUMBNAILS") == "1" and item.get("thumb_path"):
        thumb_url = to_raw_github_url(item["thumb_path"], repo=repo, branch=branch)
        ok_t, _ = verify_url_accessible(thumb_url)
        if ok_t:
            params["thumbnail"] = thumb_url

    pub_at = item.get("publish_at")
    if pub_at:
        try:
            pub_dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
            if pub_dt > datetime.now(timezone.utc) + timedelta(seconds=120):
                params["publish_at"] = pub_at
        except Exception:
            pass
    return params


def _upload_via_direct_api(pending: list[dict], max_uploads: int, dry_run: bool) -> tuple[list[str], str | None]:
    from youtube_direct_upload import check_deps, upload_one

    if not check_deps():
        return [], "google-api-python-client missing; skipping direct OAuth uploader"

    uploaded: list[str] = []
    for it in pending[:max_uploads]:
        iid = it["id"]
        try:
            rc = upload_one(item_id=iid, dry_run=dry_run, use_realtime_seo=False)
            if rc != 0:
                return uploaded, f"direct upload failed on {iid} (rc={rc})"
            uploaded.append(iid)
        except Exception as exc:
            msg = str(exc)
            if any(k in msg for k in ("quotaExceeded", "uploadLimitExceeded", "rateLimitExceeded")):
                print(f"YOUTUBE_API_QUOTA_REACHED: {msg}", flush=True)
                return uploaded, "youtube_quota_reached"
            raise
    return uploaded, None


def _upload_via_zapier(
    client: ZapierMcpClient | None,
    connection_id: str,
    pending: list[dict],
    max_uploads: int,
    dry_run: bool,
    repo: str | None,
    branch: str | None,
) -> tuple[list[str], bool]:
    uploaded: list[str] = []
    throttled = False

    for it in pending[:max_uploads]:
        iid = it["id"]
        params = build_zapier_params(it, repo=repo, branch=branch)
        ok_cdn, cdn_info = verify_url_accessible(params["video"])
        if not ok_cdn:
            print(f"CDN_ASSET_NOT_READY {iid}: {params['video']} ({cdn_info})", flush=True)
            continue

        if dry_run:
            print(
                json.dumps(
                    {
                        "dry_run_item": iid,
                        "cdn_status": cdn_info,
                        "video_url": params["video"],
                        "title": params["title"],
                        "publish_at": params.get("publish_at"),
                        "tags_count": len(params["tags"]),
                    },
                    indent=2,
                ),
                flush=True,
            )
            uploaded.append(f"{iid}(dry-run)")
            continue

        print(f"ZAPIER_UPLOAD_START {iid} cdn={cdn_info} publish_at={params.get('publish_at', 'private-unscheduled')}", flush=True)
        assert client is not None
        try:
            parsed, raw = client.call_tool(
                "execute_zapier_write_action",
                {
                    "selected_api": "YouTubeV4CLIAPI",
                    "action": "upload_video",
                    "tool_name": "youtube_upload_video",
                    "connection_id": connection_id,
                    "params": params,
                },
                timeout_sec=240,
            )
        except ZapierThrottledError as exc:
            print(f"ZAPIER_THROTTLED at {iid}: {exc}", flush=True)
            throttled = True
            break

        vid_id = _extract_video_id(parsed, raw)
        if not vid_id:
            raise ZapierError(f"Upload response for {iid} missing video id: {raw[:400]}")

        status = "SCHEDULED" if params.get("publish_at") else "UPLOADED_PRIVATE"
        mark_uploaded(
            iid,
            vid_id,
            status=status,
            note="Uploaded via GitHub Actions cloud_autopilot + GitHub CDN",
            upload_method="zapier_mcp_cloud",
            refresh=False,
        )
        uploaded.append(f"{iid}:{vid_id}")
        print(f"ZAPIER_UPLOAD_OK {iid} -> https://www.youtube.com/watch?v={vid_id} ({status})", flush=True)

    return uploaded, throttled


def _queue_counts() -> tuple[int, int, int, str]:
    uq = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    items = uq.get("items", [])
    total = len(items)
    done = sum(
        1 for it in items
        if it.get("status") in ("UPLOADED", "SCHEDULED", "UPLOADED_PRIVATE") or bool(it.get("youtube_video_id"))
    )
    ready = sum(1 for it in items if it.get("status") == "READY_FOR_UPLOAD" and not it.get("youtube_video_id"))
    nxt = next((it["id"] for it in items if it.get("status") == "READY_FOR_UPLOAD" and not it.get("youtube_video_id")), "ALL_DONE")
    return done, ready, total, nxt


def run_autopilot(
    max_uploads: int = 10,
    dry_run: bool = False,
    sync_only: bool = False,
    skip_seo: bool = False,
    notify: bool = True,
    repo: str | None = None,
    branch: str | None = None,
) -> int:
    if PAUSE_SENTINEL.exists() and not dry_run:
        print("CLOUD_AUTOPILOT_PAUSED: PAUSE_UPLOADS sentinel exists.", flush=True)
        return 0

    now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    seo_refreshed = 0
    if not skip_seo and not sync_only:
        res_list = refresh_queue(target_id=None, force=False)
        seo_refreshed = len(res_list)

    zapier_token = os.environ.get("ZAPIER_MCP_TOKEN", "").strip()
    connection_id = os.environ.get("ZAPIER_CONNECTION_ID", "").strip() or DEFAULT_CONNECTION_ID
    mcp_url = os.environ.get("ZAPIER_MCP_URL", "").strip() or DEFAULT_ZAPIER_URL
    has_direct_oauth = bool(os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()) or (AUTO_DIR / "creds" / "youtube_token.json").exists()

    client: ZapierMcpClient | None = None
    reconciled: list[str] = []
    throttled = False
    uploaded: list[str] = []
    note = ""

    if zapier_token:
        client = ZapierMcpClient(zapier_token, mcp_url=mcp_url)
        try:
            sync_res = sync_from_channel(client, connection_id)
            reconciled = sync_res.get("reconciled", [])
            print(f"CHANNEL_SYNC_OK remote_items={sync_res.get('remote_count')} reconciled={reconciled}", flush=True)
        except ZapierThrottledError as exc:
            throttled = True
            note = f"Channel sync throttled: {exc}"
            print(f"CHANNEL_SYNC_THROTTLED: {exc}", flush=True)
        except Exception as exc:
            print(f"CHANNEL_SYNC_WARN: {exc}", flush=True)

    uq = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    pending = [
        it for it in uq.get("items", [])
        if it.get("status") == "READY_FOR_UPLOAD" and not it.get("youtube_video_id")
    ]

    exit_code = 0
    if not sync_only and pending:
        if has_direct_oauth and not dry_run:
            print(f"UPLOAD_ENGINE=youtube_direct_api pending={len(pending)}", flush=True)
            uploaded, direct_note = _upload_via_direct_api(pending, max_uploads=max_uploads, dry_run=dry_run)
            if direct_note:
                note = direct_note
        elif (client is not None or dry_run) and not throttled:
            print(f"UPLOAD_ENGINE=zapier_mcp_cloud pending={len(pending)} repo={repo or os.environ.get('GITHUB_REPOSITORY', 'akshayxt/Faceless-Shorts')}", flush=True)
            try:
                uploaded, throttled = _upload_via_zapier(
                    client, connection_id, pending, max_uploads=max_uploads, dry_run=dry_run, repo=repo, branch=branch
                )
                if throttled:
                    note = "Zapier quota throttled; state saved and will auto-resume on next cron run"
            except ZapierError as exc:
                note = f"Zapier upload interrupted: {exc}"
                print(f"ZAPIER_UPLOAD_INTERRUPTED: {exc}", flush=True)
                if not uploaded:
                    exit_code = 1
        elif not client:
            msg = "MISSING_CREDENTIALS: Set ZAPIER_MCP_TOKEN or YOUTUBE_TOKEN_JSON secret."
            print(msg, flush=True)
            return 2

    if not dry_run:
        sync_live()
        refresh_dashboards()

    done_cnt, ready_cnt, total_cnt, next_id = _queue_counts()
    summary = (
        f"BabyBeats Cloud Autopilot ({now_ist})\n"
        f"Uploaded/Scheduled: {done_cnt}/{total_cnt} (Remaining: {ready_cnt}, Next: {next_id})\n"
        f"SEO Refreshed: {seo_refreshed} | Reconciled: {len(reconciled)} | Uploaded This Run: {len(uploaded)}\n"
        f"Items: {', '.join(uploaded) if uploaded else 'none'}\n"
        f"Note: {note or 'OK'}"
    )
    print(summary, flush=True)

    if notify and not dry_run:
        send_telegram(summary, tag="CLOUD_AUTOPILOT")

    return exit_code


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-uploads", type=int, default=10, help="Max videos to attempt per run")
    ap.add_argument("--dry-run", action="store_true", help="Verify SEO + GitHub CDN URLs without calling upload")
    ap.add_argument("--sync-only", action="store_true", help="Only reconcile channel state and refresh dashboards")
    ap.add_argument("--skip-seo", action="store_true", help="Skip live US trending SEO refresh")
    ap.add_argument("--no-notify", action="store_true", help="Do not send Telegram digest")
    ap.add_argument("--repo", help="Override GitHub owner/repo (default: GITHUB_REPOSITORY or akshayxt/Faceless-Shorts)")
    ap.add_argument("--branch", help="Override GitHub branch (default: GITHUB_REF_NAME or main)")
    args = ap.parse_args()
    return run_autopilot(
        max_uploads=args.max_uploads,
        dry_run=args.dry_run,
        sync_only=args.sync_only,
        skip_seo=args.skip_seo,
        notify=not args.no_notify,
        repo=args.repo,
        branch=args.branch,
    )


if __name__ == "__main__":
    raise SystemExit(main())
