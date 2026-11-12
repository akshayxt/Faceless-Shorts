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
import random
import re
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
AGENT_INBOX_PATH = AUTO_DIR / "data" / "agent_inbox.json"

DEFAULT_PUBLIC_URL = "https://babybeats-cloud-autopilot.onrender.com"
OWNER_ID = 7118065044
UNAUTHORIZED_REPLY = "Baap Ko Bhej Tere Bs Ki Baat Ni Meethe"
SUPPORT_CHAT = "TeamXT_Support"
UPDATES_CHAT = "TeamX_TSupport"
PAGE_SIZE = 8
_BOT_USERNAME: str = ""

START_IMG = [
    "https://telegra.ph/file/f3b2776b2766e911383f0.jpg",
    "https://graph.org/file/08db66a4374af926c9bd3.jpg",
    "https://graph.org/file/7d9eaee9efe95444fb5e3.jpg",
    "https://telegra.ph/file/f71f13dc4755349c13a70.jpg",
    "https://telegra.ph/file/0b99d9768000b9fbc7a28.jpg",
    "https://telegra.ph/file/6af06601caadb0e88e8fe.jpg",
    "https://telegra.ph/file/0cd3fdfb1c37e35860167.jpg",
    "https://graph.org/file/a45b214adabcd86401152.jpg",
]

START_VID = PING_MP4 = ALIVE_ANIMATION = [
    "https://telegra.ph/file/5ce0259747cdd75db040f.mp4",
    "https://telegra.ph/file/925d833773c3f75500255.mp4",
    "https://telegra.ph/file/3c1ca2ea64323e00426c2.mp4",
    "https://telegra.ph/file/436f9cacca9b37538dda3.mp4",
]

HEY_IMG = "https://graph.org/file/3740819ccb58317741e8e.jpg"

FIRST_PART_TEXT = "✨ <b>ʜᴇʟʟᴏ</b> <code>{}</code> . . ."

PM_START_TEXT = (
    "<b>Hᴇʏ ɢᴜʏs, I ᴀᴍ BᴀʙʏBᴇᴀᴛs XT</b>, ᴀ ʜᴀᴄᴋɪɴɢ ᴛʜᴇᴍᴇ ʙᴀsᴇᴅ "
    "<b>24/7 YᴏᴜTᴜʙᴇ Cʟᴏᴜᴅ Aᴜᴛᴏᴘɪʟᴏᴛ &amp; AI Cᴏɴᴛʀᴏʟ Bᴏᴛ</b> "
    "ᴘᴏᴡᴇʀᴇᴅ ʙʏ <b>Rᴇɴᴅᴇʀ + GɪᴛHᴜʙ + Aɴᴛɪɢʀᴀᴠɪᴛʏ</b> ⚡"
)

HELP_STRINGS = (
    "☉ <b>Here, you will find a list of all the available commands.</b>\n"
    "ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ : <code>/</code>"
)

