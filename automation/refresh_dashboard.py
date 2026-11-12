import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"G:\Faceless-Shorts")
AUTO = ROOT / "automation"
QUEUE_PATH = AUTO / "data" / "30day_topic_queue.json"
UPLOAD_Q_PATH = AUTO / "data" / "upload_queue.json"
GROWTH_PATH = AUTO / "data" / "growth_tracker.json"
CHANNEL_PATH = AUTO / "data" / "channel_config.json"
LOCK_PATH = AUTO / "logs" / "autopilot.pid"
LOG_PATH = AUTO / "logs" / "autopilot.log"
HTML_OUT = AUTO / "dashboard.html"
MD_ARTIFACT = Path(r"C:\Users\Admin\.gemini\antigravity\brain\91b89b72-aed5-4703-add7-594e8deab7a2\growth_dashboard.md")
IST = timezone(timedelta(hours=5, minutes=30))


def read_json(p: Path, default):
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    now_ist = datetime.now(IST)
    cfg = read_json(CHANNEL_PATH, {})
    growth = read_json(GROWTH_PATH, {})
    tq = read_json(QUEUE_PATH, {"topics": []})
    uq = read_json(UPLOAD_Q_PATH, {"items": []})

    topics = tq.get("topics", [])
    items = uq.get("items", [])
    start_subs = int(growth.get("starting_subscribers", 0))
    cur_subs = int(growth.get("current_subscribers", 0))
    net_gained = cur_subs - start_subs
    target_subs = int(growth.get("target_net_subscribers", 5000))
    rem_subs = max(0, target_subs - net_gained)
    end_dt = datetime.fromisoformat(growth.get("campaign_end_date", "2026-12-09") + "T23:59:59+05:30")
    rem_days = max(1, (end_dt.date() - now_ist.date()).days)
    req_per_day = round(rem_subs / rem_days, 1)

    rendered_cnt = sum(1 for it in items if it.get("status") in ("READY_FOR_UPLOAD", "UPLOADED", "SCHEDULED", "UPLOADED_PRIVATE") or it.get("youtube_video_id"))
    uploaded_cnt = sum(1 for it in items if it.get("status") in ("UPLOADED", "SCHEDULED", "UPLOADED_PRIVATE") or bool(it.get("youtube_video_id")))
    remaining_uploads = max(0, len(items) - uploaded_cnt)
    seo_sync = uq.get("realtime_seo_last_sync_ist", "Not yet synced")
    pending_cnt = sum(1 for t in topics if t.get("status", "pending") == "pending")
    pid = LOCK_PATH.read_text(encoding="utf-8").strip() if LOCK_PATH.exists() else "Not running"
    recent_logs = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-15:] if LOG_PATH.exists() else []

    # 1. Generate visual HTML cockpit
    rows_html = []
    for it in items:
        vid_file = Path(it.get("video_path", "")).name
        specs = it.get("video_specs", {})
        res_str = f"{specs.get('width', '?')}x{specs.get('height', '?')} ({specs.get('duration_sec', '?')}s)"
        badge_cls = "ok" if (it.get("status") in ("UPLOADED", "SCHEDULED", "UPLOADED_PRIVATE") or it.get("youtube_video_id")) else "ready"
        rows_html.append(
            f"<tr><td>{it['id']}</td><td>{it['format'].upper()}</td><td>{it['title']}</td>"
            f"<td>{res_str}</td><td><span class='badge {badge_cls}'>{it['status']}</span></td>"
            f"<td><code>{vid_file}</code></td></tr>"
        )

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="30">
<title>BabyBeats Rhymo — 5,000 Sub Autopilot</title>
<style>
  body {{ font-family: system-ui, sans-serif; background:#0F172A; color:#F8FAFC; margin:0; padding:28px; }}
  h1,h2 {{ margin:0 0 14px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; margin-bottom:24px; }}
  .card {{ background:#1E293B; border:2px solid #334155; border-radius:14px; padding:16px; }}
  .val {{ font-size:28px; font-weight:800; color:#FFD43B; }}
  .lbl {{ font-size:13px; color:#94A3B8; margin-top:4px; }}
  table {{ width:100%; border-collapse:collapse; background:#1E293B; border-radius:12px; overflow:hidden; margin-bottom:24px; }}
  th,td {{ text-align:left; padding:11px 14px; border-bottom:1px solid #334155; font-size:14px; }}
  th {{ background:#0B1120; color:#CBD5E1; }}
  .badge {{ padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; }}
  .ready {{ background:#FDE047; color:#18181B; }}
  .ok {{ background:#22C55E; color:#052E16; }}
  pre {{ background:#020617; padding:14px; border-radius:10px; overflow-x:auto; font-size:12px; color:#A5F3FC; }}
</style></head>
<body>
  <h1>BabyBeats Rhymo — Autonomous 5,000 Subscriber Engine</h1>
  <p style="color:#94A3B8">Channel ID: <code>{cfg.get('channel_id','UCR-Di4-tEAdUM7oPzlGn-vg')}</code> · Last refreshed: {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')} · Real-Time US SEO Sync: <code>{seo_sync}</code> · Autopilot PID: <code>{pid}</code></p>
  <div class="grid">
    <div class="card"><div class="val">{net_gained} / {target_subs}</div><div class="lbl">Net New Subscribers (Current: {cur_subs})</div></div>
    <div class="card"><div class="val">{rem_days} days</div><div class="lbl">Remaining Campaign Days ({req_per_day}/day needed)</div></div>
    <div class="card"><div class="val">{uploaded_cnt} / {len(items)}</div><div class="lbl">Uploaded & Scheduled ({remaining_uploads} Remaining)</div></div>
    <div class="card"><div class="val">{pending_cnt} / {len(topics)}</div><div class="lbl">Pending Topic Renders ({rendered_cnt} Verified)</div></div>
  </div>
  <h2>Production & Upload Queue</h2>
  <table><thead><tr><th>ID</th><th>Format</th><th>Selected SEO Title</th><th>Media Specs</th><th>Status</th><th>File</th></tr></thead>
  <tbody>{''.join(rows_html) if rows_html else '<tr><td colspan="6">No queue items yet.</td></tr>'}</tbody></table>
  <h2>Recent Autopilot Loop Logs</h2>
  <pre>{chr(10).join(recent_logs) if recent_logs else 'Waiting for first heartbeat...'}</pre>
</body></html>"""
    HTML_OUT.write_text(html, encoding="utf-8")

    # 2. Update markdown artifact dashboard
    def md_cell(text: str) -> str:
        return str(text).replace("|", "\\|")

    md_rows = []
    for it in items:
        sp = it.get("video_specs", {})
        dim = f"{sp.get('width', '?')}x{sp.get('height', '?')}, {sp.get('duration_sec', '?')}s"
        sched = it.get("scheduled_publish_est", it.get("scheduled_slot_est", "—")).replace("T", " ").replace("-05:00", " EST")
        seo_sc = it.get("realtime_seo_score", "—")
        md_rows.append(
            f"| `{it['id']}` | {it['format']} | {md_cell(it['title'])} | {seo_sc}/100 | {sched} | {dim} | `{it['status']}` | [{Path(it['video_path']).name}](file:///{it['video_path'].replace(chr(92), '/')}) |"
        )

    top10 = []
    for t in topics[:10]:
        top10.append(f"| Day {t['day']:02d} | {t['category']} | {md_cell(t['title'])} | **{t['total_score']}/100** | `{t.get('status', 'pending')}` |")

    md = f"""# YouTube 5,000 Subscriber Autopilot Dashboard — BabyBeats Rhymo

> [!NOTE]
> Live workspace dashboard updated automatically at `{now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}` by [`refresh_dashboard.py`](file:///G:/Faceless-Shorts/automation/refresh_dashboard.py).
> Channel counts remain at baseline until live YouTube OAuth / Zapier MCP telemetry pulls post-upload data (never fabricated).

## 1. Channel Identity & Campaign Telemetry
- **Channel:** **BabyBeats Rhymo** (`UCR-Di4-tEAdUM7oPzlGn-vg`)
- **Primary Niche:** Kids Cartoons, Science Education & Funny Stories (`made_for_kids: true`, Category `27`)
- **Language & Market:** **US English ONLY (`am_puck`, `en-US`)** — targeting US kids & families
- **Publishing Schedule (US Eastern):** Daily Short at **3:30 PM EST** (`02:00 AM IST`) | Daily Long-Form at **6:00 PM EST** (`04:30 AM IST`)
- **Autopilot Daemon PID:** `{pid}` · Live Local Cockpit: [`dashboard.html`](file:///G:/Faceless-Shorts/automation/dashboard.html)

| Metric | Value |
|---|---|
| Campaign Target (`2026-11-09` -> `2026-12-09`) | **+5,000 net new subscribers** |
| Starting / Current Subscribers | `{start_subs}` / `{cur_subs}` *(pending live analytics pull)* |
| Net Gained / Remaining | `{net_gained}` / `{rem_subs}` |
| Remaining Days / Required Daily Rate | `{rem_days}` days / **`{req_per_day}` subs/day** |
| Videos Rendered & Verified | **`{rendered_cnt}`** (`{uploaded_cnt}` uploaded/scheduled, `{remaining_uploads}` remaining) |
| Real-Time US SEO Sync | `{seo_sync}` |
| Topic Backlog Remaining | `{pending_cnt}` pending out of `{len(topics)}` scored |

## 2. Production & Upload Queue Status

| Queue ID | Format | Selected SEO Title | SEO Score | Scheduled EST | Verified Specs | Status | Deliverable |
|---|---|---|---|---|---|---|---|
{chr(10).join(md_rows) if md_rows else '| — | — | Pending first render | — | — | — | — | — |'}

### Publishing Status Note
- Automated unattended publishing runs via [`youtube_direct_upload.py`](file:///G:/Faceless-Shorts/automation/youtube_direct_upload.py) once Google OAuth credentials (`client_secrets.json`) are placed in `G:/Faceless-Shorts/automation/creds/`, **or** by opening a fresh chat session where `zapier_zapier` MCP tools are loaded and triggering upload from `upload_queue.json`.
- Duplicate uploads are blocked automatically by checking `status == "UPLOADED"` and non-empty `youtube_video_id`.

## 3. Top 10 Daily Viral Leaderboard (Scored /100)

| Day | Category | Video Opportunity Title | Score | Queue Status |
|---|---|---|---|---|
{chr(10).join(top10)}

## 4. Automation Loop Heartbeat (Latest Entries)
```text
{chr(10).join(recent_logs) if recent_logs else 'No log lines recorded yet.'}
```
"""
    MD_ARTIFACT.write_text(md, encoding="utf-8")
    print(f"Dashboard refreshed -> {HTML_OUT} & {MD_ARTIFACT}")


if __name__ == "__main__":
    from telegram_logger import wrap_if_top_level
    wrap_if_top_level("DASHBOARD", __file__, sys.argv[1:])
    main()
