"""
Comprehensive Telegram Moderation, Administration, Centralized Logging & Bot Management Engine.
Powers @MessageXTRobot for group administration, user moderation, video privacy, and interactive cockpit.
"""
import csv
import io
import json
import os
import re
import threading
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

IST = timezone(timedelta(hours=5, minutes=30))
AUTO_DIR = Path(__file__).resolve().parent
DATA_DIR = AUTO_DIR / "data"
MOD_DATA_PATH = DATA_DIR / "moderation_data.json"
AUDIT_LOG_PATH = DATA_DIR / "bot_audit_logs.json"
UPLOAD_Q_PATH = DATA_DIR / "upload_queue.json"

OWNER_ID = int(os.environ.get("TELEGRAM_OWNER_ID", 8017642813))
_LOCK = threading.Lock()
_FLOOD_TRACKER: dict[str, list[float]] = {}


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_mod_data() -> dict:
    with _LOCK:
        data = _read_json(MOD_DATA_PATH, {})
    defaults = {
        "maintenance": False,
        "banned_bot_users": [],
        "registered_users": {},
        "registered_groups": {},
        "warnings": {},
        "group_settings": {},
        "logging": {"enabled": True, "channel_id": None, "bot_log_message_ids": []},
        "blacklist_keywords": ["t.me/", "discord.gg/", "free crypto", "telegram.me/"],
        "link_filter_enabled": False,
        "flood_threshold": 5,
    }
    for k, v in defaults.items():
        data.setdefault(k, v)
    return data


def save_mod_data(data: dict) -> None:
    with _LOCK:
        _write_json(MOD_DATA_PATH, data)


def register_actor(user: dict | None, chat: dict | None) -> None:
    """Track registered users and connected groups for bot management and broadcasts."""
    if not user and not chat:
        return
    data = get_mod_data()
    changed = False
    if user and user.get("id"):
        uid = str(user["id"])
        u_info = {
            "id": user["id"],
            "username": user.get("username"),
            "first_name": user.get("first_name", ""),
            "last_seen_ist": _now_ist(),
        }
        if data["registered_users"].get(uid) != u_info:
            data["registered_users"][uid] = u_info
            changed = True
    if chat and chat.get("id") and str(chat.get("type")) in ("group", "supergroup"):
        cid = str(chat["id"])
        c_info = {
            "id": chat["id"],
            "title": chat.get("title", ""),
            "type": chat.get("type", ""),
            "last_seen_ist": _now_ist(),
        }
        if data["registered_groups"].get(cid) != c_info:
            data["registered_groups"][cid] = c_info
            changed = True
    if changed:
        save_mod_data(data)


def is_owner(user_id: int | str | None) -> bool:
    try:
        return int(user_id) == OWNER_ID if user_id is not None else False
    except (TypeError, ValueError):
        return False


def is_bot_user_banned(user_id: int | str | None) -> bool:
    if not user_id:
        return False
    data = get_mod_data()
    return int(user_id) in [int(x) for x in data.get("banned_bot_users", []) if str(x).isdigit()]


def is_maintenance_active() -> bool:
    return bool(get_mod_data().get("maintenance", False))


# ---------------------------------------------------------------------------
# Centralized Audit Logging
# ---------------------------------------------------------------------------

