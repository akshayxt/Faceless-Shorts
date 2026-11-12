# BabyBeats Rhymo — Autonomous YouTube Production & 5,000-Subscriber System

## Folder Map (`G:\Faceless-Shorts\automation\`)
- `data/channel_config.json` — Channel niche (`Kids Cartoons, Science Education & Funny Stories`), US target (`en-US`), `made_for_kids: true`, Category `27`, US Eastern publishing schedule (`3:30 PM EST` Short / `6:00 PM EST` Long-form = `02:00` / `04:30 IST`).
- `data/30day_topic_queue.json` — 30 daily kid-safe US English topics scored out of 100 with source URLs, competitor benchmarks, hooks, and thumbnail copy.
- `data/upload_queue.json` — Idempotent upload queue (`READY_FOR_UPLOAD` -> `UPLOADED`, preventing duplicate uploads).
- `data/growth_tracker.json` — Net subscriber progress ledger (`2026-11-09` -> `2026-12-09`, goal `+5,000`).
- `run_pipeline.ps1` — Renders `9:16` Shorts (`1080×1920`, `30fps`, Kokoro + Whisper + procedural SFX + music bed + QA sheet).
- `longform_renderer.mjs` & `build_longform.ps1` — Renders `16:9` multi-chapter animated episodes (`1920×1080`, `24fps`).
- `make_thumbnail.mjs` — Generates mobile-readable `1280×720` custom comic thumbnails via headless Chrome Canvas.
- `build_seo_package.py` — Runs `title.py` + `hookscore.py` and writes full SEO metadata (`tags`, `hashtags`, `chapters`, `pinned comment`, `sources`, `made_for_kids: true`).
- `auto_short_factory.py` — Autonomously scaffolds, scores, renders, verifies via `ffprobe`, and queues the next pending topic.
- `autopilot_loop.ps1` — Non-stopping continuous daemon (`while ($true)`) with PID lock (`logs/autopilot.pid`) and dashboard refresh.
- `youtube_direct_upload.py` & `analytics_sync.py` — Unattended YouTube Data API v3 upload + analytics checkpoints (activated automatically once Google OAuth credentials are added).
- `install_scheduler.ps1` — Registers Windows Task Scheduler daily triggers in local IST timezone + Logon auto-start.
- `dashboard.html` — Local auto-refreshing visual dashboard (mirrors `growth_dashboard.md`).

## Enabling Unattended Auto-Publishing on YouTube
Choose **either** path:
1. **Fresh Antigravity Chat Session (Zapier MCP):** Open a new chat so `zapier_zapier` MCP tools load at startup, then ask Antigravity to upload pending items in `G:\Faceless-Shorts\automation\data\upload_queue.json`.
2. **Direct Windows YouTube OAuth (Fully Autonomous):**
   - Install libs in the venv:
     ```powershell
     C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe -m pip install google-api-python-client google-auth-oauthlib
     ```
   - Save your Google Cloud Desktop OAuth `client_secrets.json` into `G:\Faceless-Shorts\automation\creds\client_secrets.json`.
   - Run once to authorize:
     ```powershell
     C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe G:\Faceless-Shorts\automation\youtube_direct_upload.py --auth-only
     ```
   - `autopilot_loop.ps1` will then automatically publish pending Shorts/Long-form videos and pull analytics!

## Stopping the Background Autopilot Cleanly
Create the sentinel file to stop gracefully after the current cycle finishes:
```powershell
New-Item -ItemType File -Path G:\Faceless-Shorts\automation\logs\STOP_AUTOPILOT -Force
```
