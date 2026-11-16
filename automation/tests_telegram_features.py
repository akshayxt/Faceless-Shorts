import io
import json
import os
import sys
import tempfile
import unittest.mock as mock
from pathlib import Path

sys.path.insert(0, r"g:\Faceless-Shorts\automation")
import telegram_bot as tb
import telegram_moderation as tm

TEST_USER_ID = 7875287164

def run_tests():
    with tempfile.TemporaryDirectory() as tmp:
        tpath = Path(tmp)
        tm.MOD_DATA_PATH = tpath / "moderation_data.json"
        tm.AUDIT_LOG_PATH = tpath / "bot_audit_logs.json"
        tm.UPLOAD_Q_PATH = tpath / "upload_queue.json"
        tb.UPLOAD_Q = tm.UPLOAD_Q_PATH
        tb.AGENT_INBOX_PATH = tpath / "agent_inbox.json"

        tm.save_mod_data({
            "maintenance": False,
            "banned_bot_users": [],
            "registered_users": {str(TEST_USER_ID): {"id": TEST_USER_ID, "username": "testguy", "first_name": "TestGuy"}},
            "registered_groups": {"-1001997761568": {"id": -1001997761568, "title": "TeamXT_Support"}},
            "warnings": {},
            "group_settings": {},
            "logging": {"enabled": True, "channel_id": -1001997761568, "bot_log_message_ids": []},
            "blacklist_keywords": ["t.me/", "free crypto"],
            "flood_threshold": 5,
        })
        tm._write_json(tm.AUDIT_LOG_PATH, {"logs": []})
        tm._write_json(tm.UPLOAD_Q_PATH, {"items": [
            {"id": "day01_short", "status": "UPLOADED", "title": "Mosquito Bite"},
            {"id": "day02_short", "status": "SCHEDULED", "title": "Inside Belly"},
        ]})

        tb._BOT_USERNAME = "messagextrobot"
        calls = []

        def fake_tg_api(method, params=None, **kwargs):
            if method == "getMe":
                return {"ok": True, "result": {"id": 6575470408, "username": "MessageXTRobot"}}
            if method == "getChatMember":
                uid = (params or {}).get("user_id")
                if uid == tb.OWNER_ID:
                    return {"ok": True, "result": {"status": "creator", "user": {"id": tb.OWNER_ID, "first_name": "Akshay"}}}
                if uid == 6575470408:
                    return {"ok": True, "result": {"status": "administrator", "can_restrict_members": True, "can_promote_members": True, "can_delete_messages": True, "can_change_info": True}}
                if uid == 888:
                    return {"ok": True, "result": {"status": "administrator", "can_restrict_members": True, "can_promote_members": True, "can_delete_messages": True, "can_change_info": True}}
                if uid == TEST_USER_ID:
                    return {"ok": True, "result": {"status": "member", "user": {"id": TEST_USER_ID, "first_name": "TestGuy", "username": "testguy"}}}
                return {"ok": True, "result": {"status": "member", "user": {"id": uid, "first_name": "NormalUser"}}}
            if method == "getChatAdministrators":
                return {"ok": True, "result": [
                    {"status": "creator", "user": {"id": tb.OWNER_ID, "first_name": "Akshay", "username": "AkshayGangwar"}},
                    {"status": "administrator", "user": {"id": 888, "first_name": "Admin2", "username": "admin2"}},
                ]}
            calls.append((method, params or {}))
            return {"ok": True, "result": {"message_id": 101}}

        doc_calls = []
        def fake_send_doc(chat_id, file_target, caption="", filename="", reply_to_message_id=None):
            doc_calls.append({"chat_id": chat_id, "filename": filename, "caption": caption})
            return {"ok": True}

        with mock.patch.object(tb, "tg_api", side_effect=fake_tg_api), mock.patch.object(tb, "tg_send_document", side_effect=fake_send_doc):
            # 1. Video Privacy controls
            calls.clear()
            r_priv = tb.handle_webhook_update(
                {"update_id": 1, "message": {"message_id": 10, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": tb.OWNER_ID}, "text": "/private day01_short"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_priv == {"handled": "cmd:private"}, r_priv
            uq_data = tm._read_json(tm.UPLOAD_Q_PATH, {})
            assert uq_data["items"][0]["status"] == "UPLOADED_PRIVATE"
            assert "PRIVATE" in calls[0][1]["text"]

            calls.clear()
            r_pub = tb.handle_webhook_update(
                {"update_id": 2, "message": {"message_id": 11, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": tb.OWNER_ID}, "text": "/public day01_short"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_pub == {"handled": "cmd:public"}, r_pub
            uq_data = tm._read_json(tm.UPLOAD_Q_PATH, {})
            assert uq_data["items"][0]["status"] == "UPLOADED"
            assert "PUBLIC" in calls[0][1]["text"]

            # 2. Group Administration: /promote, /demote, /admins using TEST_USER_ID
            calls.clear()
            r_prom = tb.handle_webhook_update(
                {"update_id": 3, "message": {"message_id": 12, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": tb.OWNER_ID}, "text": f"/promote {TEST_USER_ID}"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_prom == {"handled": "cmd:promote"}
            assert any(c[0] == "promoteChatMember" and c[1]["user_id"] == TEST_USER_ID for c in calls)

            calls.clear()
            r_dem = tb.handle_webhook_update(
                {"update_id": 4, "message": {"message_id": 13, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": tb.OWNER_ID}, "text": f"/demote {TEST_USER_ID}"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_dem == {"handled": "cmd:demote"}
            assert any(c[0] == "promoteChatMember" and c[1]["user_id"] == TEST_USER_ID and c[1]["can_manage_chat"] is False for c in calls)

            calls.clear()
            r_adm = tb.handle_webhook_update(
                {"update_id": 5, "message": {"message_id": 14, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": 888}, "text": "/admins"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_adm == {"handled": "cmd:admins"}
            assert "Group Administrators" in calls[0][1]["text"]

            # 3. Moderation: /ban, /mute, /warn on TEST_USER_ID
            calls.clear()
            r_ban = tb.handle_webhook_update(
                {"update_id": 6, "message": {"message_id": 15, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": 888}, "text": f"/ban {TEST_USER_ID} spam"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_ban == {"handled": "cmd:ban"}
            assert any(c[0] == "banChatMember" and c[1]["user_id"] == TEST_USER_ID for c in calls)

            calls.clear()
            r_mute = tb.handle_webhook_update(
                {"update_id": 7, "message": {"message_id": 16, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": 888}, "text": f"/mute {TEST_USER_ID} 15m rule break"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_mute == {"handled": "cmd:mute"}
            assert any(c[0] == "restrictChatMember" and c[1]["user_id"] == TEST_USER_ID for c in calls)

            # Warning increment & 3rd warn auto-ban on TEST_USER_ID
            tb.handle_webhook_update(
                {"update_id": 8, "message": {"message_id": 17, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": 888}, "text": f"/warn {TEST_USER_ID} bad words"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            tb.handle_webhook_update(
                {"update_id": 9, "message": {"message_id": 18, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": 888}, "text": f"/warn {TEST_USER_ID} bad words 2"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            calls.clear()
            tb.handle_webhook_update(
                {"update_id": 10, "message": {"message_id": 19, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": 888}, "text": f"/warn {TEST_USER_ID} bad words 3"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert any(c[0] == "banChatMember" and c[1]["user_id"] == TEST_USER_ID for c in calls)
            assert any("temporarily banned" in c[1]["text"] for c in calls if c[0] == "sendMessage")

            # 4. Control Panel: /panel with 10 sections
            calls.clear()
            r_pan = tb.handle_webhook_update(
                {"update_id": 11, "message": {"message_id": 20, "chat": {"id": tb.OWNER_ID, "type": "private"}, "from": {"id": tb.OWNER_ID}, "text": "/panel"}},
                lambda: {"runs_completed": 4, "running": False}, lambda **kw: {}, lambda msg: {}
            )
            assert r_pan == {"handled": "cmd:panel"}
            assert "Master Control Cockpit" in calls[0][1]["text"]
            assert len(calls[0][1]["reply_markup"]["inline_keyboard"]) == 6

            # Sub-panel navigation via callback
            calls.clear()
            r_cb_stats = tb.handle_webhook_update(
                {"update_id": 12, "callback_query": {"id": "cq1", "from": {"id": tb.OWNER_ID}, "message": {"message_id": 20, "chat": {"id": tb.OWNER_ID, "type": "private"}}, "data": "cb:panel:stats"}},
                lambda: {"runs_completed": 4, "running": False}, lambda **kw: {}, lambda msg: {}
            )
            assert r_cb_stats == {"handled": "callback:cb:panel:stats"}
            assert any(c[0] == "editMessageText" and "General Bot Statistics" in c[1]["text"] for c in calls)

            # 5. Database Backup
            doc_calls.clear()
            r_bak = tb.handle_webhook_update(
                {"update_id": 13, "message": {"message_id": 21, "chat": {"id": tb.OWNER_ID, "type": "private"}, "from": {"id": tb.OWNER_ID}, "text": "/backup"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_bak == {"handled": "cmd:backup"}
            assert len(doc_calls) == 1 and doc_calls[0]["filename"].endswith(".zip")

            # 6. Unauthorized roast check when TEST_USER_ID attempts an unauthorized command
            calls.clear()
            r_unauth = tb.handle_webhook_update(
                {"update_id": 14, "message": {"message_id": 22, "chat": {"id": -1001997761568, "type": "supergroup"}, "from": {"id": TEST_USER_ID}, "text": "/panel"}},
                lambda: {}, lambda **kw: {}, lambda msg: {}
            )
            assert r_unauth == {"handled": "unauthorized_message"}
            assert calls[0][1]["text"] == "Baap Ko Bhej Tere Bs Ki Baat Ni Meethe"

    print(f"ALL_UNIT_TESTS_PASSED_SUCCESSFULLY! Tested with ID: {TEST_USER_ID}")

if __name__ == "__main__":
    run_tests()