def log_audit_event(
    action: str,
    actor: dict | str,
    target: dict | str | None = None,
    details: str = "",
    chat_id: int | str | None = None,
    tg_api_fn: Callable[..., dict] | None = None,
) -> dict:
    actor_str = f"@{actor.get('username')}" if isinstance(actor, dict) and actor.get("username") else (str(actor.get("id")) if isinstance(actor, dict) else str(actor))
    target_str = f"@{target.get('username')}" if isinstance(target, dict) and target.get("username") else (str(target.get("id")) if isinstance(target, dict) else (str(target) if target else "—"))
    entry = {
        "timestamp_ist": _now_ist(),
        "action": action.upper(),
        "actor": actor_str,
        "target": target_str,
        "chat_id": str(chat_id) if chat_id else "—",
        "details": details,
    }
    with _LOCK:
        store = _read_json(AUDIT_LOG_PATH, {"logs": []})
        logs = store.setdefault("logs", [])
        logs.append(entry)
        store["logs"] = logs[-1000:]
        _write_json(AUDIT_LOG_PATH, store)

    data = get_mod_data()
    log_cfg = data.get("logging", {})
    if log_cfg.get("enabled") and log_cfg.get("channel_id") and tg_api_fn:
        dest = log_cfg["channel_id"]
        text = (
            f"📋 <b>Bot Audit Log</b>: <code>{entry['action']}</code>\n\n"
            f"• <b>Actor:</b> <code>{entry['actor']}</code>\n"
            f"• <b>Target:</b> <code>{entry['target']}</code>\n"
            f"• <b>Chat:</b> <code>{entry['chat_id']}</code>\n"
            f"• <b>Details:</b> {entry['details']}\n"
            f"• <b>Time:</b> <code>{entry['timestamp_ist']}</code>"
        )
        res = tg_api_fn("sendMessage", {"chat_id": dest, "text": text, "parse_mode": "HTML"})
        if res.get("ok") and (res.get("result") or {}).get("message_id"):
            mid = res["result"]["message_id"]
            mids = log_cfg.setdefault("bot_log_message_ids", [])
            mids.append({"chat_id": dest, "message_id": mid})
            log_cfg["bot_log_message_ids"] = mids[-200:]
            save_mod_data(data)

    return entry


def get_audit_logs(filter_user: str | None = None, limit: int = 15) -> list[dict]:
    with _LOCK:
        store = _read_json(AUDIT_LOG_PATH, {"logs": []})
    logs = list(store.get("logs", []))
    if filter_user:
        q = filter_user.lower().lstrip("@")
        logs = [e for e in logs if q in str(e.get("actor", "")).lower() or q in str(e.get("target", "")).lower()]
    return list(reversed(logs))[:limit]


def export_audit_logs(fmt: str = "json") -> tuple[bytes, str, str]:
    with _LOCK:
        store = _read_json(AUDIT_LOG_PATH, {"logs": []})
    logs = store.get("logs", [])
    if fmt == "csv":
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=["timestamp_ist", "action", "actor", "target", "chat_id", "details"])
        writer.writeheader()
        for row in logs:
            writer.writerow(row)
        return out.getvalue().encode("utf-8"), "audit_logs.csv", "text/csv"
    data = json.dumps({"exported_at_ist": _now_ist(), "total_logs": len(logs), "logs": logs}, indent=2, ensure_ascii=False)
    return data.encode("utf-8"), "audit_logs.json", "application/json"


def clear_audit_logs() -> int:
    with _LOCK:
        store = _read_json(AUDIT_LOG_PATH, {"logs": []})
        cnt = len(store.get("logs", []))
        _write_json(AUDIT_LOG_PATH, {"logs": []})
    return cnt


# ---------------------------------------------------------------------------
# Target User Resolver & Permissions
# ---------------------------------------------------------------------------

def parse_duration_seconds(raw: str, default_sec: int = 600) -> int:
    if not raw:
        return default_sec
    m = re.match(r"^(\d+)([smhd]?)$", raw.strip().lower())
    if not m:
        return default_sec
    val, unit = int(m.group(1)), m.group(2)
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(unit, 60)
    return max(30, min(86400 * 365, val * mult))


