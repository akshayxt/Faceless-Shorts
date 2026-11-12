"""
Interactive Telegram Bot Dashboard & Command Center for BabyBeats Rhymo.

Integrates directly into cloud_server.py via Telegram Webhooks (/telegram/webhook) at $0 cost:
  - Interactive /dashboard with inline refresh, pagination, SEO & upload trigger buttons
  - Multiple commands: /dashboard, /status, /queue, /pending, /scheduled, /uploaded,
    /next, /seo, /seotxt, /run, /sync, /refreshseo, /pause, /resume, /links, /logs, /help
  - Fail-closed authorization via X-Telegram-Bot-Api-Secret-Token + Telegram group admin verification
  - Strictly ignores unrelated group moderation commands (e.g., /ban, /mute, /warn)
"""
import hashlib
import hmac
import html
import json
import os
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from github_sync import DEFAULT_BRANCH, DEFAULT_REPO
from repo_paths import AUTO_DIR, resolve_repo_path, to_raw_github_url
from telegram_logger import load_config as load_tg_config

IST = timezone(timedelta(hours=5, minutes=30))
UPLOAD_Q = AUTO_DIR / "data" / "upload_queue.json"
TOPIC_Q = AUTO_DIR / "data" / "30day_topic_queue.json"
GROWTH_PATH = AUTO_DIR / "data" / "growth_tracker.json"
CHANNEL_CFG = AUTO_DIR / "data" / "channel_config.json"
BOT_SETTINGS_PATH = AUTO_DIR / "data" / "bot_settings.json"

DEFAULT_PUBLIC_URL = "https://babybeats-cloud-autopilot.onrender.com"
PAGE_SIZE = 8
_ADMIN_CACHE: dict[int, tuple[bool, float]] = {}
_BOT_USERNAME: str = ""

BOT_COMMANDS: list[dict[str, str]] = [
    {"command": "dashboard", "description": "Interactive growth, upload & server cockpit"},
    {"command": "status", "description": "Cloud runner health, cron & commit telemetry"},
    {"command": "queue", "description": "Browse all 31 videos with status & links"},
    {"command": "pending", "description": "Show remaining READY_FOR_UPLOAD videos"},
    {"command": "scheduled", "description": "Show YouTube scheduled videos & times"},
    {"command": "uploaded", "description": "Show live published YouTube videos"},
    {"command": "next", "description": "Spotlight next video in upload queue"},
    {"command": "seo", "description": "Show real-time US SEO package (/seo day09_short)"},
    {"command": "seotxt", "description": "Send downloadable *_seo.txt file (/seotxt day09_short)"},
    {"command": "run", "description": "Start cloud SEO + YouTube upload cycle now"},
    {"command": "sync", "description": "Reconcile live YouTube channel + refresh dashboards"},
    {"command": "refreshseo", "description": "Refresh real-time US trending SEO for pending items"},
    {"command": "pause", "description": "Pause automatic uploads cleanly"},
    {"command": "resume", "description": "Resume automatic uploads"},
    {"command": "links", "description": "Web dashboard, health API, channel & repo links"},
    {"command": "logs", "description": "Latest cloud execution & GitHub sync details"},
    {"command": "help", "description": "Show all BabyBeats bot commands"},
]
_KNOWN_CMD_SET = {c["command"] for c in BOT_COMMANDS} | {"start", "dash", "panel"}


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def get_bot_settings() -> dict:
    data = _read_json(BOT_SETTINGS_PATH, {})
    return {
        "paused": bool(data.get("paused", False)),
        "updated_at_ist": data.get("updated_at_ist", "never"),
        "updated_by": data.get("updated_by", "default"),
    }


def set_bot_paused(paused: bool, actor: str) -> dict:
    payload = {
        "paused": bool(paused),
        "updated_at_ist": _now_ist(),
        "updated_by": actor,
    }
    BOT_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOT_SETTINGS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def webhook_secret(bot_token: str | None = None, cron_secret: str | None = None) -> str:
    explicit = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if explicit:
        return explicit
    tok = (bot_token if bot_token is not None else str(load_tg_config().get("bot_token", ""))).strip()
    cron = (cron_secret if cron_secret is not None else os.environ.get("CRON_SECRET", "")).strip()
    if not tok:
        return ""
    seed = f"{cron}:{tok}".encode("utf-8")
    return hmac.new(b"babybeats-telegram-webhook-v1", seed, hashlib.sha256).hexdigest()[:48]