BOT_COMMANDS: list[dict[str, str]] = [
    {"command": "start", "description": "Stylish BabyBeats XT control center intro"},
    {"command": "alive", "description": "Check live bot animation, cloud & queue ping"},
    {"command": "dashboard", "description": "Interactive growth, upload & server cockpit"},
    {"command": "ask", "description": "Give natural-language command (/ask upload 2 videos)"},
    {"command": "cmd", "description": "Execute cloud/AI instruction (/cmd sync youtube)"},
    {"command": "agent", "description": "Queue coding/browser task for Antigravity bridge"},
    {"command": "tasks", "description": "View queued & completed Antigravity agent tasks"},
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
_KNOWN_CMD_SET = {c["command"] for c in BOT_COMMANDS} | {"dash", "panel", "do", "ai", "inbox"}


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
    """Allow strictly OWNER_ID (7118065044) in the primary group or private DM."""
    try:
        uid = int(user_id) if user_id is not None else 0
    except (TypeError, ValueError):
        return False
    if uid != OWNER_ID:
        return False
    cfg = load_tg_config()
    primary_chat = str(cfg.get("chat_id", "")).strip()
    if chat_type != "private" and primary_chat and str(chat_id) != primary_chat:
        return False
    return True


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


_INBOX_LOCK = threading.Lock()


def _bot_username() -> str:
    global _BOT_USERNAME
    if not _BOT_USERNAME:
        me = tg_api("getMe")
        if me.get("ok"):
            _BOT_USERNAME = str((me.get("result") or {}).get("username") or "").lower()
    return _BOT_USERNAME or "MessageXTRobot"


def _start_buttons(chat_type: str) -> dict:
    uname = _bot_username()
    if chat_type == "private":
        return {
            "inline_keyboard": [
                [{"text": "⛩ 𝘼𝘿𝘿 𝙈𝙀 𝙏𝙊 𝙔𝙊𝙐𝙍 𝙂𝘾 ⛩", "url": f"https://t.me/{uname}?startgroup=true"}],
                [
                    {"text": "📊 𝘿𝘼𝙎𝙃𝘽𝙊𝘼𝙍𝘿", "callback_data": "cb:dash"},
                    {"text": "📖 𝙃𝙀𝙇𝙋", "callback_data": "help_back"},
                ],
                [
                    {"text": "ℹ️ DETAILS", "callback_data": "bb_details"},
                    {"text": "🤖 AI", "callback_data": "ai_handler"},
                    {"text": "📦 SOURCE", "callback_data": "git_source"},
                ],
                [{"text": "👑 CREATOR", "url": f"tg://user?id={OWNER_ID}"}],
                [
                    {"text": "💬 𝘾𝙃𝘼𝙏 𝙂𝙍𝙊𝙐𝙋", "url": f"https://t.me/{SUPPORT_CHAT}"},
                    {"text": "⚡ 𝐓𝐄𝐀𝐌冬𝗫𝗧", "url": f"https://t.me/{UPDATES_CHAT}"},
                ],
            ]
        }
    return {
        "inline_keyboard": [
            [{"text": "⇦ 𝘼𝘿𝘿 𝙈𝙀 𝙏𝙊 𝙔𝙊𝙐𝙍 𝙂𝘾 ⇨", "url": f"https://t.me/{uname}?startgroup=true"}],
            [
                {"text": "📊 DASHBOARD", "callback_data": "cb:dash"},
                {"text": "🤖 AI CMD", "callback_data": "ai_handler"},
            ],
            [
                {"text": "💬 SUPPORT", "url": f"https://t.me/{SUPPORT_CHAT}"},
                {"text": "👑 CREATOR", "url": f"tg://user?id={OWNER_ID}"},
            ],
        ]
    }


def _alive_buttons() -> dict:
    uname = _bot_username()
    return {
        "inline_keyboard": [
            [
                {"text": "⚡ UPDATES", "url": f"https://t.me/{UPDATES_CHAT}"},
                {"text": "💬 SUPPORT", "url": f"https://t.me/{SUPPORT_CHAT}"},
            ],
            [{"text": "📊 DASHBOARD", "callback_data": "cb:dash"}, {"text": "🤖 AI CMD", "callback_data": "ai_handler"}],
            [{"text": "⇦ 𝘼𝘿𝘿 𝙈𝙀 𝙏𝙊 𝙔𝙊𝙐𝙍 𝙂𝘾 ⇨", "url": f"https://t.me/{uname}?startgroup=true"}],
        ]
    }


def build_start_view(user_name: str, chat_type: str, server_state: dict) -> tuple[str, dict]:
    snap = _load_queue_snapshot()
    nxt = snap["next_item"]
    nxt_id = html.escape(nxt["id"]) if nxt else "ALL DONE"
    mode = "⏸ PAUSED" if get_bot_settings()["paused"] else ("🔄 RUNNING" if server_state.get("running") else "🟢 ONLINE 24/7")
    text = (
        f"{FIRST_PART_TEXT.format(html.escape(user_name or 'Owner'))}\n\n"
        f"{PM_START_TEXT}\n\n"
        f"• <b>Sᴛᴀᴛᴇ:</b> {mode}\n"
        f"• <b>Pʀᴏɢʀᴇss:</b> <code>{snap['done_cnt']}/{snap['total_cnt']}</code> (Next: <code>{nxt_id}</code>)\n"
        f"• <b>Oᴡɴᴇʀ Lᴏᴄᴋ:</b> <code>{OWNER_ID}</code>"
    )
    return text, _start_buttons(chat_type)


def build_details_view(server_state: dict) -> tuple[str, dict]:
    snap = _load_queue_snapshot()
    cfg = _read_json(CHANNEL_CFG, {})
    gh_repo = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO)
    text = (
        f"ℹ️ <b>BabyBeats XT — System Details</b>\n\n"
        f"• <b>YouTube Channel:</b> <code>{html.escape(str(cfg.get('channel_id', 'UCR-Di4-tEAdUM7oPzlGn-vg')))}</code>\n"
        f"• <b>Cloud Host:</b> Render Free Web Service (24/7 PC-Offline)\n"
        f"• <b>Storage &amp; CDN:</b> <code>{html.escape(gh_repo)}</code>\n"
        f"• <b>Queue:</b> {snap['done_cnt']}/{snap['total_cnt']} uploaded/scheduled\n"
        f"• <b>Completed Runs:</b> {server_state.get('runs_completed', 0)}\n"
        f"• <b>Access Lock:</b> Strictly <code>OWNER_ID = {OWNER_ID}</code>"
    )
    kb = {
        "inline_keyboard": [
            [{"text": "📊 Open Dashboard", "callback_data": "cb:dash"}, {"text": "🔙 Back", "callback_data": "start_home"}]
        ]
    }
    return text, kb