def resolve_target(
    msg: dict,
    arg: str,
    chat_id: int | str,
    tg_api_fn: Callable[..., dict],
) -> tuple[dict | None, str]:
    """Find target user from replied message or argument (@username or numeric user_id)."""
    reply = msg.get("reply_to_message")
    if reply and reply.get("from"):
        u = reply["from"]
        return {"id": u["id"], "username": u.get("username"), "first_name": u.get("first_name", "User")}, ""

    tokens = (arg or "").strip().split()
    if not tokens:
        return None, "Target user not specified (reply to a message or pass @username/ID)."

    target_token = tokens[0]
    rest_arg = " ".join(tokens[1:]).strip()

    if target_token.isdigit() or (target_token.startswith("-") and target_token[1:].isdigit()):
        uid = int(target_token)
        res = tg_api_fn("getChatMember", {"chat_id": chat_id, "user_id": uid})
        if res.get("ok"):
            u = (res.get("result") or {}).get("user", {})
            return {"id": uid, "username": u.get("username"), "first_name": u.get("first_name", f"User {uid}")}, rest_arg
        return {"id": uid, "username": None, "first_name": f"User {uid}"}, rest_arg

    uname = target_token.lstrip("@").lower()
    mod = get_mod_data()
    for uid_str, u_info in mod.get("registered_users", {}).items():
        if (u_info.get("username") or "").lower() == uname:
            return {"id": int(uid_str), "username": u_info.get("username"), "first_name": u_info.get("first_name", "User")}, rest_arg

    admins = tg_api_fn("getChatAdministrators", {"chat_id": chat_id})
    if admins.get("ok"):
        for adm in admins.get("result", []):
            u = adm.get("user", {})
            if (u.get("username") or "").lower() == uname:
                return {"id": u["id"], "username": u.get("username"), "first_name": u.get("first_name", "User")}, rest_arg

    return None, f"Could not resolve user @{uname}. Please reply directly to their message in the group."