def verify_webhook_header(headers: Any) -> bool:
    expected = webhook_secret()
    if not expected:
        return False
    supplied = (headers.get("X-Telegram-Bot-Api-Secret-Token") or "").strip()
    return bool(supplied and hmac.compare_digest(supplied, expected))


def tg_api(method: str, params: dict | None = None, bot_token: str | None = None, timeout: int = 15) -> dict:
    tok = (bot_token or str(load_tg_config().get("bot_token", ""))).strip()
    if not tok:
        return {"ok": False, "description": "Missing TELEGRAM_BOT_TOKEN"}
    url = f"https://api.telegram.org/bot{tok}/{method}"
    data = json.dumps(params or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "error_code": exc.code, "description": body}
    except Exception as exc:
        return {"ok": False, "description": str(exc)}


def tg_send_document(chat_id: int | str, file_path: Path, caption: str = "", reply_to_message_id: int | None = None) -> dict:
    """Upload a local text/report file cleanly to Telegram via multipart/form-data."""
    tok = str(load_tg_config().get("bot_token", "")).strip()
    if not tok or not file_path.exists():
        return {"ok": False, "description": "Missing bot token or file"}
    boundary = f"----BabyBeatsBoundary{uuid.uuid4().hex}"
    parts: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode("utf-8"))

    add_field("chat_id", str(chat_id))
    if caption:
        add_field("caption", caption[:1024])
        add_field("parse_mode", "HTML")
    if reply_to_message_id:
        add_field("reply_to_message_id", str(reply_to_message_id))

    file_bytes = file_path.read_bytes()
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{file_path.name}\"\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n\r\n".encode("utf-8")
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode("utf-8")
    )
    body = b"".join(parts)
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Content-Length": str(len(body))},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error_code": exc.code, "description": exc.read().decode("utf-8", errors="replace")}
    except Exception as exc:
        return {"ok": False, "description": str(exc)}


def public_base_url() -> str:
    return (
        os.environ.get("PUBLIC_BASE_URL", "").strip()
        or os.environ.get("RENDER_EXTERNAL_URL", "").strip()
        or DEFAULT_PUBLIC_URL
    ).rstrip("/")


def register_telegram_bot(base_url: str | None = None) -> dict:
    """Register bot username, command autocomplete menu, and Render webhook automatically."""
    global _BOT_USERNAME
    cfg = load_tg_config()
    tok = str(cfg.get("bot_token", "")).strip()
    if not tok:
        return {"ok": False, "skipped": "missing TELEGRAM_BOT_TOKEN"}

    me = tg_api("getMe", bot_token=tok)
    if me.get("ok"):
        _BOT_USERNAME = str((me.get("result") or {}).get("username") or "").lower()

    cmd_default = tg_api("setMyCommands", {"commands": BOT_COMMANDS}, bot_token=tok)
    cmd_admins = tg_api(
        "setMyCommands",
        {"commands": BOT_COMMANDS, "scope": {"type": "all_chat_administrators"}},
        bot_token=tok,
    )

    target_url = f"{(base_url or public_base_url()).rstrip('/')}/telegram/webhook"
    sec = webhook_secret(bot_token=tok)
    wh_res = tg_api(
        "setWebhook",
        {
            "url": target_url,
            "secret_token": sec,
            "allowed_updates": ["message", "callback_query"],
            "drop_pending_updates": False,
        },
        bot_token=tok,
    )
    return {"ok": bool(wh_res.get("ok")), "bot_username": _BOT_USERNAME, "commands_default": cmd_default.get("ok"), "commands_admins": cmd_admins.get("ok"), "webhook": wh_res}


