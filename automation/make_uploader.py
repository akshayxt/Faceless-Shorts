"""
Make.com (Integromat) Secondary YouTube Video Uploader for BabyBeats Rhymo.
Acts as a manual or fallback uploader when Zapier quota is throttled.
Dispatches video metadata + raw GitHub CDN media links to a Make.com scenario webhook.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from repo_paths import AUTO_DIR, ROOT_DIR, to_raw_github_url

IST = timezone(timedelta(hours=5, minutes=30))
MAKE_CONFIG_PATH = AUTO_DIR / "data" / "make_config.json"
UPLOAD_Q_PATH = AUTO_DIR / "data" / "upload_queue.json"


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def load_make_config() -> dict:
    cfg: dict[str, Any] = {
        "enabled": True,
        "webhook_url": os.environ.get("MAKE_WEBHOOK_URL", "").strip(),
        "api_key": os.environ.get("MAKE_API_KEY", "").strip(),
        "scenario_id": os.environ.get("MAKE_SCENARIO_ID", "").strip(),
        "last_trigger_ist": None,
        "last_status": "READY_FOR_SETUP",
    }
    if MAKE_CONFIG_PATH.exists():
        try:
            stored = json.loads(MAKE_CONFIG_PATH.read_text(encoding="utf-8"))
            for k, v in stored.items():
                if v or k not in cfg:
                    cfg[k] = v
        except Exception:
            pass
    # Env var takes precedence if provided
    env_hook = os.environ.get("MAKE_WEBHOOK_URL", "").strip()
    if env_hook:
        cfg["webhook_url"] = env_hook
    return cfg


def save_make_config(cfg: dict) -> None:
    MAKE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAKE_CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def set_make_webhook_url(url: str) -> dict:
    cfg = load_make_config()
    cleaned = url.strip()
    cfg["webhook_url"] = cleaned
    cfg["enabled"] = bool(cleaned)
    cfg["last_status"] = "CONFIGURED" if cleaned else "NOT_CONFIGURED"
    save_make_config(cfg)
    return cfg


def build_make_payload(item: dict, repo: str | None = None, branch: str | None = None) -> dict:
    repo = repo or os.environ.get("GITHUB_REPOSITORY", "akshayxt/Faceless-Shorts")
    branch = branch or os.environ.get("GITHUB_BRANCH", "main")
    
    vid_rel = item.get("video_path", "").replace("\\", "/")
    if vid_rel.startswith("G:/Faceless-Shorts/"):
        vid_rel = vid_rel[len("G:/Faceless-Shorts/"):]
    elif vid_rel.startswith("videos/"):
        pass
    else:
        vid_rel = f"videos/{item['id']}/renders/{item['id']}.mp4"

    thumb_rel = item.get("thumb_path", "").replace("\\", "/")
    if thumb_rel.startswith("G:/Faceless-Shorts/"):
        thumb_rel = thumb_rel[len("G:/Faceless-Shorts/"):]
    elif thumb_rel.startswith("videos/"):
        pass
    else:
        parts = item["id"].split("_")
        day_str = f"{int(parts[0]):02d}_{parts[1]}_{parts[2]}" if len(parts) >= 3 else item["id"]
        thumb_rel = f"videos/{item['id']}/renders/{day_str}_thumb.jpg"

    video_cdn = to_raw_github_url(vid_rel, repo=repo, branch=branch)
    thumb_cdn = to_raw_github_url(thumb_rel, repo=repo, branch=branch)

    # SEO Metadata
    seo_path = ROOT_DIR / item.get("seo_path", f"videos/{item['id']}/seo_package.json")
    seo_data: dict = {}
    if seo_path.exists():
        try:
            seo_data = json.loads(seo_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    title = item.get("title") or seo_data.get("selected_title") or f"BabyBeats Rhymo Short #{item['id']}"
    desc = seo_data.get("description") or f"{title}\n\n#BabyBeats #KidsAnimation #KidsStories #Shorts"
    tags = seo_data.get("tags") or ["BabyBeats", "Kids Animation", "Moral Stories", "Kids Cartoons", "Shorts"]
    publish_at = item.get("publish_at") or item.get("scheduled_publish_est")

    return {
        "event": "youtube_upload_short",
        "service": "make_com_secondary_uploader",
        "timestamp_ist": _now_ist(),
        "item_id": item["id"],
        "title": title[:100],
        "description": desc,
        "tags": tags if isinstance(tags, list) else [t.strip() for t in str(tags).split(",") if t.strip()],
        "tags_csv": ", ".join(tags) if isinstance(tags, list) else str(tags),
        "video_url": video_cdn,
        "thumbnail_url": thumb_cdn,
        "publish_at": publish_at,
        "scheduled_slot_est": item.get("scheduled_slot_est", "15:30 EST"),
        "scheduled_publish_est": item.get("scheduled_publish_est"),
        "made_for_kids": True,
        "category_id": "27",
        "channel_id": "UCR-Di4-tEAdUM7oPzlGn-vg",
        "privacy_status": "private" if publish_at else "public"
    }


def execute_make_upload(item_id: str | None = None, max_uploads: int = 1) -> dict:
    """Send pending video project(s) to Make.com Webhook."""
    cfg = load_make_config()
    webhook_url = cfg.get("webhook_url", "").strip()
    if not webhook_url:
        return {
            "ok": False,
            "status": "NOT_CONFIGURED",
            "message": "Make.com Webhook URL is not configured. Set it via /setmake <url> or in automation/data/make_config.json."
        }

    if not UPLOAD_Q_PATH.exists():
        return {"ok": False, "status": "NO_QUEUE", "message": "upload_queue.json does not exist."}

    try:
        q_data = json.loads(UPLOAD_Q_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "status": "QUEUE_ERROR", "message": f"Failed to load upload_queue: {exc}"}

    items = q_data.get("items", [])
    if item_id:
        targets = [it for it in items if it.get("id") == item_id]
    else:
        targets = [it for it in items if it.get("status") == "READY_FOR_UPLOAD" and not it.get("youtube_video_id")]

    if not targets:
        return {"ok": True, "status": "ALL_DONE", "message": "No pending videos waiting for upload."}

    targets = targets[:max_uploads]
    uploaded_items = []
    errors = []

    for it in targets:
        iid = it["id"]
        payload = build_make_payload(it)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "BabyBeatsMakeUploader/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_bytes = resp.read()
                resp_text = resp_bytes.decode("utf-8", errors="replace")
                
                # Check for video_id in response if Make scenario returns it
                vid_id = None
                try:
                    res_json = json.loads(resp_text)
                    vid_id = res_json.get("videoId") or res_json.get("video_id") or res_json.get("id")
                except Exception:
                    pass

                generated_id = vid_id or f"make_{iid}_{int(time.time())}"
                
                # Mark item uploaded/scheduled
                it["status"] = "SCHEDULED" if it.get("publish_at") else "UPLOADED_PRIVATE"
                it["youtube_video_id"] = vid_id
                it["upload_method"] = "make_com_webhook"
                it["uploaded_at_ist"] = _now_ist()
                it["make_response"] = resp_text[:200]
                
                uploaded_items.append({
                    "id": iid,
                    "title": payload["title"],
                    "video_id": vid_id,
                    "scheduled_publish_est": it.get("scheduled_publish_est"),
                    "status": it["status"]
                })
        except Exception as exc:
            errors.append(f"{iid}: {exc}")

    if uploaded_items:
        # Save updated queue
        UPLOAD_Q_PATH.write_text(json.dumps(q_data, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # Clean local media and archive
        for up in uploaded_items:
            try:
                from auto_clean_archive import archive_single_item
                archive_single_item(up["id"])
            except Exception:
                pass

        # Update config state
        cfg["last_trigger_ist"] = _now_ist()
        cfg["last_status"] = f"SUCCESS ({len(uploaded_items)} uploaded)"
        save_make_config(cfg)

        # Refresh dashboards
        try:
            from refresh_dashboard import main as refresh_dashboards
            refresh_dashboards()
        except Exception:
            pass

    return {
        "ok": len(uploaded_items) > 0,
        "uploaded_count": len(uploaded_items),
        "uploaded_items": uploaded_items,
        "errors": errors,
        "status": "COMPLETED" if uploaded_items else "FAILED",
        "message": f"Successfully sent {len(uploaded_items)} video(s) to Make.com scenario." if uploaded_items else f"Failed to send: {', '.join(errors)}"
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--set-url":
        if len(sys.argv) > 2:
            res = set_make_webhook_url(sys.argv[2])
            print(f"Make.com Webhook URL set to: {res['webhook_url']}")
        else:
            print("Usage: python make_uploader.py --set-url <webhook_url>")
    elif len(sys.argv) > 1 and sys.argv[1] == "--run":
        res = execute_make_upload(max_uploads=1)
        print(json.dumps(res, indent=2))
    else:
        cfg = load_make_config()
        print(f"Make.com Config Status: {cfg.get('last_status')} | Webhook: {cfg.get('webhook_url') or 'NOT_SET'}")