def check_actor_admin(
    chat_id: int | str,
    user_id: int | None,
    required_right: str | None,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    if is_owner(user_id):
        return True, "owner"
    if not user_id:
        return False, "Missing user id"

    res = tg_api_fn("getChatMember", {"chat_id": chat_id, "user_id": user_id})
    if not res.get("ok"):
        return False, "Unable to verify member permissions."
    member = res.get("result") or {}
    status = member.get("status")
    if status == "creator":
        return True, "creator"
    if status == "administrator":
        if not required_right:
            return True, "administrator"
        if member.get(required_right) is True:
            return True, "administrator"
        return False, f"Missing permission: <code>{required_right}</code>."
    return False, "This command requires group administrator privileges."


def check_bot_rights(
    chat_id: int | str,
    required_right: str,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    me = tg_api_fn("getMe")
    bot_id = (me.get("result") or {}).get("id")
    if not bot_id:
        return False, "Unable to verify bot account."
    res = tg_api_fn("getChatMember", {"chat_id": chat_id, "user_id": bot_id})
    if not res.get("ok"):
        return False, "Bot is not a member of this chat."
    bot_member = res.get("result") or {}
    if bot_member.get("status") != "administrator":
        return False, "Bot must be promoted to administrator with required permissions."
    if required_right and not bot_member.get(required_right):
        return False, f"Bot is missing required permission: <code>{required_right}</code>."
    return True, "ok"


# ---------------------------------------------------------------------------
# Group Administration: Promote, Demote, Admininfo, Admins, Staff
# ---------------------------------------------------------------------------

DEFAULT_ADMIN_PERMISSIONS = {
    "can_manage_chat": True,
    "can_delete_messages": True,
    "can_restrict_members": True,
    "can_invite_users": True,
    "can_pin_messages": True,
    "can_promote_members": False,
    "can_change_info": False,
    "can_manage_video_chats": True,
}


def cmd_promote(
    chat_id: int | str,
    actor: dict,
    target: dict,
    custom_rights: dict | None,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    if is_owner(target["id"]):
        return False, "Target is the Bot Owner."
    ok_actor, why = check_actor_admin(chat_id, actor.get("id"), "can_promote_members", tg_api_fn)
    if not ok_actor:
        return False, why
    ok_bot, why_b = check_bot_rights(chat_id, "can_promote_members", tg_api_fn)
    if not ok_bot:
        return False, why_b

    rights = dict(DEFAULT_ADMIN_PERMISSIONS)
    if custom_rights:
        rights.update(custom_rights)

    payload = {"chat_id": chat_id, "user_id": target["id"], **rights}
    res = tg_api_fn("promoteChatMember", payload)
    if not res.get("ok"):
        return False, str(res.get("description") or "Telegram API promote failed.")

    log_audit_event("PROMOTE", actor, target, f"Promoted with rights: {list(rights.keys())}", chat_id, tg_api_fn)
    return True, f"✅ Successfully promoted <b>{target.get('first_name')}</b> (@{target.get('username') or target['id']}) to Group Administrator!"


def cmd_demote(
    chat_id: int | str,
    actor: dict,
    target: dict,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    if is_owner(target["id"]):
        return False, "Cannot demote the Bot Owner."
    ok_actor, why = check_actor_admin(chat_id, actor.get("id"), "can_promote_members", tg_api_fn)
    if not ok_actor:
        return False, why
    ok_bot, why_b = check_bot_rights(chat_id, "can_promote_members", tg_api_fn)
    if not ok_bot:
        return False, why_b

    res_target = tg_api_fn("getChatMember", {"chat_id": chat_id, "user_id": target["id"]})
    if (res_target.get("result") or {}).get("status") == "creator":
        return False, "Cannot demote the Group Creator."

    clear_rights = {k: False for k in DEFAULT_ADMIN_PERMISSIONS}
    payload = {"chat_id": chat_id, "user_id": target["id"], **clear_rights}
    res = tg_api_fn("promoteChatMember", payload)
    if not res.get("ok"):
        return False, str(res.get("description") or "Telegram API demote failed.")

    log_audit_event("DEMOTE", actor, target, "Stripped all admin permissions", chat_id, tg_api_fn)
    return True, f"🔻 Successfully demoted <b>{target.get('first_name')}</b> (@{target.get('username') or target['id']}) to normal member."


def cmd_admins(chat_id: int | str, tg_api_fn: Callable[..., dict]) -> str:
    res = tg_api_fn("getChatAdministrators", {"chat_id": chat_id})
    if not res.get("ok"):
        return f"⚠️ Unable to fetch administrators: {res.get('description')}"
    admins = res.get("result") or []
    lines = [f"🛡️ <b>Group Administrators</b> ({len(admins)} total)\n"]
    for a in admins:
        u = a.get("user") or {}
        st = a.get("status", "administrator").upper()
        custom = a.get("custom_title")
        tag = f" <i>[{custom}]</i>" if custom else ""
        uname = f"@{u['username']}" if u.get("username") else str(u.get("id"))
        ico = "👑" if st == "CREATOR" else ("🤖" if u.get("is_bot") else "⭐️")
        lines.append(f"{ico} <b>{u.get('first_name', 'User')}</b> ({uname}){tag} — <code>{st}</code>")
    return "\n".join(lines)


def cmd_admininfo(chat_id: int | str, target: dict, tg_api_fn: Callable[..., dict]) -> str:
    res = tg_api_fn("getChatMember", {"chat_id": chat_id, "user_id": target["id"]})
    if not res.get("ok"):
        return f"⚠️ Unable to fetch member details: {res.get('description')}"
    m = res.get("result") or {}
    st = str(m.get("status", "member")).upper()
    title = m.get("custom_title") or "None"
    lines = [
        f"👤 <b>Administrator Details:</b> <code>{target['id']}</code>",
        f"• <b>Name:</b> {target.get('first_name')}",
        f"• <b>Username:</b> @{target.get('username') or 'none'}",
        f"• <b>Status:</b> <b>{st}</b>",
        f"• <b>Custom Title:</b> <code>{title}</code>\n",
        "<b>Permissions:</b>",
    ]
    perm_keys = [
        "can_change_info", "can_post_messages", "can_edit_messages", "can_delete_messages",
        "can_invite_users", "can_restrict_members", "can_pin_messages", "can_promote_members",
        "can_manage_video_chats", "can_manage_chat"
    ]
    for k in perm_keys:
        ico = "✅" if m.get(k) is True else "❌"
        lines.append(f"{ico} <code>{k}</code>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Moderation Suite: Ban, Unban, Kick, Mute, Unmute, Warn, Purge, Pin, Lock
# ---------------------------------------------------------------------------

def cmd_ban(
    chat_id: int | str,
    actor: dict,
    target: dict,
    reason: str,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    if is_owner(target["id"]):
        return False, "Cannot ban the Bot Owner."
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_restrict_members", tg_api_fn)
    if not ok:
        return False, why
    ok_b, why_b = check_bot_rights(chat_id, "can_restrict_members", tg_api_fn)
    if not ok_b:
        return False, why_b

    res = tg_api_fn("banChatMember", {"chat_id": chat_id, "user_id": target["id"]})
    if not res.get("ok"):
        return False, str(res.get("description") or "Ban failed.")
    log_audit_event("BAN", actor, target, reason or "No reason specified", chat_id, tg_api_fn)
    return True, f"🔨 <b>Banned</b> {target.get('first_name')} (@{target.get('username') or target['id']}). Reason: <i>{reason or 'Violation'}</i>"


def cmd_unban(
    chat_id: int | str,
    actor: dict,
    target: dict,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_restrict_members", tg_api_fn)
    if not ok:
        return False, why
    ok_b, why_b = check_bot_rights(chat_id, "can_restrict_members", tg_api_fn)
    if not ok_b:
        return False, why_b

    res = tg_api_fn("unbanChatMember", {"chat_id": chat_id, "user_id": target["id"], "only_if_banned": True})
    if not res.get("ok"):
        return False, str(res.get("description") or "Unban failed.")
    log_audit_event("UNBAN", actor, target, "Unbanned member", chat_id, tg_api_fn)
    return True, f"🔓 <b>Unbanned</b> {target.get('first_name')} (@{target.get('username') or target['id']})."


def cmd_kick(
    chat_id: int | str,
    actor: dict,
    target: dict,
    reason: str,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    if is_owner(target["id"]):
        return False, "Cannot kick the Bot Owner."
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_restrict_members", tg_api_fn)
    if not ok:
        return False, why
    ok_b, why_b = check_bot_rights(chat_id, "can_restrict_members", tg_api_fn)
    if not ok_b:
        return False, why_b

    res1 = tg_api_fn("banChatMember", {"chat_id": chat_id, "user_id": target["id"]})
    if not res1.get("ok"):
        return False, str(res1.get("description") or "Kick ban phase failed.")
    tg_api_fn("unbanChatMember", {"chat_id": chat_id, "user_id": target["id"]})
    log_audit_event("KICK", actor, target, reason or "Kicked from chat", chat_id, tg_api_fn)
    return True, f"👢 <b>Kicked</b> {target.get('first_name')} (@{target.get('username') or target['id']})."


def cmd_mute(
    chat_id: int | str,
    actor: dict,
    target: dict,
    duration_str: str,
    reason: str,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    if is_owner(target["id"]):
        return False, "Cannot mute the Bot Owner."
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_restrict_members", tg_api_fn)
    if not ok:
        return False, why
    ok_b, why_b = check_bot_rights(chat_id, "can_restrict_members", tg_api_fn)
    if not ok_b:
        return False, why_b

    dur_sec = parse_duration_seconds(duration_str, 600)
    until = int(time.time()) + dur_sec
    perms = {
        "can_send_messages": False,
        "can_send_media_messages": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
    }
    res = tg_api_fn("restrictChatMember", {"chat_id": chat_id, "user_id": target["id"], "permissions": perms, "until_date": until})
    if not res.get("ok"):
        return False, str(res.get("description") or "Mute failed.")
    min_val = round(dur_sec / 60, 1)
    log_audit_event("MUTE", actor, target, f"Muted for {min_val}m. Reason: {reason}", chat_id, tg_api_fn)
    return True, f"🔇 <b>Muted</b> {target.get('first_name')} for {min_val} minutes. Reason: <i>{reason or 'Rule violation'}</i>"


def cmd_unmute(
    chat_id: int | str,
    actor: dict,
    target: dict,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_restrict_members", tg_api_fn)
    if not ok:
        return False, why
    ok_b, why_b = check_bot_rights(chat_id, "can_restrict_members", tg_api_fn)
    if not ok_b:
        return False, why_b

    full_perms = {
        "can_send_messages": True,
        "can_send_media_messages": True,
        "can_send_other_messages": True,
        "can_add_web_page_previews": True,
    }
    res = tg_api_fn("restrictChatMember", {"chat_id": chat_id, "user_id": target["id"], "permissions": full_perms})
    if not res.get("ok"):
        return False, str(res.get("description") or "Unmute failed.")
    log_audit_event("UNMUTE", actor, target, "Restored voice", chat_id, tg_api_fn)
    return True, f"🔊 <b>Unmuted</b> {target.get('first_name')} (@{target.get('username') or target['id']})."


def cmd_warn(
    chat_id: int | str,
    actor: dict,
    target: dict,
    reason: str,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    if is_owner(target["id"]):
        return False, "Cannot warn the Bot Owner."
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_restrict_members", tg_api_fn)
    if not ok:
        return False, why

    data = get_mod_data()
    warns = data.setdefault("warnings", {})
    key = f"{chat_id}:{target['id']}"
    user_warns = warns.setdefault(key, [])
    user_warns.append({"reason": reason or "Rule violation", "by": actor.get("username") or actor.get("id"), "time": _now_ist()})
    count = len(user_warns)
    save_mod_data(data)
    log_audit_event("WARN", actor, target, f"Warn #{count}. Reason: {reason}", chat_id, tg_api_fn)

    if count >= 3:
        warns[key] = []
        save_mod_data(data)
        ok_b, _ = check_bot_rights(chat_id, "can_restrict_members", tg_api_fn)
        if ok_b:
            until = int(time.time()) + 86400
            tg_api_fn("banChatMember", {"chat_id": chat_id, "user_id": target["id"], "until_date": until})
            log_audit_event("AUTO_TEMP_BAN", "SYSTEM", target, "3 warnings limit reached (24h ban)", chat_id, tg_api_fn)
            return True, f"⚠️ <b>Warning 3/3 reached!</b> {target.get('first_name')} has been <b>temporarily banned for 24 hours</b>."
        return True, f"⚠️ <b>Warning 3/3 reached for {target.get('first_name')}!</b> (Bot lacks ban permissions for auto-ban)."

    return True, f"⚠️ <b>Warned</b> {target.get('first_name')} [<b>{count}/3</b>]. Reason: <i>{reason or 'Rule violation'}</i>"


def cmd_warnings(chat_id: int | str, target: dict) -> str:
    data = get_mod_data()
    key = f"{chat_id}:{target['id']}"
    list_w = data.get("warnings", {}).get(key, [])
    if not list_w:
        return f"🟢 <b>{target.get('first_name')}</b> has <b>0</b> active warnings."
    lines = [f"⚠️ <b>Warnings for {target.get('first_name')}</b> ({len(list_w)}/3)\n"]
    for i, w in enumerate(list_w, 1):
        lines.append(f"{i}. <i>{w['reason']}</i> (by @{w.get('by', 'admin')} at <code>{w.get('time')}</code>)")
    return "\n".join(lines)


def cmd_resetwarn(chat_id: int | str, actor: dict, target: dict, tg_api_fn: Callable[..., dict]) -> tuple[bool, str]:
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_restrict_members", tg_api_fn)
    if not ok:
        return False, why
    data = get_mod_data()
    key = f"{chat_id}:{target['id']}"
    data.setdefault("warnings", {})[key] = []
    save_mod_data(data)
    log_audit_event("RESETWARN", actor, target, "Warnings reset to 0", chat_id, tg_api_fn)
    return True, f"🔄 Warnings reset to <b>0</b> for {target.get('first_name')}."


def cmd_purge(
    chat_id: int | str,
    actor: dict,
    msg_id: int,
    count_str: str,
    reply_to_msg_id: int | None,
    tg_api_fn: Callable[..., dict],
) -> tuple[bool, str]:
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_delete_messages", tg_api_fn)
    if not ok:
        return False, why
    ok_b, why_b = check_bot_rights(chat_id, "can_delete_messages", tg_api_fn)
    if not ok_b:
        return False, why_b

    count = int(count_str) if count_str.isdigit() else 20
    count = max(1, min(100, count))
    start_id = reply_to_msg_id or msg_id
    ids = list(range(max(1, start_id - count), start_id + 1))
    tg_api_fn("deleteMessages", {"chat_id": chat_id, "message_ids": ids})
    log_audit_event("PURGE", actor, None, f"Purged up to {count} messages", chat_id, tg_api_fn)
    return True, f"🧹 Purged eligible recent messages (requested: {count})."


def cmd_lock(chat_id: int | str, actor: dict, lock: bool, tg_api_fn: Callable[..., dict]) -> tuple[bool, str]:
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_change_info", tg_api_fn)
    if not ok:
        return False, why
    ok_b, why_b = check_bot_rights(chat_id, "can_restrict_members", tg_api_fn)
    if not ok_b:
        return False, why_b

    perms = {
        "can_send_messages": not lock,
        "can_send_media_messages": not lock,
        "can_send_other_messages": not lock,
        "can_add_web_page_previews": not lock,
    }
    res = tg_api_fn("setChatPermissions", {"chat_id": chat_id, "permissions": perms})
    if not res.get("ok"):
        return False, str(res.get("description") or "Set chat permissions failed.")
    action = "LOCK" if lock else "UNLOCK"
    log_audit_event(action, actor, None, f"Group messaging {'locked' if lock else 'unlocked'}", chat_id, tg_api_fn)
    return True, f"🔒 Group has been <b>{'LOCKED' if lock else 'UNLOCKED'}</b> for regular members."


def cmd_slowmode(chat_id: int | str, actor: dict, delay_str: str, tg_api_fn: Callable[..., dict]) -> tuple[bool, str]:
    ok, why = check_actor_admin(chat_id, actor.get("id"), "can_change_info", tg_api_fn)
    if not ok:
        return False, why
    delay = int(delay_str) if delay_str.isdigit() else 10
    delay = max(0, min(21600, delay))
    res = tg_api_fn("setChatSlowModeDelay", {"chat_id": chat_id, "slow_mode_delay": delay})
    if not res.get("ok"):
        return False, str(res.get("description") or "Slowmode config failed.")
    log_audit_event("SLOWMODE", actor, None, f"Delay set to {delay}s", chat_id, tg_api_fn)
    return True, f"⏱ Slowmode delay set to <b>{delay} seconds</b>."


def check_flood_and_filters(msg: dict, chat_id: int | str, tg_api_fn: Callable[..., dict]) -> bool:
    """Anti-spam, keyword blacklist, and message flood rate-limiter for groups."""
    chat_type = str((msg.get("chat") or {}).get("type", ""))
    if chat_type not in ("group", "supergroup"):
        return False
    u = msg.get("from") or {}
    uid = u.get("id")
    if not uid or is_owner(uid):
        return False
    ok_adm, _ = check_actor_admin(chat_id, uid, None, tg_api_fn)
    if ok_adm:
        return False

    now = time.time()
    k = f"{chat_id}:{uid}"
    times = _FLOOD_TRACKER.setdefault(k, [])
    times.append(now)
    _FLOOD_TRACKER[k] = [t for t in times if now - t <= 3.0]
    data = get_mod_data()
    thresh = data.get("flood_threshold", 5)
    if len(_FLOOD_TRACKER[k]) > thresh:
        tg_api_fn("deleteMessage", {"chat_id": chat_id, "message_id": msg.get("message_id")})
        tg_api_fn("restrictChatMember", {
            "chat_id": chat_id,
            "user_id": uid,
            "permissions": {"can_send_messages": False},
            "until_date": int(now) + 300
        })
        log_audit_event("AUTO_MUTE_FLOOD", "SYSTEM", u, "Exceeded message flood limit (muted 5m)", chat_id, tg_api_fn)
        return True

    text = str(msg.get("text") or msg.get("caption") or "").lower()
    for kw in data.get("blacklist_keywords", []):
        if kw.lower() in text:
            tg_api_fn("deleteMessage", {"chat_id": chat_id, "message_id": msg.get("message_id")})
            log_audit_event("FILTER_KEYWORD", "SYSTEM", u, f"Deleted message matching '{kw}'", chat_id, tg_api_fn)
            return True

    return False


# ---------------------------------------------------------------------------
# Video Management: Public & Private Controls
# ---------------------------------------------------------------------------

def set_video_privacy(item_id: str, is_public: bool) -> tuple[bool, str, dict | None]:
    data = _read_json(UPLOAD_Q_PATH, {"items": []})
    items = data.get("items", [])
    q = item_id.strip().lower()
    target = None
    for it in items:
        if it["id"].lower() == q or it["id"].lower().startswith(q):
            target = it
            break
    if not target:
        return False, f"Video '{item_id}' not found in upload queue.", None

    new_status = "UPLOADED" if is_public else "UPLOADED_PRIVATE"
    target["status"] = new_status
    target["updated_at_ist"] = _now_ist()
    target["manual_privacy_override"] = "public" if is_public else "private"
    _write_json(UPLOAD_Q_PATH, data)
    return True, f"Video <code>{target['id']}</code> marked <b>{'PUBLIC' if is_public else 'PRIVATE'}</b>.", target


# ---------------------------------------------------------------------------
# Database Backup & Bot Management
# ---------------------------------------------------------------------------

def create_database_backup() -> tuple[bytes, str]:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in DATA_DIR.glob("*.json"):
            zf.writestr(f"data/{p.name}", p.read_bytes())
    buf.seek(0)
    fname = f"babybeats_backup_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.zip"
    return buf.getvalue(), fname


def broadcast_message(text: str, tg_api_fn: Callable[..., dict]) -> tuple[int, int]:
    data = get_mod_data()
    targets = set()
    for uid in data.get("registered_users", {}):
        targets.add(int(uid))
    for cid in data.get("registered_groups", {}):
        targets.add(int(cid))

    success = 0
    failed = 0
    for tid in targets:
        res = tg_api_fn("sendMessage", {"chat_id": tid, "text": f"📢 <b>Announcement:</b>\n\n{text}", "parse_mode": "HTML"})
        if res.get("ok"):
            success += 1
        else:
            failed += 1
        time.sleep(0.04)
    return success, failed


def get_bot_stats(server_state: dict) -> dict:
    mod = get_mod_data()
    uq = _read_json(UPLOAD_Q_PATH, {"items": []})
    items = uq.get("items", [])
    uploaded = sum(1 for it in items if it.get("status") == "UPLOADED")
    scheduled = sum(1 for it in items if it.get("status") in ("SCHEDULED", "UPLOADED_PRIVATE"))
    ready = sum(1 for it in items if it.get("status") == "READY_FOR_UPLOAD")
    with _LOCK:
        logs_cnt = len(_read_json(AUDIT_LOG_PATH, {"logs": []}).get("logs", []))

    return {
        "users_count": len(mod.get("registered_users", {})),
        "groups_count": len(mod.get("registered_groups", {})),
        "videos_uploaded": uploaded,
        "videos_scheduled": scheduled,
        "videos_ready": ready,
        "videos_total": len(items),
        "audit_logs_count": logs_cnt,
        "maintenance": mod.get("maintenance", False),
        "banned_users_count": len(mod.get("banned_bot_users", [])),
        "server_runs": server_state.get("runs_completed", 0),
        "server_running": server_state.get("running", False),
    }