def is_authorized_actor(user_id: int | None, chat_id: int | str, chat_type: str) -> bool:
    """Allow only configured admins (or group admins of TELEGRAM_CHAT_ID) in the primary group or DM."""
    if not user_id:
        return False
    cfg = load_tg_config()
    primary_chat = str(cfg.get("chat_id", "")).strip()
    if chat_type != "private" and str(chat_id) != primary_chat:
        return False

    explicit = {x.strip() for x in os.environ.get("TELEGRAM_ADMIN_IDS", "").split(",") if x.strip()}
    if explicit:
        return str(user_id) in explicit

    now = time.monotonic()
    cached = _ADMIN_CACHE.get(user_id)
    if cached and cached[1] > now:
        return cached[0]

    if not primary_chat:
        return False
    res = tg_api("getChatMember", {"chat_id": primary_chat, "user_id": user_id})
    status = str((res.get("result") or {}).get("status") or "")
    allowed = bool(res.get("ok") and status in ("creator", "administrator"))
    _ADMIN_CACHE[user_id] = (allowed, now + 300.0)
    return allowed


def _parse_command(text: str, bot_username: str) -> tuple[str | None, str]:
    raw = (text or "").strip()
    if not raw.startswith("/"):
        return None, ""
    head, _, rest = raw.partition(" ")
    cmd_token = head[1:]
    if "@" in cmd_token:
        cmd_name, target_bot = cmd_token.split("@", 1)
        if bot_username and target_bot.lower() != bot_username.lower():
            return None, ""
    else:
        cmd_name = cmd_token
    cmd = cmd_name.strip().lower()
    if cmd not in _KNOWN_CMD_SET:
        return None, ""
    return cmd, rest.strip()


def _progress_bar(done: int, total: int, width: int = 16) -> str:
    if total <= 0:
        return "[" + ("░" * width) + "] 0%"
    pct = int(round((done / total) * 100))
    filled = int(round((done / total) * width))
    return f"[{'█' * filled}{'░' * max(0, width - filled)}] {pct}%"


def _load_queue_snapshot() -> dict:
    uq = _read_json(UPLOAD_Q, {"items": []})
    tq = _read_json(TOPIC_Q, {"topics": []})
    growth = _read_json(GROWTH_PATH, {})
    items = uq.get("items", [])
    uploaded = [it for it in items if it.get("status") == "UPLOADED"]
    scheduled = [it for it in items if it.get("status") == "SCHEDULED"]
    private_only = [it for it in items if it.get("status") == "UPLOADED_PRIVATE"]
    pending = [it for it in items if it.get("status") == "READY_FOR_UPLOAD" and not it.get("youtube_video_id")]
    done_cnt = len(uploaded) + len(scheduled) + len(private_only)
    next_item = pending[0] if pending else None
    return {
        "uq": uq,
        "tq": tq,
        "growth": growth,
        "items": items,
        "uploaded": uploaded,
        "scheduled": scheduled,
        "private_only": private_only,
        "pending": pending,
        "done_cnt": done_cnt,
        "total_cnt": len(items),
        "next_item": next_item,
    }


def _dashboard_keyboard(paused: bool) -> dict:
    base = public_base_url()
    gh_repo = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO)
    toggle_btn = (
        {"text": "▶ Resume Uploads", "callback_data": "cb:resume"}
        if paused
        else {"text": "⏸ Pause Uploads", "callback_data": "cb:pause"}
    )
    return {
        "inline_keyboard": [
            [
                {"text": "🔄 Refresh", "callback_data": "cb:dash"},
                {"text": "📋 Queue", "callback_data": "cb:queue:all:0"},
                {"text": "⏭ Next Video", "callback_data": "cb:next"},
            ],
            [
                {"text": "▶ Run Cycle", "callback_data": "cb:run"},
                {"text": "🔎 Sync YouTube", "callback_data": "cb:sync"},
                {"text": "🔍 Refresh SEO", "callback_data": "cb:seo"},
            ],
            [
                toggle_btn,
                {"text": "📊 Server Status", "callback_data": "cb:status"},
            ],
            [
                {"text": "🌐 Web Dashboard", "url": f"{base}/dashboard"},
                {"text": "📁 GitHub Repo", "url": f"https://github.com/{gh_repo}"},
            ],
        ]
    }