def build_ai_guide_view() -> tuple[str, dict]:
    text = (
        f"🤖 <b>Antigravity Telegram AI Command Mode</b>\n\n"
        f"Send commands to me here just like Antigravity chat:\n\n"
        f"• <b>In DM:</b> Simply type any instruction normally (no <code>/</code> needed!)\n"
        f"  <i>e.g.</i> <code>upload 2 videos now</code>, <code>kitne pending hain?</code>, <code>refresh seo</code>, <code>pause uploads</code>\n"
        f"• <b>In Group:</b> Prefix with <code>/ask</code>, <code>/cmd</code>, or <code>/agent</code>:\n"
        f"  <code>/ask show next video seo file</code>\n"
        f"  <code>/cmd upload 1 video</code>\n"
        f"  <code>/agent update day10 thumbnail headline</code>\n\n"
        f"• Use <code>/tasks</code> to track queued Antigravity bridge jobs."
    )
    kb = {
        "inline_keyboard": [
            [{"text": "📋 Agent Tasks", "callback_data": "cb:tasks"}, {"text": "📊 Dashboard", "callback_data": "cb:dash"}],
            [{"text": "🔙 Back", "callback_data": "start_home"}],
        ]
    }
    return text, kb


def build_help_view() -> tuple[str, dict]:
    lines = [HELP_STRINGS, ""]
    for entry in BOT_COMMANDS:
        lines.append(f"/{entry['command']} — {html.escape(entry['description'])}")
    kb = {
        "inline_keyboard": [
            [{"text": "🚀 Dashboard", "callback_data": "cb:dash"}, {"text": "📋 Queue", "callback_data": "cb:queue:all:0"}],
            [{"text": "🤖 AI Mode", "callback_data": "ai_handler"}, {"text": "🔙 Start", "callback_data": "start_home"}],
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
            [{"text": "🌐 Web Dashboard", "url": f"{base}/dashboard"}, {"text": "📁 GitHub Repo", "url": f"https://github.com/{gh_repo}"}],
            [{"text": "🔙 Back", "callback_data": "start_home"}],
        ]
    }
    return text, kb


def list_agent_tasks(status_filter: str | None = None) -> list[dict]:
    with _INBOX_LOCK:
        data = _read_json(AGENT_INBOX_PATH, {"tasks": []})
        tasks = list(data.get("tasks") or [])
    if status_filter:
        return [t for t in tasks if t.get("status") == status_filter]
    return tasks


