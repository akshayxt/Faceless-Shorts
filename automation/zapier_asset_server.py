"""
Scoped, read-only local HTTP server + Cloudflare Quick Tunnel for Zapier MCP uploads.
Only serves the explicit allowlisted .mp4 and .jpg render files listed in upload_queue.json
under an unguessable random URL token prefix, bound to 127.0.0.1.
Also provides CLI subcommands to build exact Zapier upload payloads and persist uploaded IDs.
"""
import argparse
import http.server
import json
import os
import re
import secrets
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_tunnel_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host and (host.endswith("trycloudflare.com") or host.endswith("lhr.life")) and family in (0, socket.AF_UNSPEC):
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _ipv4_tunnel_getaddrinfo

AUTO = Path(r"G:\Faceless-Shorts\automation")
UPLOAD_Q = AUTO / "data" / "upload_queue.json"
TOPIC_Q = AUTO / "data" / "30day_topic_queue.json"
TUNNEL_STATE = AUTO / "logs" / "zapier_tunnel.json"
STOP_FILE = AUTO / "logs" / "STOP_TUNNEL"
IST = timezone(timedelta(hours=5, minutes=30))


def find_cloudflared() -> str | None:
    exe = shutil.which("cloudflared")
    if exe:
        return exe
    candidates = [
        Path(r"C:\Program Files (x86)\cloudflared\cloudflared.exe"),
        Path(r"C:\Program Files\cloudflared\cloudflared.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "cloudflared.exe",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    pkg_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if pkg_root.exists():
        for match in pkg_root.rglob("cloudflared.exe"):
            return str(match)
    return None


def build_asset_map() -> dict[str, tuple[Path, str]]:
    """Map '<item_id>.mp4' and '<item_id>.jpg' strictly to allowlisted existing render files."""
    uq = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    assets: dict[str, tuple[Path, str]] = {}
    for it in uq.get("items", []):
        iid = it["id"]
        vp = Path(it.get("video_path", ""))
        tp = Path(it.get("thumb_path", ""))
        if vp.exists() and vp.is_file():
            assets[f"{iid}.mp4"] = (vp, "video/mp4")
        if tp.exists() and tp.is_file():
            assets[f"{iid}.jpg"] = (tp, "image/jpeg")
    return assets


def make_handler(token: str, assets: dict[str, tuple[Path, str]]):
    prefix = f"/{token}/"

    class ScopedAssetHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            ts = datetime.now(IST).strftime("%H:%M:%S")
            print(f"[{ts}] ASSET_HTTP {self.command} {self.path.split('/')[-1]} -> {args[1] if len(args) > 1 else ''}", flush=True)

        def _resolve(self):
            clean_path = self.path.split("?", 1)[0]
            if not clean_path.startswith(prefix):
                return None
            rel = clean_path[len(prefix):]
            if "/" in rel or "\\" in rel or ".." in rel:
                return None
            return assets.get(rel)

        def do_HEAD(self):
            resolved = self._resolve()
            if not resolved:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            fpath, ctype = resolved
            size = fpath.stat().st_size
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def do_GET(self):
            resolved = self._resolve()
            if not resolved:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            fpath, ctype = resolved
            size = fpath.stat().st_size
            rng = self.headers.get("Range")
            start, end = 0, size - 1
            status = 200
            if rng and rng.startswith("bytes="):
                spec = rng[6:].split(",", 1)[0].strip()
                m = re.match(r"^(\d*)-(\d*)$", spec)
                if m:
                    s_str, e_str = m.groups()
                    if s_str:
                        start = int(s_str)
                        end = int(e_str) if e_str else size - 1
                    elif e_str:
                        suffix = int(e_str)
                        start = max(0, size - suffix)
                        end = size - 1
                    if start >= size or start > end:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{size}")
                        self.end_headers()
                        return
                    end = min(end, size - 1)
                    status = 206

            length = end - start + 1
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()

            try:
                with fpath.open("rb") as fh:
                    fh.seek(start)
                    rem = length
                    while rem > 0:
                        chunk = fh.read(min(262144, rem))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        rem -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

    return ScopedAssetHandler


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _record_tunnel_state(public_host: str, token: str, port: int, pid: int, asset_count: int, provider: str, registered: bool) -> dict:
    """Persist active tunnel metadata so payload queries read the current public base URL."""
    state = {
        "started_at_ist": datetime.now(IST).isoformat(),
        "provider": provider,
        "public_host": public_host,
        "token": token,
        "base_url": f"{public_host}/{token}",
        "local_port": port,
        "tunnel_pid": pid,
        "server_pid": os.getpid(),
        "asset_count": asset_count,
        "registered": registered,
    }
    TUNNEL_STATE.parent.mkdir(parents=True, exist_ok=True)
    TUNNEL_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def _verify_tunnel_url(public_host: str, token: str) -> bool:
    """Confirm end-to-end HTTPS reachability of a real allowlisted MP4 file."""
    test_url = f"{public_host}/{token}/day01_short.mp4"
    for _ in range(8):
        try:
            req = urllib.request.Request(test_url, method="HEAD", headers={"User-Agent": "BabyBeatsTunnelCheck/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                ctype = (r.headers.get("Content-Type") or "").lower()
                if r.status == 200 and "video/mp4" in ctype:
                    print(f"TUNNEL_HTTPS_VERIFIED status={r.status} content_length={r.headers.get('Content-Length')}", flush=True)
                    return True
        except Exception:
            pass
        time.sleep(2.0)
    return False


def _start_tunnel_attempt(
    name: str,
    cmd: list[str],
    url_re: re.Pattern[str],
    ready_substr: str,
    token: str,
    port: int,
    asset_count: int,
    startup_timeout_s: float = 25.0,
) -> tuple[subprocess.Popen | None, str | None]:
    """Launch one tunnel backend process and return (proc, public_host) once verified."""
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    public_host = None
    registered = False
    verified = False
    start_t = time.time()
    recent_lines: list[str] = []
    assert proc.stdout is not None

    while proc.poll() is None:
        line = proc.stdout.readline()
        if not line:
            if not verified and (time.time() - start_t > startup_timeout_s):
                break
            time.sleep(0.1)
            continue
        clean_ln = line.strip()
        if clean_ln:
            recent_lines.append(clean_ln)
            if len(recent_lines) > 8:
                recent_lines.pop(0)
        m = url_re.search(line)
        if m and not public_host:
            public_host = m.group(0)
            _record_tunnel_state(public_host, token, port, proc.pid, asset_count, name, registered=False)
            print(f"TUNNEL_URL_ISSUED provider={name} host={public_host} allowlisted_files={asset_count}", flush=True)

        if public_host and ready_substr in line and not registered:
            registered = True
            _record_tunnel_state(public_host, token, port, proc.pid, asset_count, name, registered=True)
            print(f"TUNNEL_REGISTERED provider={name} host={public_host}", flush=True)
            time.sleep(1.5)
            verified = _verify_tunnel_url(public_host, token)
            if verified:
                return proc, public_host
            break

        if not public_host and (time.time() - start_t > startup_timeout_s):
            break
        if STOP_FILE.exists():
            break

    print(f"TUNNEL_ATTEMPT_FAILED provider={name}: " + " | ".join(recent_lines[-3:]), flush=True)
    if proc.poll() is None:
        proc.terminate()
    return None, None


def serve_tunnel(port: int, provider: str = "auto"):
    """Serve allowlisted renders over a local server + temporary HTTPS tunnel."""
    if STOP_FILE.exists():
        STOP_FILE.unlink()

    token = secrets.token_urlsafe(24)
    assets = build_asset_map()
    server = ThreadedHTTPServer(("127.0.0.1", port), make_handler(token, assets))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"LOCAL_ASSET_SERVER_READY port={port} allowlisted_files={len(assets)}", flush=True)

    candidates: list[tuple[str, list[str], re.Pattern[str], str, float]] = []
    cf_bin = find_cloudflared()
    if provider in ("auto", "cloudflared") and cf_bin:
        cf_re = re.compile(r"https://(?!api\.)[a-z0-9-]+-[a-z0-9-]+\.trycloudflare\.com")
        candidates.append(("cloudflared", [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{port}", "--edge-ip-version", "4", "--protocol", "http2", "--no-autoupdate"], cf_re, "Registered tunnel connection", 22.0))
        if provider == "auto":
            candidates.append(("cloudflared", [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{port}", "--edge-ip-version", "4", "--protocol", "http2", "--no-autoupdate"], cf_re, "Registered tunnel connection", 22.0))

    ssh_bin = shutil.which("ssh")
    if provider in ("auto", "localhostrun") and ssh_bin:
        known_hosts = AUTO / "logs" / "tunnel_known_hosts"
        known_hosts.parent.mkdir(parents=True, exist_ok=True)
        lhr_re = re.compile(r"https://[a-z0-9.-]+\.lhr\.life")
        candidates.append((
            "localhostrun",
            [ssh_bin, "-T", "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={known_hosts}", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=15", "-o", "ConnectTimeout=12", "-R", f"80:127.0.0.1:{port}", "nokey@localhost.run"],
            lhr_re,
            ".lhr.life",
            22.0,
        ))

    if not candidates:
        print("ERROR: Neither cloudflared.exe nor ssh.exe available for HTTPS tunneling.", flush=True)
        server.shutdown()
        server.server_close()
        return 2

    proc = None
    public_host = None
    try:
        for name, cmd, regex, ready_sub, tmo in candidates:
            if STOP_FILE.exists():
                break
            proc, public_host = _start_tunnel_attempt(name, cmd, regex, ready_sub, token, port, len(assets), tmo)
            if proc and public_host:
                break
            time.sleep(1.5)

        while proc is not None and proc.poll() is None:
            if STOP_FILE.exists():
                print("STOP_TUNNEL sentinel detected; shutting down cleanly.", flush=True)
                break
            # Drain stdout continuously so child pipe never fills during uploads
            if proc.stdout:
                _ = proc.stdout.readline()
            else:
                time.sleep(1.0)
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
        server.shutdown()
        server.server_close()
    return 0 if public_host else 1


def build_payload(item_id: str, include_publish_at: bool = True, include_thumb: bool = True) -> dict:
    if not TUNNEL_STATE.exists():
        raise FileNotFoundError(f"Missing active tunnel state: {TUNNEL_STATE}")
    st = json.loads(TUNNEL_STATE.read_text(encoding="utf-8"))
    uq = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    it = next((x for x in uq.get("items", []) if x["id"] == item_id), None)
    if not it:
        raise ValueError(f"Queue item not found: {item_id}")
    seo = json.loads(Path(it["seo_path"]).read_text(encoding="utf-8"))

    # Use live real-time SEO values
    base_url = st["base_url"]
    params = {
        "title": seo["selected_title"][:100],
        "description": seo["description"],
        "tags": seo["tags"][:15],
        "video": f"{base_url}/{item_id}.mp4",
        "category_id": str(seo["youtube_settings"].get("category_id", "27")),
        "made_for_kids": "true" if seo["youtube_settings"].get("made_for_kids", True) else "false",
        "default_language": seo["youtube_settings"].get("default_language", "en"),
        "default_audio_language": seo["youtube_settings"].get("default_audio_language", "en-US"),
        "privacy_status": "private",
        "license": "youtube",
        "embeddable": "true",
        "notify_subscribers": "true",
        "public_stats_viewable": "true",
    }
    if include_thumb:
        params["thumbnail"] = f"{base_url}/{item_id}.jpg"
    if include_publish_at and it.get("publish_at"):
        params["publish_at"] = it["publish_at"]
    return {
        "id": item_id,
        "scheduled_publish_est": it.get("scheduled_publish_est"),
        "publish_at": it.get("publish_at"),
        "seo_score": seo["selected_title_lint"].get("score"),
        "zapier_params": params,
    }


def mark_uploaded(item_id: str, video_id: str, status: str, note: str = "") -> dict:
    uq = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    target = None
    for it in uq.get("items", []):
        if it["id"] == item_id:
            target = it
            break
    if not target:
        raise ValueError(f"Queue item not found: {item_id}")

    url = f"https://www.youtube.com/watch?v={video_id}"
    target["status"] = status
    target["youtube_video_id"] = video_id
    target["youtube_url"] = url
    target["upload_method"] = "zapier_mcp"
    target["uploaded_at_ist"] = datetime.now(IST).isoformat()
    if note:
        target["upload_note"] = note
    UPLOAD_Q.write_text(json.dumps(uq, indent=2, ensure_ascii=False), encoding="utf-8")

    # Sync topic status cleanly when short uploads
    if TOPIC_Q.exists() and target.get("format") == "short":
        tq = json.loads(TOPIC_Q.read_text(encoding="utf-8"))
        for t in tq.get("topics", []):
            if t["id"] == target.get("topic_id"):
                t["status"] = status.lower()
                t["youtube_video_id"] = video_id
                t["youtube_url"] = url
        TOPIC_Q.write_text(json.dumps(tq, indent=2, ensure_ascii=False), encoding="utf-8")

    refresh_py = AUTO / "refresh_dashboard.py"
    if refresh_py.exists():
        subprocess.run([sys.executable, str(refresh_py)], check=False)

    return {"id": item_id, "status": status, "youtube_video_id": video_id, "youtube_url": url}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_srv = sub.add_parser("serve")
    p_srv.add_argument("--port", type=int, default=18923)
    p_srv.add_argument("--provider", choices=["auto", "cloudflared", "localhostrun"], default="auto")

    p_pay = sub.add_parser("payload")
    p_pay.add_argument("--id", required=True)
    p_pay.add_argument("--no-publish-at", action="store_true")
    p_pay.add_argument("--no-thumb", action="store_true")

    p_mrk = sub.add_parser("mark")
    p_mrk.add_argument("--id", required=True)
    p_mrk.add_argument("--video-id", required=True)
    p_mrk.add_argument("--status", default="SCHEDULED")
    p_mrk.add_argument("--note", default="")

    args = ap.parse_args()
    if args.cmd == "serve":
        from telegram_logger import wrap_if_top_level
        wrap_if_top_level("ZAPIER_TUNNEL", __file__, sys.argv[1:])
        return serve_tunnel(args.port, provider=args.provider)
    elif args.cmd == "payload":
        out = build_payload(args.id, include_publish_at=not args.no_publish_at, include_thumb=not args.no_thumb)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    elif args.cmd == "mark":
        out = mark_uploaded(args.id, args.video_id, args.status, args.note)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