def build_dashboard_view(server_state: dict) -> tuple[str, dict]:
    snap = _load_queue_snapshot()
    growth = snap["growth"]
    uq = snap["uq"]
    settings = get_bot_settings()
    paused = settings["paused"]

    cur_subs = int(growth.get("current_subscribers", 0))
    target_subs = int(growth.get("target_net_subscribers", 5000))
    end_date = growth.get("campaign_end_date", "2026-12-09")
    rem_days = max(1, (datetime.fromisoformat(end_date + "T23:59:59+05:30").date() - datetime.now(IST).date()).days)
    req_day = round(max(0, target_subs - cur_subs) / rem_days, 1)

    nxt = snap["next_item"]
    nxt_line = (
        f"<code>{html.escape(nxt['id'])}</code> · {html.escape(nxt.get('title', '')[:48])}\n"
        f"   Slot: <code>{html.escape(str(nxt.get('scheduled_publish_est', '—')))}</code> · SEO: <b>{nxt.get('realtime_seo_score', '—')}/100</b>"
        if nxt
        else "<b>ALL 31 VIDEOS UPLOADED / SCHEDULED!</b>"
    )
    run_badge = "🔄 Running now" if server_state.get("running") else ("⏸ Paused" if paused else "✅ Active (24/7 Cloud)")
    last_sync = str(uq.get("realtime_seo_last_sync_ist") or "Pending")[:19].replace("T", " ")
    last_run = server_state.get("last_run_ist") or "Never yet"

    text = (
        f"🚀 <b>BabyBeats Rhymo — Cloud Growth Dashboard</b>\n"
        f"<i>US English (en-US) · YouTube + Render + GitHub</i>\n\n"
        f"📊 <b>Upload Progress:</b> <code>{_progress_bar(snap['done_cnt'], snap['total_cnt'])}</code>\n"
        f"• 🟢 Live Public: <b>{len(snap['uploaded'])}</b>\n"
        f"• 🗓 Scheduled: <b>{len(snap['scheduled']) + len(snap['private_only'])}</b>\n"
        f"• ⏳ Remaining: <b>{len(snap['pending'])}</b> / {snap['total_cnt']}\n\n"
        f"🎯 <b>5K Sub Target:</b> <b>{cur_subs}</b> / {target_subs} ({rem_days}d left · <code>{req_day}/day</code> needed)\n"
        f"☁️ <b>Engine State:</b> {run_badge}\n"
        f"🕒 <b>Last Cloud Run:</b> <code>{html.escape(str(last_run))}</code>\n"
        f"📈 <b>Last US SEO Sync:</b> <code>{html.escape(last_sync)} IST</code>\n\n"
        f"⏭ <b>Next Up:</b> {nxt_line}"
    )
    return text, _dashboard_keyboard(paused)


def build_status_view(server_state: dict) -> tuple[str, dict]:
    snap = _load_queue_snapshot()
    settings = get_bot_settings()
    last_sync = server_state.get("last_sync") or {}
    push_info = last_sync.get("push") or {}
    sha = str(push_info.get("sha") or "none")[:10]
    files_cnt = len(push_info.get("files") or [])
    err = server_state.get("last_error") or "None"

    text = (
        f"🩺 <b>Cloud Server Telemetry</b>\n\n"
        f"• <b>Host:</b> Render Free Web Service + <code>cron-job.org</code>\n"
        f"• <b>Time:</b> <code>{_now_ist()}</code>\n"
        f"• <b>Worker Running:</b> <code>{server_state.get('running')}</code>\n"
        f"• <b>Auto-Uploads Paused:</b> <code>{settings['paused']}</code> ({html.escape(str(settings['updated_by']))})\n"
        f"• <b>Completed Runs:</b> <b>{server_state.get('runs_completed', 0)}</b>\n"
        f"• <b>Last Start:</b> <code>{html.escape(str(server_state.get('last_run_ist') or '—'))}</code>\n"
        f"• <b>Last Finish:</b> <code>{html.escape(str(server_state.get('last_finish_ist') or '—'))}</code>\n"
        f"• <b>Last Exit Code:</b> <code>{server_state.get('last_exit_code')}</code>\n"
        f"• <b>Last GitHub Commit:</b> <code>{html.escape(sha)}</code> ({files_cnt} files)\n"
        f"• <b>Queue:</b> {snap['done_cnt']}/{snap['total_cnt']} done ({len(snap['pending'])} left)\n"
        f"• <b>Last Error:</b> <code>{html.escape(str(err)[:180])}</code>"
    )
    kb = {
        "inline_keyboard": [
            [{"text": "🔄 Refresh Status", "callback_data": "cb:status"}, {"text": "🔙 Dashboard", "callback_data": "cb:dash"}],
            [{"text": "▶ Trigger /run Now", "callback_data": "cb:run"}],
        ]
    }
    return text, kb