def queue_agent_task(prompt: str, chat_id: int | str, msg_id: int | None, actor: str) -> dict:
    task = {
        "task_id": f"T-{datetime.now(IST).strftime('%H%M%S')}-{uuid.uuid4().hex[:4]}",
        "prompt": prompt.strip(),
        "chat_id": str(chat_id),
        "reply_to_message_id": msg_id,
        "requested_by": actor,
        "status": "PENDING",
        "created_at_ist": _now_ist(),
        "completed_at_ist": None,
        "reply": None,
    }
    with _INBOX_LOCK:
        data = _read_json(AGENT_INBOX_PATH, {"tasks": []})
        tasks = list(data.get("tasks") or [])
        tasks.append(task)
        data["tasks"] = tasks[-100:]
        AGENT_INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
        AGENT_INBOX_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return task


def complete_agent_task(task_id: str, reply_text: str, status: str = "DONE") -> dict | None:
    updated = None
    with _INBOX_LOCK:
        data = _read_json(AGENT_INBOX_PATH, {"tasks": []})
        tasks = list(data.get("tasks") or [])
        for t in tasks:
            if t.get("task_id") == task_id:
                t["status"] = status
                t["reply"] = reply_text
                t["completed_at_ist"] = _now_ist()
                updated = dict(t)
                break
        if updated:
            AGENT_INBOX_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return updated


def build_tasks_view() -> tuple[str, dict]:
    tasks = list_agent_tasks()
    recent = list(reversed(tasks[-8:]))
    lines = [f"🤖 <b>Antigravity Command Inbox</b> ({len(tasks)} total)\n"]
    icon = {"PENDING": "🟡", "DONE": "🟢", "FAILED": "🔴"}
    for t in recent:
        ico = icon.get(t.get("status", ""), "❔")
        snippet = html.escape(str(t.get("prompt", ""))[:55])
        lines.append(f"{ico} <code>{html.escape(str(t.get('task_id')))}</code> [{t.get('status')}] · {snippet}")
    if not recent:
        lines.append("<i>No Antigravity tasks queued yet. Use /agent &lt;task&gt; or chat in DM.</i>")
    kb = {
        "inline_keyboard": [
            [{"text": "🔄 Refresh Tasks", "callback_data": "cb:tasks"}, {"text": "📊 Dashboard", "callback_data": "cb:dash"}]
        ]
    }
    return "\n".join(lines), kb


def _ask_gemini_cloud(prompt: str, server_state: dict) -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    snap = _load_queue_snapshot()
    nxt = snap["next_item"] or {}
    context = (
        f"Project: BabyBeats Rhymo YouTube Automation (31 videos). "
        f"Progress: {snap['done_cnt']}/{snap['total_cnt']} done, {len(snap['pending'])} remaining. "
        f"Next video: {nxt.get('id', 'none')} - {nxt.get('title', '')}. "
        f"Paused: {get_bot_settings()['paused']}. Server runs: {server_state.get('runs_completed', 0)}."
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": f"System context: {context}\nReply concisely in Hinglish/English for the repo owner:\n\n{prompt}"}]}]
    }).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        cands = data.get("candidates") or []
        parts = ((cands[0].get("content") or {}).get("parts") or []) if cands else []
        return str(parts[0].get("text") or "").strip() if parts else None
    except Exception:
        return None


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


def _dispatch_start_media(chat_id: int | str, caption: str, reply_markup: dict, reply_to: int | None = None) -> dict:
    for url in random.sample(START_IMG, min(2, len(START_IMG))):
        payload: dict[str, Any] = {
            "chat_id": str(chat_id),
            "photo": url,
            "caption": caption[:1024],
            "parse_mode": "HTML",
            "reply_markup": reply_markup,
        }
        if reply_to:
            payload["reply_to_message_id"] = reply_to
        res = tg_api("sendPhoto", payload, timeout=20)
        if res.get("ok"):
            return res
    return _dispatch_message(chat_id, caption, reply_markup, reply_to=reply_to)


