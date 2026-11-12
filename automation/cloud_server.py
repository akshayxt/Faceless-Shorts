"""
Zero-dependency Cloud HTTP Runner for Render, Koyeb, Hugging Face Spaces & Railway.

Binds 0.0.0.0:$PORT immediately so free cloud PaaS health checks pass, while running
24/7 SEO refresh, channel reconciliation, YouTube/Zapier uploads, Telegram reporting,
and atomic GitHub state write-backs via github_sync.py.

Endpoints:
  GET /              -> JSON service health & live queue progress
  GET /health        -> same JSON health payload
  GET /dashboard     -> live HTML growth cockpit (automation/dashboard.html)
  GET|POST /run      -> protected trigger (?token=CRON_SECRET or Bearer header)
                        returns 202 Accepted immediately so external crons (cron-job.org)
                        never time out during uploads; pass ?blocking=1 for sync output.
"""
import argparse
import hmac
import http.server
import json
import os
import threading
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

from cloud_autopilot import _queue_counts, run_autopilot
from github_sync import pull_state_files, push_changed_files
from refresh_dashboard import main as refresh_dashboards
from repo_paths import AUTO_DIR

IST = timezone(timedelta(hours=5, minutes=30))
DASHBOARD_HTML = AUTO_DIR / "dashboard.html"

_RUN_LOCK = threading.Lock()
_STATE_LOCK = threading.Lock()
_STATE: dict = {
    "running": False,
    "last_run_ist": None,
    "last_finish_ist": None,
    "last_exit_code": None,
    "last_sync": None,
    "last_error": None,
    "runs_completed": 0,
}


def _now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _execute_cycle(max_uploads: int = 10, dry_run: bool = False, sync_only: bool = False) -> dict:
    """Pull state from GitHub, run cloud autopilot, and push changed files back atomically."""
    if not _RUN_LOCK.acquire(blocking=False):
        return {"started": False, "reason": "already_running"}

    with _STATE_LOCK:
        _STATE["running"] = True
        _STATE["last_run_ist"] = _now_ist()
        _STATE["last_error"] = None

    rc = 1
    push_res: dict = {}
    pull_res: dict = {}
    err_msg: str | None = None
    try:
        pull_res = pull_state_files()
        if pull_res.get("pulled"):
            print(f"GITHUB_PULL_UPDATED: {pull_res['pulled']}", flush=True)
        rc = run_autopilot(
            max_uploads=max_uploads,
            dry_run=dry_run,
            sync_only=sync_only,
            notify=not dry_run,
        )
        if not dry_run:
            push_res = push_changed_files()
            print(f"GITHUB_PUSH_RESULT: {json.dumps(push_res)}", flush=True)
    except Exception as exc:
        err_msg = str(exc)
        print(f"CLOUD_CYCLE_ERROR: {err_msg}", flush=True)
    finally:
        with _STATE_LOCK:
            _STATE["running"] = False
            _STATE["last_finish_ist"] = _now_ist()
            _STATE["last_exit_code"] = rc
            _STATE["last_sync"] = {"pull": pull_res, "push": push_res}
            _STATE["last_error"] = err_msg
            _STATE["runs_completed"] += 1
        _RUN_LOCK.release()

    return {"started": True, "exit_code": rc, "pull": pull_res, "push": push_res, "error": err_msg}


def _is_authorized(handler: http.server.BaseHTTPRequestHandler, query: dict[str, list[str]]) -> tuple[bool, int, str]:
    expected = os.environ.get("CRON_SECRET", "").strip()
    if not expected:
        return False, 503, "CRON_SECRET env var is not configured"
    auth_hdr = (handler.headers.get("Authorization") or "").strip()
    bearer = auth_hdr[7:].strip() if auth_hdr.lower().startswith("bearer ") else ""
    supplied = (
        (query.get("token") or [""])[0].strip()
        or (handler.headers.get("X-Cron-Secret") or "").strip()
        or bearer
    )
    if not supplied or not hmac.compare_digest(supplied, expected):
        return False, 401, "Unauthorized"
    return True, 200, "OK"


class CloudAutopilotHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print(f"[{_now_ist()}] HTTP {self.command} {self.path.split('?')[0]} -> {args[1] if len(args) > 1 else ''}", flush=True)

    def _send_json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, code: int, html: str) -> None:
        raw = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _handle_request(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = urllib.parse.parse_qs(parsed.query)

        if route in ("/", "/health", "/status"):
            done, ready, total, nxt = _queue_counts()
            with _STATE_LOCK:
                snap = dict(_STATE)
            self._send_json(
                200,
                {
                    "service": "babybeats-cloud-server",
                    "status": "ok",
                    "uploaded_or_scheduled": done,
                    "remaining": ready,
                    "total": total,
                    "next_id": nxt,
                    "server_time_ist": _now_ist(),
                    **snap,
                },
            )
            return

        if route == "/dashboard":
            if DASHBOARD_HTML.exists():
                self._send_html(200, DASHBOARD_HTML.read_text(encoding="utf-8"))
            else:
                self._send_html(404, "<h1>Dashboard not generated yet</h1>")
            return

        if route == "/run":
            ok, code, msg = _is_authorized(self, query)
            if not ok:
                self._send_json(code, {"error": msg})
                return
            try:
                max_uploads = max(1, min(31, int((query.get("max_uploads") or ["10"])[0])))
            except ValueError:
                max_uploads = 10
            dry_run = (query.get("dry_run") or ["0"])[0].lower() in ("1", "true", "yes")
            sync_only = (query.get("sync_only") or ["0"])[0].lower() in ("1", "true", "yes")
            blocking = (query.get("blocking") or ["0"])[0].lower() in ("1", "true", "yes")

            with _STATE_LOCK:
                already = bool(_STATE["running"])
            if already:
                self._send_json(200, {"status": "already_running", "started": False})
                return

            if blocking:
                res = _execute_cycle(max_uploads=max_uploads, dry_run=dry_run, sync_only=sync_only)
                self._send_json(200, {"status": "completed", **res})
                return

            threading.Thread(
                target=_execute_cycle,
                kwargs={"max_uploads": max_uploads, "dry_run": dry_run, "sync_only": sync_only},
                daemon=True,
            ).start()
            self._send_json(202, {"status": "accepted", "started": True, "max_uploads": max_uploads, "sync_only": sync_only, "dry_run": dry_run})
            return

        self._send_json(404, {"error": "Not found"})

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or "0")
        if length > 0:
            _ = self.rfile.read(min(length, 65536))
        self._handle_request()


def _internal_scheduler(interval_hours: float) -> None:
    """Optional in-container periodic trigger if host stays continuously awake."""
    if interval_hours <= 0:
        return
    interval_sec = max(300.0, interval_hours * 3600.0)
    while True:
        time.sleep(interval_sec)
        _execute_cycle(max_uploads=10, dry_run=False, sync_only=False)


def _startup_sync() -> None:
    try:
        res = pull_state_files()
        if res.get("pulled"):
            print(f"STARTUP_GITHUB_PULL: {res['pulled']}", flush=True)
        refresh_dashboards()
    except Exception as exc:
        print(f"STARTUP_SYNC_WARN: {exc}", flush=True)


class ThreadedCloudServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    ap.add_argument("--once", action="store_true", help="Run one cycle and exit (no HTTP server)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.once:
        res = _execute_cycle(dry_run=args.dry_run)
        print(json.dumps(res, indent=2), flush=True)
        return int(res.get("exit_code") or 0)

    threading.Thread(target=_startup_sync, daemon=True).start()
    interval_h = float(os.environ.get("AUTO_INTERVAL_HOURS", "6"))
    if interval_h > 0:
        threading.Thread(target=_internal_scheduler, args=(interval_h,), daemon=True).start()

    httpd = ThreadedCloudServer((args.host, args.port), CloudAutopilotHandler)
    print(f"BABYBEATS_CLOUD_SERVER_READY listening={args.host}:{args.port} interval_hours={interval_h}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