def build_queue_view(flt: str = "all", page: int = 0) -> tuple[str, dict]:
    snap = _load_queue_snapshot()
    items = snap["items"]
    if flt == "pending":
        filtered = snap["pending"]
        label = "Pending Uploads"
    elif flt == "scheduled":
        filtered = snap["scheduled"] + snap["private_only"]
        label = "Scheduled Videos"
    elif flt == "uploaded":
        filtered = snap["uploaded"]
        label = "Live Public Videos"
    else:
        flt = "all"
        filtered = items
        label = "All Videos"

    total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    chunk = filtered[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

    lines = [f"📋 <b>{label}</b> ({len(filtered)} total · Page {page + 1}/{total_pages})\n"]
    icon_map = {"UPLOADED": "🟢", "SCHEDULED": "🗓", "UPLOADED_PRIVATE": "🔒", "READY_FOR_UPLOAD": "⏳"}
    for it in chunk:
        ico = icon_map.get(it.get("status", ""), "❔")
        title = html.escape(str(it.get("title", ""))[:44])
        sched = str(it.get("scheduled_publish_est", "—"))[:10]
        sc = it.get("realtime_seo_score", "—")
        yt_url = it.get("youtube_url")
        if yt_url:
            link_part = f" · <a href=\"{html.escape(yt_url)}\">Watch</a>"
        else:
            link_part = f" · <code>{sched}</code>"
        lines.append(f"{ico} <code>{html.escape(it['id'])}</code> ({sc}/100){link_part}\n   {title}")

    if not chunk:
        lines.append("<i>No videos in this filter yet.</i>")

    nav_row = []
    if page > 0:
        nav_row.append({"text": "◀ Prev", "callback_data": f"cb:queue:{flt}:{page - 1}"})
    if page + 1 < total_pages:
        nav_row.append({"text": "Next ▶", "callback_data": f"cb:queue:{flt}:{page + 1}"})

    filter_row = [
        {"text": "All", "callback_data": "cb:queue:all:0"},
        {"text": "⏳ Pending", "callback_data": "cb:queue:pending:0"},
        {"text": "🗓 Sched", "callback_data": "cb:queue:scheduled:0"},
        {"text": "🟢 Live", "callback_data": "cb:queue:uploaded:0"},
    ]
    rows = [filter_row]
    if nav_row:
        rows.append(nav_row)
    rows.append([{"text": "🔙 Back to Dashboard", "callback_data": "cb:dash"}])
    return "\n".join(lines), {"inline_keyboard": rows}


def _find_item(item_id: str = "") -> dict | None:
    snap = _load_queue_snapshot()
    q = item_id.strip().lower()
    if q:
        for it in snap["items"]:
            if it["id"].lower() == q or it["id"].lower().startswith(q):
                return it
    return snap["next_item"] or (snap["items"][0] if snap["items"] else None)


def build_next_or_seo_view(item_id: str = "", include_desc: bool = False) -> tuple[str, dict, dict | None]:
    it = _find_item(item_id)
    if not it:
        return "No videos found in queue.", {"inline_keyboard": [[{"text": "🔙 Dashboard", "callback_data": "cb:dash"}]]}, None

    seo = _read_json(resolve_repo_path(it.get("seo_path", "")), {})
    title = seo.get("selected_title") or it.get("title", "")
    score = (seo.get("selected_title_lint") or {}).get("score", it.get("realtime_seo_score", "—"))
    queries = ", ".join(seo.get("target_search_queries", [])[:5]) or "—"
    hashtags = " ".join(seo.get("hashtags", [])[:6]) or "—"
    tags = ", ".join(seo.get("tags", [])[:8]) or "—"
    cdn_url = to_raw_github_url(it.get("video_path", ""))

    header = "🔍 <b>Real-Time US SEO Package</b>" if include_desc else "⏭ <b>Next Video Spotlight</b>"
    desc_block = ""
    if include_desc and seo.get("description"):
        desc_snip = html.escape(str(seo["description"])[:500])
        desc_block = f"\n\n📝 <b>Description Preview:</b>\n<pre>{desc_snip}</pre>"

    text = (
        f"{header}: <code>{html.escape(it['id'])}</code>\n\n"
        f"📌 <b>Title:</b> {html.escape(title)}\n"
        f"• <b>Status:</b> <code>{html.escape(it.get('status', '—'))}</code>\n"
        f"• <b>SEO Score:</b> <b>{score}/100</b>\n"
        f"• <b>US Schedule:</b> <code>{html.escape(str(it.get('scheduled_publish_est', '—')))}</code>\n"
        f"• <b>Trending Queries:</b> <code>{html.escape(queries)}</code>\n"
        f"• <b>Hashtags:</b> {html.escape(hashtags)}\n"
        f"• <b>Keywords:</b> <code>{html.escape(tags)}</code>\n"
        f"• <b>CDN Video:</b> <a href=\"{html.escape(cdn_url)}\">{html.escape(it['id'])}.mp4</a>"
        f"{desc_block}"
    )
    kb = {
        "inline_keyboard": [
            [
                {"text": "📄 Send SEO.txt File", "callback_data": f"cb:seodoc:{it['id']}"},
                {"text": "▶ Run Upload Now", "callback_data": "cb:run"},
            ],
            [{"text": "📋 Queue", "callback_data": "cb:queue:all:0"}, {"text": "🔙 Dashboard", "callback_data": "cb:dash"}],
        ]
    }
    return text, kb, it


def _send_seo_document(chat_id: int | str, item_id: str = "", reply_to: int | None = None) -> tuple[bool, str]:
    it = _find_item(item_id)
    if not it:
        return False, "No matching video id found."
    txt_rel = it.get("seo_txt_path")
    candidates = []
    if txt_rel:
        candidates.append(resolve_repo_path(txt_rel))
    vid_p = resolve_repo_path(it.get("video_path", ""))
    candidates.extend([vid_p.parent / f"{it['id']}_seo.txt", resolve_repo_path(it.get("seo_path", "")).parent / "seo.txt"])
    target = next((p for p in candidates if p.exists() and p.is_file()), None)
    if not target:
        return False, f"SEO text file missing on disk for `{it['id']}`."
    res = tg_send_document(
        chat_id,
        target,
        caption=f"📄 Real-Time US SEO file for <code>{html.escape(it['id'])}</code>",
        reply_to_message_id=reply_to,
    )
    return bool(res.get("ok")), str(res.get("description") or "Sent")


def build_help_view() -> tuple[str, dict]:
    lines = ["🤖 <b>BabyBeats Rhymo — Bot Command Center</b>\n"]
    for entry in BOT_COMMANDS:
        lines.append(f"/{entry['command']} — {html.escape(entry['description'])}")
    lines.append("\n<i>All cloud actions run on Render + sync state to GitHub even when your PC is off.</i>")
    kb = {
        "inline_keyboard": [
            [{"text": "🚀 Open Dashboard", "callback_data": "cb:dash"}, {"text": "📋 Queue", "callback_data": "cb:queue:all:0"}],
            [{"text": "🌐 Web Cockpit", "url": f"{public_base_url()}/dashboard"}],
        ]
    }
    return "\n".join(lines), kb


def build_links_view() -> tuple[str, dict]:
    base = public_base_url()
    gh_repo = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO)
    cfg = _read_json(CHANNEL_CFG, {})
    ch_id = cfg.get("channel_id", "UCR-Di4-tEAdUM7oPzlGn-vg")
    text = (
        f"🔗 <b>BabyBeats Cloud Links</b>\n\n"
        f"• 🌐 <a href=\"{base}/dashboard\">Live Web Dashboard</a>\n"
        f"• 🩺 <a href=\"{base}/health\">Server Health JSON</a>\n"
        f"• 📺 <a href=\"https://www.youtube.com/channel/{ch_id}\">BabyBeats Rhymo YouTube</a>\n"
        f"• 📁 <a href=\"https://github.com/{gh_repo}\">GitHub Repo ({gh_repo})</a>"
    )
    kb = {
        "inline_keyboard": [
            [{"text": "🌐 Open Dashboard", "url": f"{base}/dashboard"}, {"text": "📺 YouTube Channel", "url": f"https://www.youtube.com/channel/{ch_id}"}],
            [{"text": "🔙 Back to Bot Dashboard", "callback_data": "cb:dash"}],
        ]
    }
    return text, kb