def _dispatch_alive_media(chat_id: int | str, server_state: dict, reply_to: int | None = None) -> dict:
    snap = _load_queue_snapshot()
    caption = (
        f"⚡ <b>BᴀʙʏBᴇᴀᴛs XT — ALIVE &amp; RUNNING</b>\n\n"
        f"• <b>Host:</b> Render Cloud + GitHub CDN\n"
        f"• <b>Progress:</b> <code>{snap['done_cnt']}/{snap['total_cnt']}</code> done\n"
        f"• <b>Completed Runs:</b> <code>{server_state.get('runs_completed', 0)}</code>\n"
        f"• <b>Time:</b> <code>{_now_ist()}</code>"
    )
    kb = _alive_buttons()
    vid = random.choice(ALIVE_ANIMATION)
    payload: dict[str, Any] = {
        "chat_id": str(chat_id),
        "video": vid,
        "caption": caption[:1024],
        "parse_mode": "HTML",
        "reply_markup": kb,
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    res = tg_api("sendVideo", payload, timeout=20)
    if res.get("ok"):
        return res
    if HEY_IMG:
        p2 = dict(payload)
        p2.pop("video", None)
        p2["photo"] = HEY_IMG
        res2 = tg_api("sendPhoto", p2, timeout=20)
        if res2.get("ok"):
            return res2
    return _dispatch_message(chat_id, caption, kb, reply_to=reply_to)


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


def _edit_message_smart(msg: dict, chat_id: int | str, message_id: int, text: str, reply_markup: dict | None = None) -> dict:
    is_media = any(k in msg for k in ("photo", "video", "animation", "document"))
    if is_media:
        if len(text) <= 1024:
            payload: dict[str, Any] = {
                "chat_id": str(chat_id),
                "message_id": message_id,
                "caption": text,
                "parse_mode": "HTML",
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            res = tg_api("editMessageCaption", payload)
            if res.get("ok"):
                return res
        return _dispatch_message(chat_id, text, reply_markup)
    res = _edit_message(chat_id, message_id, text, reply_markup)
    if not res.get("ok") and "message to edit not found" not in str(res).lower():
        return _dispatch_message(chat_id, text, reply_markup)
    return res


def _execute_nl_command(
    prompt: str,
    chat_id: int | str,
    msg_id: int | None,
    from_u: dict,
    get_state: Callable[[], dict],
    trigger_cycle: Callable[..., dict],
    sync_github_fn: Callable[[str], dict],
    force_agent: bool = False,
) -> dict:
    raw = (prompt or "").strip()
    if not raw:
        t, kb = build_ai_guide_view()
        _dispatch_message(chat_id, t, kb, reply_to=msg_id)
        return {"handled": "nl_empty"}

    low = raw.lower()
    actor = from_u.get("username") or str(from_u.get("id") or OWNER_ID)
    vid_match = re.search(r"\b(day\d{2}_(?:short|long))\b", low)
    vid_id = vid_match.group(1) if vid_match else ""

    if not force_agent:
        if any(k in low for k in ("pause upload", "pause auto", "stop upload", "uploads band", "pause kr")):
            set_bot_paused(True, actor=f"@{actor}")
            threading.Thread(target=sync_github_fn, args=("chore(bot): pause auto uploads via AI cmd [skip render] [skip ci]",), daemon=True).start()
            t, kb = build_dashboard_view(get_state())
            _dispatch_message(chat_id, "⏸ <b>Auto-uploads PAUSED via AI command.</b>\n\n" + t, kb, reply_to=msg_id)
            return {"handled": "nl:pause"}

        if any(k in low for k in ("resume upload", "unpause", "start auto", "resume kr", "chalu kr")):
            set_bot_paused(False, actor=f"@{actor}")
            threading.Thread(target=sync_github_fn, args=("chore(bot): resume auto uploads via AI cmd [skip render] [skip ci]",), daemon=True).start()
            t, kb = build_dashboard_view(get_state())
            _dispatch_message(chat_id, "▶ <b>Auto-uploads RESUMED via AI command.</b>\n\n" + t, kb, reply_to=msg_id)
            return {"handled": "nl:resume"}

        if any(k in low for k in ("upload", "run cycle", "run now", "upload kro", "start upload")) and "queue" not in low and "status" not in low:
            m_num = re.search(r"\b(\d{1,2})\b", low)
            max_up = max(1, min(31, int(m_num.group(1)))) if m_num else 10
            res = trigger_cycle(max_uploads=max_up, sync_only=False, skip_seo=False, reply_chat_id=chat_id)
            reply = f"🚀 <b>Started</b> cloud upload cycle (max <code>{max_up}</code>) on Render — completion update will arrive here." if res.get("started") else "⏳ A cloud cycle is already running; check /status shortly."
            _dispatch_message(chat_id, reply, reply_to=msg_id)
            return {"handled": f"nl:upload:{max_up}"}

        if "refresh seo" in low or "update seo" in low:
            res = trigger_cycle(max_uploads=10, sync_only=True, skip_seo=False, reply_chat_id=chat_id)
            _dispatch_message(chat_id, "🔍 <b>Started</b> Real-Time US SEO refresh on Render." if res.get("started") else "⏳ A cloud cycle is already running.", reply_to=msg_id)
            return {"handled": "nl:refreshseo"}

        if any(k in low for k in ("sync youtube", "reconcile", "yt sync", "sync kr", "sync channel")):
            res = trigger_cycle(max_uploads=10, sync_only=True, skip_seo=True, reply_chat_id=chat_id)
            _dispatch_message(chat_id, "🔎 <b>Started</b> YouTube channel sync + dashboard refresh on Render." if res.get("started") else "⏳ A cloud cycle is already running.", reply_to=msg_id)
            return {"handled": "nl:sync"}

        if any(k in low for k in ("seotxt", "seo.txt", "seo file")) or ("file" in low and ("seo" in low or vid_id)):
            ok, info = _send_seo_document(chat_id, vid_id, reply_to=msg_id)
            if not ok:
                _dispatch_message(chat_id, f"⚠️ {html.escape(info)}", reply_to=msg_id)
            return {"handled": "nl:seotxt"}

        if "seo" in low or "next video" in low or vid_id:
            t, kb, _ = build_next_or_seo_view(vid_id, include_desc=("seo" in low or bool(vid_id)))
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:seo"}

        if any(k in low for k in ("dashboard", "dash", "progress", "kitne", "kya haal", "report", "summary")):
            t, kb = build_dashboard_view(get_state())
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:dashboard"}

        if any(k in low for k in ("status", "health", "logs", "server", "telemetry")):
            t, kb = build_status_view(get_state())
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:status"}

        if any(k in low for k in ("pending", "remaining", "bache")):
            t, kb = build_queue_view("pending", 0)
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:pending"}

        if "scheduled" in low:
            t, kb = build_queue_view("scheduled", 0)
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:scheduled"}

        if "uploaded" in low or "live video" in low:
            t, kb = build_queue_view("uploaded", 0)
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:uploaded"}

        if "queue" in low or "videos list" in low:
            t, kb = build_queue_view("all", 0)
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:queue"}

        if "tasks" in low or "inbox" in low:
            t, kb = build_tasks_view()
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:tasks"}

        if "links" in low or "url" in low:
            t, kb = build_links_view()
            _dispatch_message(chat_id, t, kb, reply_to=msg_id)
            return {"handled": "nl:links"}

        gem_ans = _ask_gemini_cloud(raw, get_state())
        if gem_ans:
            _dispatch_message(chat_id, f"🤖 <b>Cloud AI Reply:</b>\n\n{html.escape(gem_ans)}", reply_to=msg_id)
            return {"handled": "nl:gemini"}

    task = queue_agent_task(raw, chat_id, msg_id, actor=f"@{actor}")
    threading.Thread(
        target=sync_github_fn,
        args=(f"chore(agent-inbox): queue {task['task_id']} [skip render] [skip ci]",),
        daemon=True,
    ).start()
    _dispatch_message(
        chat_id,
        f"🧠 <b>Antigravity Command Queued:</b> <code>{html.escape(task['task_id'])}</code>\n\n"
        f"• <b>Command:</b> <code>{html.escape(raw[:300])}</code>\n"
        f"• <b>Status:</b> 🟡 <code>PENDING</code> (synced to GitHub + <code>/agent/inbox</code>)\n\n"
        f"<i>Custom code/browser tasks run automatically whenever your Antigravity bridge is online; instant upload/SEO/queue commands execute 24/7 directly via /ask or /cmd even when PC is off.</i>",
        reply_to=msg_id,
    )
    return {"handled": f"nl:queued:{task['task_id']}"}


def handle_webhook_update(
    update: dict,
    get_state: Callable[[], dict],
    trigger_cycle: Callable[..., dict],
    sync_github_fn: Callable[[str], dict],
) -> dict:
    """Process one Telegram Message or CallbackQuery update cleanly without blocking HTTP response."""
    _bot_username()

    if "callback_query" in update:
        cq = update["callback_query"]
        cq_id = cq.get("id")
        from_u = cq.get("from") or {}
        msg = cq.get("message") or {}
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        chat_type = str(chat.get("type") or "")
        msg_id = msg.get("message_id")
        data = str(cq.get("data") or "")

        if not is_authorized_actor(from_u.get("id"), chat_id, chat_type):
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": UNAUTHORIZED_REPLY, "show_alert": True})
            return {"handled": "unauthorized_callback"}

        if data == "start_home":
            uname = str(from_u.get("first_name") or from_u.get("username") or "Owner")
            text, kb = build_start_view(uname, chat_type, get_state())
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data == "help_back":
            text, kb = build_help_view()
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data == "bb_details":
            text, kb = build_details_view(get_state())
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data == "ai_handler":
            text, kb = build_ai_guide_view()
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data == "git_source":
            text, kb = build_links_view()
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data == "cb:tasks":
            text, kb = build_tasks_view()
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data == "cb:dash":
            text, kb = build_dashboard_view(get_state())
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": "Dashboard refreshed"})
        elif data == "cb:status":
            text, kb = build_status_view(get_state())
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data.startswith("cb:queue:"):
            parts = data.split(":")
            flt = parts[2] if len(parts) > 2 else "all"
            page = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
            text, kb = build_queue_view(flt, page)
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        elif data == "cb:next":
            text, kb, _ = build_next_or_seo_view("", include_desc=False)
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
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
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
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
            _edit_message_smart(msg, chat_id, msg_id, text, kb)
        else:
            tg_api("answerCallbackQuery", {"callback_query_id": cq_id})
        return {"handled": f"callback:{data}"}

    msg = update.get("message")
    if not msg or not msg.get("text"):
        return {"handled": "ignored_non_text"}

    text_in = str(msg["text"]).strip()
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    chat_type = str(chat.get("type") or "")
    msg_id = msg.get("message_id")
    from_u = msg.get("from") or {}

    if not text_in.startswith("/"):
        if chat_type != "private":
            return {"handled": "ignored_group_chatter"}
        if not is_authorized_actor(from_u.get("id"), chat_id, chat_type):
            _dispatch_message(chat_id, UNAUTHORIZED_REPLY, reply_to=msg_id)
            return {"handled": "unauthorized_message"}
        return _execute_nl_command(text_in, chat_id, msg_id, from_u, get_state, trigger_cycle, sync_github_fn, force_agent=False)

    cmd, arg = _parse_command(text_in, _BOT_USERNAME)
    if not cmd:
        return {"handled": "ignored_non_bot_cmd"}

    if not is_authorized_actor(from_u.get("id"), chat_id, chat_type):
        _dispatch_message(chat_id, UNAUTHORIZED_REPLY, reply_to=msg_id)
        return {"handled": "unauthorized_message"}

    if cmd == "start":
        uname = str(from_u.get("first_name") or from_u.get("username") or "Owner")
        text, kb = build_start_view(uname, chat_type, get_state())
        _dispatch_start_media(chat_id, text, kb, reply_to=msg_id)
    elif cmd == "alive":
        _dispatch_alive_media(chat_id, get_state(), reply_to=msg_id)
    elif cmd == "help":
        text, kb = build_help_view()
        _dispatch_message(chat_id, text, kb, reply_to=msg_id)
    elif cmd in ("ask", "cmd", "do", "ai", "agent"):
        return _execute_nl_command(arg, chat_id, msg_id, from_u, get_state, trigger_cycle, sync_github_fn, force_agent=(cmd == "agent"))
    elif cmd in ("tasks", "inbox"):
        text, kb = build_tasks_view()
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
