"""
Group Chat Archiver & Periodic GitHub Synchronizer for @MessageXTRobot.
Logs incoming group chat messages per-group into distinct JSON files and master chatdata.json,
and syncs changed chat data to GitHub at user-configured intervals 't' on /boostcommit commands.
"""
import json
import os
import re
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from repo_paths import AUTO_DIR, ROOT_DIR

IST = timezone(timedelta(hours=5, minutes=30))
OWNER_ID = int(os.environ.get("TELEGRAM_OWNER_ID", 8017642813))

DATA_DIR = AUTO_DIR / "data"
CHAT_LOGS_DIR = DATA_DIR / "chat_logs"
CHATDATA_PATH = DATA_DIR / "chatdata.json"
SETTINGS_PATH = DATA_DIR / "chat_sync_settings.json"

_LOCK = threading.Lock()
_WORKER_THREAD: threading.Thread | None = None
_WORKER_STOP_EVENT = threading.Event()
_HAS_NEW_DATA = False


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[\\/*?:"<>|]+', "_", name.strip())
    clean = re.sub(r"\s+", "_", clean).strip("_")
    return clean[:60] or "unnamed_group"


def get_sync_settings() -> dict:
    with _LOCK:
        return _read_json(SETTINGS_PATH, {
            "enabled": False,
            "interval_minutes": 5,
            "last_sync_ist": None,
            "total_messages_recorded": 0,
            "groups_tracked": {}
        })


def save_sync_settings(settings: dict) -> None:
    with _LOCK:
        _write_json(SETTINGS_PATH, settings)


def record_group_message(msg: dict) -> None:
    """Record an incoming group chat message into its group-specific file and chatdata.json."""
    global _HAS_NEW_DATA
    if not msg:
        return
    chat = msg.get("chat") or {}
    chat_type = str(chat.get("type", ""))
    if chat_type not in ("group", "supergroup"):
        return

    chat_id = chat.get("id")
    chat_title = chat.get("title") or f"Group_{chat_id}"
    sender = msg.get("from") or {}
    msg_id = msg.get("message_id")
    text = msg.get("text") or msg.get("caption") or ""
    if not text and msg.get("new_chat_members"):
        text = f"[New Member Added: {[u.get('first_name') for u in msg.get('new_chat_members', [])]}]"
    elif not text and msg.get("left_chat_member"):
        text = f"[Member Left: {msg.get('left_chat_member', {}).get('first_name')}]"
    elif not text:
        text = "[Non-text media / event]"

    entry = {
        "msg_id": msg_id,
        "chat_id": chat_id,
        "chat_title": chat_title,
        "sender_id": sender.get("id"),
        "sender_username": sender.get("username"),
        "sender_name": sender.get("first_name", "User"),
        "text": text,
        "date_ist": _now_ist(),
    }

    group_file_name = f"{sanitize_filename(chat_title)}_{abs(chat_id)}.json"
    group_file_path = CHAT_LOGS_DIR / group_file_name

    with _LOCK:
        # 1. Update group-specific file
        g_data = _read_json(group_file_path, {
            "chat_id": chat_id,
            "chat_title": chat_title,
            "created_at_ist": _now_ist(),
            "updated_at_ist": _now_ist(),
            "messages": []
        })
        g_data["updated_at_ist"] = _now_ist()
        g_data["chat_title"] = chat_title
        msgs = g_data.setdefault("messages", [])
        msgs.append(entry)
        if len(msgs) > 2000:
            msgs = msgs[-2000:]
            g_data["messages"] = msgs
        _write_json(group_file_path, g_data)

        # 2. Update master chatdata.json
        master = _read_json(CHATDATA_PATH, {
            "title": "Master Chat Data Logs",
            "updated_at_ist": _now_ist(),
            "total_messages": 0,
            "recent_messages": []
        })
        master["updated_at_ist"] = _now_ist()
        master["total_messages"] = int(master.get("total_messages", 0)) + 1
        recents = master.setdefault("recent_messages", [])
        recents.append(entry)
        if len(recents) > 1000:
            recents = recents[-1000:]
            master["recent_messages"] = recents
        _write_json(CHATDATA_PATH, master)

        # 3. Update settings tracker
        cfg = _read_json(SETTINGS_PATH, {
            "enabled": False,
            "interval_minutes": 5,
            "last_sync_ist": None,
            "total_messages_recorded": 0,
            "groups_tracked": {}
        })
        cfg["total_messages_recorded"] = int(cfg.get("total_messages_recorded", 0)) + 1
        groups = cfg.setdefault("groups_tracked", {})
        groups[str(chat_id)] = {
            "id": chat_id,
            "title": chat_title,
            "file": group_file_name,
            "last_message_at": _now_ist(),
            "message_count": len(msgs)
        }
        _write_json(SETTINGS_PATH, cfg)

        _HAS_NEW_DATA = True


def sync_chat_data_to_github() -> dict:
    """Commit any updated chat logs to GitHub repository via github_sync."""
    global _HAS_NEW_DATA
    from github_sync import push_changed_files
    from repo_paths import AUTO_DIR
    commit_msg = f"chore(chat-backup): sync group chat data ({_now_ist()}) [skip render] [skip ci]"
    chat_paths = [
        AUTO_DIR / "data" / "chatdata.json",
        AUTO_DIR / "data" / "chat_sync_settings.json",
    ]
    chat_logs_dir = AUTO_DIR / "data" / "chat_logs"
    if chat_logs_dir.exists():
        chat_paths.extend(sorted(chat_logs_dir.glob("*.json")))
    res = push_changed_files(commit_message=commit_msg, candidate_paths=chat_paths)
    if res.get("committed"):
        _HAS_NEW_DATA = False
        with _LOCK:
            cfg = _read_json(SETTINGS_PATH, {})
            cfg["last_sync_ist"] = _now_ist()
            _write_json(SETTINGS_PATH, cfg)
        print(f"CHAT_SYNC_GITHUB_OK: {res.get('sha')} (files: {res.get('files')})", flush=True)
    return res


def _background_sync_loop(interval_sec: float) -> None:
    print(f"CHAT_ARCHIVER_WORKER started: interval={interval_sec}s", flush=True)
    while not _WORKER_STOP_EVENT.is_set():
        _WORKER_STOP_EVENT.wait(interval_sec)
        if _WORKER_STOP_EVENT.is_set():
            break
        cfg = get_sync_settings()
        if not cfg.get("enabled"):
            break
        if _HAS_NEW_DATA:
            try:
                sync_chat_data_to_github()
            except Exception as exc:
                print(f"CHAT_SYNC_WORKER_ERR: {exc}", flush=True)


def ensure_worker_running() -> None:
    global _WORKER_THREAD
    cfg = get_sync_settings()
    if cfg.get("enabled"):
        if _WORKER_THREAD is None or not _WORKER_THREAD.is_alive():
            _WORKER_STOP_EVENT.clear()
            interval = max(60.0, float(cfg.get("interval_minutes", 5)) * 60.0)
            _WORKER_THREAD = threading.Thread(target=_background_sync_loop, args=(interval,), daemon=True)
            _WORKER_THREAD.start()


def stop_worker() -> None:
    global _WORKER_THREAD
    _WORKER_STOP_EVENT.set()
    _WORKER_THREAD = None


def handle_boostcommit_command(actor: dict, arg: str) -> str:
    """Handle /boostcommit [-on [t] | -off] command."""
    u_id = actor.get("id")
    if u_id != OWNER_ID:
        return "Baap Ko Bhej Tere Bs Ki Baat Ni Meethe"

    raw = (arg or "").strip().lower()
    tokens = raw.split()

    cfg = get_sync_settings()

    if "-on" in tokens or "on" in tokens:
        # Parse time interval 't' if provided
        interval = 5
        for tok in tokens:
            m = re.match(r"^(\d+)([mhd]?)$", tok)
            if m:
                val = int(m.group(1))
                unit = m.group(2)
                if unit == "h":
                    interval = val * 60
                elif unit == "d":
                    interval = val * 1440
                else:
                    interval = val
                break
        interval = max(5, min(1440, interval))  # Safe bound: min 5 min, max 24 hours

        cfg["enabled"] = True
        cfg["interval_minutes"] = interval
        save_sync_settings(cfg)
        stop_worker()
        ensure_worker_running()

        return (
            f"✅ <b>Group Chat Archiver & Sync Activated:</b>\n\n"
            f"• <b>Status:</b> <code>ON</code>\n"
            f"• <b>Sync Interval:</b> <code>{interval} minutes</code>\n"
            f"• <b>Master File:</b> <code>automation/data/chatdata.json</code>\n"
            f"• <b>Group Files Directory:</b> <code>automation/data/chat_logs/</code>\n"
            f"• <b>Auto Group File Creation:</b> Whenever bot is added to a new group, a separate <code>&lt;group_name&gt;.json</code> file is created automatically.\n"
            f"• <b>GitHub Sync:</b> Changed chat logs will be committed to GitHub every {interval} mins when active."
        )

    if "-off" in tokens or "off" in tokens:
        cfg["enabled"] = False
        save_sync_settings(cfg)
        stop_worker()
        return (
            "🛑 <b>Group Chat Archiver & Sync Deactivated:</b>\n\n"
            "• <b>Status:</b> <code>OFF</code>\n"
            "• Periodic GitHub commits for chat data have been stopped."
        )

    # Status summary
    is_on = cfg.get("enabled", False)
    interval = cfg.get("interval_minutes", 5)
    last_sync = cfg.get("last_sync_ist") or "Never"
    total_msgs = cfg.get("total_messages_recorded", 0)
    groups = cfg.get("groups_tracked", {})

    status_tag = "🟢 ACTIVE" if is_on else "🔴 INACTIVE"
    lines = [
        f"📊 <b>Chat Archiver & Commit Status:</b> {status_tag}\n",
        f"• <b>Sync Interval:</b> <code>{interval} minutes</code>",
        f"• <b>Total Messages Recorded:</b> <code>{total_msgs}</code>",
        f"• <b>Last GitHub Commit:</b> <code>{last_sync}</code>",
        f"• <b>Monitored Groups:</b> <code>{len(groups)}</code>\n",
    ]
    if groups:
        lines.append("<b>Tracked Group Files:</b>")
        for gid, info in list(groups.items())[:5]:
            lines.append(f"  📁 <code>{info.get('file')}</code> ({info.get('message_count', 0)} msgs)")
        if len(groups) > 5:
            lines.append(f"  <i>...and {len(groups) - 5} more groups</i>")
        lines.append("")

    lines.append("<i>Usage:</i>\n<code>/boostcommit -on 5</code> — Turn ON with 5 min interval\n<code>/boostcommit -off</code> — Turn OFF")
    return "\n".join(lines)