def _dispatch_message(chat_id: int | str, text: str, reply_markup: dict | None = None, reply_to: int | None = None) -> dict:
    payload: dict[str, Any] = {
        "chat_id": str(chat_id),
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    return tg_api("sendMessage", payload)


def _edit_message(chat_id: int | str, message_id: int, text: str, reply_markup: dict | None = None) -> dict:
    payload: dict[str, Any] = {
        "chat_id": str(chat_id),
        "message_id": message_id,
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_api("editMessageText", payload)


def handle_webhook_update(
    update: dict,
    get_state: Callable[[], dict],
    trigger_cycle: Callable[..., dict],
    sync_github_fn: Callable[[str], dict],
) -> dict:
    """Process one Telegram Message or CallbackQuery update cleanly without blocking HTTP response."""
    global _BOT_USERNAME
    if not _BOT_USERNAME:
        me = tg_api("getMe")
        if me.get("ok"):
            _BOT_USERNAME = str((me.get("result") or {}).get("username") or "").lower()

    if "callback_query" in update:
        cq = update["callback_query"]
        cq_id = cq.get("id")
        from_u = cq.get("from") or {}
        msg = cq.get("message") or {}
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        msg_id = msg.get("message_id")
        data = str(cq.get("data") or "")

        if not is_authorized_actor(from_u.get("id"), chat_id, str(chat.get("type") or "")):
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": "Admins only.", "show_alert": True})
            return {"handled": "unauthorized_callback"}

        if data == "cb:dash":
            text, kb = build_dashboard_view(get_state())
            _edit_message(chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": "Dashboard refreshed"})
        elif data == "cb:status":
            text, kb = build_status_view(get_state())
            _edit_message(chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data.startswith("cb:queue:"):
            parts = data.split(":")
            flt = parts[2] if len(parts) > 2 else "all"
            page = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
            text, kb = build_queue_view(flt, page)
            _edit_message(chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data == "cb:next":
            text, kb, _ = build_next_or_seo_view("", include_desc=False)
            _edit_message(chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data.startswith("cb:seodoc:"):
            iid = data.split(":", 2)[2]
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": f"Sending SEO file for {iid}..."})
            threading.Thread(target=_send_seo_document, args=(chat_id, iid, msg_id), daemon=True).start()
        elif data in ("cb:run", "cb:sync", "cb:seo"):
            sync_only = data == "cb:sync"
            label = "YouTube sync + SEO refresh" if sync_only else ("Real-time US SEO refresh" if data == "cb:seo" else "Cloud upload + SEO cycle")
            res = trigger_cycle(
                max_uploads=10,
                sync_only=(data in ("cb:sync", "cb:seo")),
                skip_seo=(data == "cb:sync"),
                reply_chat_id=chat_id,
            )
            pop = f"🚀 Started: {label}" if res.get("started") else "⏳ A cloud cycle is already running"
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": pop})
            text, kb = build_dashboard_view(get_state())
            _edit_message(chat_id, msg_id, text, kb)
        elif data in ("cb:pause", "cb:resume"):
            actor = from_u.get("username") or str(from_u.get("id"))
            paused = data == "cb:pause"
            set_bot_paused(paused, actor=f"@{actor}")
            threading.Thread(
                target=sync_github_fn,
                args=(f"chore(bot): {'pause' if paused else 'resume'} auto uploads [skip render] [skip ci]",),
                daemon=True,
            ).start()
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": "Uploads paused ⏸" if paused else "Uploads resumed ▶"})
            text, kb = build_dashboard_view(get_state())
            _edit_message(chat_id, msg_id, text, kb)
        else:
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        return {"handled": f"callback:{data}"}

    msg = update.get("message")
    if not msg or not msg.get("text"):
        return {"handled": "ignored_non_text"}

    cmd, arg = _parse_command(msg["text"], _BOT_USERNAME)
    if not cmd:
        return {"handled": "ignored_non_bot_cmd"}

    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    msg_id = msg.get("message_id")
    from_u = msg.get("from") or {}

    if not is_authorized_actor(from_u.get("id"), chat_id, str(chat.get("type") or "")):
        return {"handled": "unauthorized_message"}

    if cmd in ("start", "help"):
        text, kb = build_help_view()
        _dispatch_message(chat_id, text, kb, reply_to=msg_id)
    elif cmd in ("dashboard", "dash", "panel"):
        text, kb = build_dashboard_view(get_state())
        _dispatch_message(chat_id, text, kb, reply_to=msg_id)
    elif cmd in ("status", "logs"):
        text, kb = build_status_view(get_state())
        _dispatch_message(chat_id, text, kb, reply_to=msg_id)
    elif cmd in ("queue", "pending", "scheduled", "uploaded"):
        flt = "all" if cmd == "queue" else cmd
        page = (int(arg) - 1) if arg.isdigit() and int(arg) > 0 else 0
        text, kb = build_queue_view(flt, page)
        _dispatch_message(chat_id, text, kb, reply_to=msg_id)
    elif cmd == "next":
        text, kb, _ = build_next_or_seo_view("", include_desc=False)
        _dispatch_message(chat_id, text, kb, reply_to=msg_id)
    elif cmd == "seo":
        text, kb, _ = build_next_or_seo_view(arg, include_desc=True)
        _dispatch_message(chat_id, text, kb, reply_to=msg_id)
    elif cmd == "seotxt":
        ok, info = _send_seo_document(chat_id, arg, reply_to=msg_id)
        if not ok:
            _dispatch_message(chat_id, f"⚠️ {html.escape(info)}", reply_to=msg_id)
    elif cmd in ("run", "sync", "refreshseo"):
        max_up = int(arg) if arg.isdigit() else 10
        max_up = max(1, min(31, max_up))
        sync_only = cmd in ("sync", "refreshseo")
        skip_seo = cmd == "sync"
        res = trigger_cycle(max_uploads=max_up, sync_only=sync_only, skip_seo=skip_seo, reply_chat_id=chat_id)
        if res.get("started"):
            _dispatch_message(chat_id, f"🚀 <b>Started</b> cloud <code>/{cmd}</code> job on Render — completion update will post here.", reply_to=msg_id)
        else:
            _dispatch_message(chat_id, "⏳ A cloud cycle is already running; check /status shortly.", reply_to=msg_id)
    elif cmd in ("pause", "resume"):
        actor = from_u.get("username") or str(from_u.get("id"))
        paused = cmd == "pause"
        set_bot_paused(paused, actor=f"@{actor}")
        threading.Thread(
            target=sync_github_fn,
            args=(f"chore(bot): {'pause' if paused else 'resume'} auto uploads [skip render] [skip ci]",),
            daemon=True,
        ).start()
        text, kb = build_dashboard_view(get_state())
        _dispatch_message(chat_id, f"{'⏸ Auto-uploads PAUSED' if paused else '▶ Auto-uploads RESUMED'}.\n\n" + text, kb, reply_to=msg_id)
    elif cmd == "links":
        text, kb = build_links_view()
        _dispatch_message(chat_id, text, kb, reply_to=msg_id)

    return {"handled": f"cmd:{cmd}"}
