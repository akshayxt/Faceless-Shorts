"""
Direct YouTube Data API v3 Uploader (Unattended OAuth mode).
Used automatically by autopilot_loop.ps1 when client_secrets.json + youtube_token.json are present
inside G:\\Faceless-Shorts\\automation\\creds\\.
Enforces idempotent upload state (never re-uploads an item already marked UPLOADED).
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

AUTO = Path(r"G:\Faceless-Shorts\automation")
CREDS_DIR = AUTO / "creds"
CLIENT_SECRETS = CREDS_DIR / "client_secrets.json"
TOKEN_FILE = CREDS_DIR / "youtube_token.json"
UPLOAD_Q = AUTO / "data" / "upload_queue.json"
PAUSE_FILE = AUTO / "logs" / "PAUSE_UPLOADS"
STOP_FILE = AUTO / "logs" / "STOP_AUTOPILOT"
REFRESH_PY = AUTO / "refresh_dashboard.py"
IST = timezone(timedelta(hours=5, minutes=30))

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]


def check_deps():
    try:
        from google.oauth2.credentials import Credentials  # noqa
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa
        from googleapiclient.discovery import build  # noqa
        return True
    except ImportError:
        return False


def get_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    CREDS_DIR.mkdir(parents=True, exist_ok=True)
    if not CLIENT_SECRETS.exists() and not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"Missing OAuth credentials at {CLIENT_SECRETS}. "
            "Drop Google OAuth Desktop client_secrets.json there or upload via fresh Zapier MCP chat session."
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def pending_items() -> list[dict]:
    q = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    return [
        it for it in q.get("items", [])
        if it.get("status") not in ("UPLOADED", "SCHEDULED") and not it.get("youtube_video_id")
    ]


def refresh_item_realtime_seo(item_id: str) -> None:
    """Refresh title, description, tags from live US YouTube autocomplete + US Trends right before upload."""
    try:
        from realtime_seo import refresh_queue
        refresh_queue(target_id=item_id, force=False)
    except Exception as e:
        print(f"REALTIME_SEO_WARN {item_id}: {e}", flush=True)


def refresh_dashboards() -> None:
    if REFRESH_PY.exists():
        subprocess.run([sys.executable, str(REFRESH_PY)], check=False)


def upload_one(item_id: str | None = None, dry_run: bool = False, use_realtime_seo: bool = True):
    if PAUSE_FILE.exists() and not dry_run:
        print("UPLOAD_PAUSED: PAUSE_UPLOADS active; prioritizing video generation first.")
        return 0
    q = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    items = q.get("items", [])
    target = None
    for it in items:
        if it.get("status") in ("UPLOADED", "SCHEDULED") or it.get("youtube_video_id"):
            continue
        if item_id is None or it.get("id") == item_id:
            target = it
            break

    if not target:
        print("NO_PENDING_UPLOADS")
        return 0

    if use_realtime_seo and not dry_run:
        refresh_item_realtime_seo(target["id"])
        q = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
        target = next((it for it in q.get("items", []) if it.get("id") == target["id"]), target)

    seo = json.loads(Path(target["seo_path"]).read_text(encoding="utf-8"))
    pub_at = target.get("publish_at")
    now_utc = datetime.now(timezone.utc)
    use_schedule = False
    if pub_at:
        try:
            pub_dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
            use_schedule = pub_dt > (now_utc + timedelta(seconds=60))
        except Exception:
            use_schedule = False

    privacy = "private" if use_schedule else seo["youtube_settings"].get("privacy_status", "public")
    if dry_run:
        print(json.dumps({
            "would_upload": target["id"],
            "title": seo["selected_title"],
            "privacy_status": privacy,
            "publish_at": pub_at if use_schedule else None,
            "scheduled_est": target.get("scheduled_publish_est"),
            "file": target["video_path"]
        }, indent=2))
        return 0

    if not check_deps():
        print("MISSING_GOOGLE_API_LIBS: Install google-api-python-client google-auth-oauthlib in venv for direct OAuth mode.")
        return 2

    yt = get_service()
    from googleapiclient.http import MediaFileUpload

    status_obj = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": True,
    }
    if use_schedule and pub_at:
        status_obj["publishAt"] = pub_at

    body = {
        "snippet": {
            "title": seo["selected_title"][:100],
            "description": seo["description"],
            "tags": seo["tags"][:15],
            "categoryId": seo["youtube_settings"]["category_id"],
            "defaultLanguage": seo["youtube_settings"]["default_language"],
            "defaultAudioLanguage": seo["youtube_settings"].get("default_audio_language", "en-US"),
        },
        "status": status_obj
    }
    media = MediaFileUpload(target["video_path"], chunksize=-1, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()

    vid = resp["id"]
    if target.get("thumb_path") and Path(target["thumb_path"]).exists():
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(target["thumb_path"])).execute()
        except Exception as e:
            target["thumb_warning"] = str(e)

    target["status"] = "SCHEDULED" if use_schedule else "UPLOADED"
    target["youtube_video_id"] = vid
    target["youtube_url"] = f"https://www.youtube.com/watch?v={vid}"
    target["uploaded_at_ist"] = datetime.now(IST).isoformat()
    UPLOAD_Q.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{target['status']}_VERIFIED {target['id']} -> {target['youtube_url']} (publish_at={pub_at})")
    return 0


def main():
    from telegram_logger import wrap_if_top_level
    wrap_if_top_level("YOUTUBE_UPLOADER", __file__, sys.argv[1:])
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", help="Upload specific queue id")
    ap.add_argument("--all", action="store_true", help="Upload & schedule all pending items sequentially")
    ap.add_argument("--loop-until-done", action="store_true", help="Keep looping with retry/backoff until all items are UPLOADED or SCHEDULED")
    ap.add_argument("--no-realtime-seo", action="store_true", help="Skip live US trending SEO refresh right before upload")
    ap.add_argument("--retry-sleep", type=int, default=30, help="Seconds to sleep after transient upload failure in loop mode")
    ap.add_argument("--quota-backoff", type=int, default=1800, help="Seconds to wait on YouTube daily quota/upload limit before retry")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--auth-only", action="store_true")
    a = ap.parse_args()
    use_rt_seo = not a.no_realtime_seo

    if a.auth_only:
        get_service()
        print(f"OAuth token saved -> {TOKEN_FILE}")
        return 0

    if a.loop_until_done:
        cycle = 0
        while True:
            if STOP_FILE.exists():
                print("STOP_AUTOPILOT detected; exiting upload loop.")
                return 0
            rem = pending_items()
            if not rem:
                print("ALL_VIDEOS_UPLOADED_OR_SCHEDULED: 0 pending items left.")
                refresh_dashboards()
                return 0
            if not CLIENT_SECRETS.exists() and not TOKEN_FILE.exists():
                print(f"MISSING_OAUTH_CREDS: Place Desktop OAuth client_secrets.json in {CREDS_DIR} (remaining={len(rem)}).", flush=True)
                time.sleep(a.retry_sleep)
                continue
            cycle += 1
            print(f"UPLOAD_LOOP_CYCLE #{cycle}: remaining={len(rem)} next={rem[0]['id']}", flush=True)
            for it in rem:
                if STOP_FILE.exists():
                    return 0
                try:
                    rc = upload_one(it["id"], a.dry_run, use_realtime_seo=use_rt_seo)
                    if rc == 0:
                        refresh_dashboards()
                    else:
                        time.sleep(a.retry_sleep)
                        break
                except Exception as exc:
                    msg = str(exc)
                    print(f"UPLOAD_ERROR {it['id']}: {msg}", flush=True)
                    if any(k in msg for k in ("quotaExceeded", "uploadLimitExceeded", "rateLimitExceeded")):
                        print(f"QUOTA_BACKOFF sleeping {a.quota_backoff}s before resume...", flush=True)
                        time.sleep(a.quota_backoff)
                    else:
                        time.sleep(a.retry_sleep)
                    break
        return 0

    if a.all:
        rem = pending_items()
        for it in rem:
            rc = upload_one(it["id"], a.dry_run, use_realtime_seo=use_rt_seo)
            if rc != 0:
                return rc
        refresh_dashboards()
        return 0
    rc = upload_one(a.id, a.dry_run, use_realtime_seo=use_rt_seo)
    if rc == 0 and not a.dry_run:
        refresh_dashboards()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
