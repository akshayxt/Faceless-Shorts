"""
Centralized Telegram Live Process Log Streamer for BabyBeats Rhymo Automation.
Forwards EVERY process stdout/stderr line (buffered in <=3500 char chunks every ~4s
to respect Telegram Bot API rate limits and 4096-char cap) to Telegram group chat.
"""
import argparse
import html
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Force IPv4 when calling Telegram API on Windows so IPv6 fallback never stalls for 15s
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_telegram_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == "api.telegram.org" and family in (0, socket.AF_UNSPEC):
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _ipv4_telegram_getaddrinfo

AUTO = Path(r"G:\Faceless-Shorts\automation")
CFG_PATH = AUTO / "data" / "telegram_config.json"
ALL_LOG_PATH = AUTO / "logs" / "all_processes.log"
IST = timezone(timedelta(hours=5, minutes=30))


def load_config() -> dict:
    if not CFG_PATH.exists():
        return {"enabled": False}
    return json.loads(CFG_PATH.read_text(encoding="utf-8"))


def _post_telegram(token: str, chat_id: str, html_text: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": str(chat_id),
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 429:
                retry = 3
                try:
                    retry = int(json.loads(body).get("parameters", {}).get("retry_after", 3)) + 1
                except Exception:
                    pass
                time.sleep(min(retry, 20))
                continue
            return {"ok": False, "error_code": e.code, "description": body}
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5)
                continue
            return {"ok": False, "description": str(e)}
    return {"ok": False, "description": "Max retries exceeded"}


def chunk_lines(text: str, max_len: int = 3400) -> list[str]:
    text = text.rstrip("\r\n")
    if not text:
        return []
    chunks = []
    cur = []
    cur_len = 0
    for line in text.splitlines():
        if len(line) > max_len:
            if cur:
                chunks.append("\n".join(cur))
                cur, cur_len = [], 0
            for i in range(0, len(line), max_len):
                chunks.append(line[i:i + max_len])
            continue
        add_len = len(line) + (1 if cur else 0)
        if cur_len + add_len > max_len:
            chunks.append("\n".join(cur))
            cur, cur_len = [line], len(line)
        else:
            cur.append(line)
            cur_len += add_len
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def send_telegram(text: str, tag: str = "PROCESS") -> bool:
    cfg = load_config()
    if not cfg.get("enabled"):
        return False
    token = cfg.get("bot_token", "")
    chat_id = str(cfg.get("chat_id", ""))
    if not token or not chat_id:
        return False
    max_chars = int(cfg.get("max_chars_per_message", 3400))
    ts = datetime.now(IST).strftime("%H:%M:%S IST")
    chunks = chunk_lines(text, max_chars)
    total = len(chunks)
    ok_all = True
    for idx, ch in enumerate(chunks, 1):
        part = f" [{idx}/{total}]" if total > 1 else ""
        header = f"<b>[{html.escape(tag)}]{part}</b> <code>{ts}</code>"
        body = f"<pre>{html.escape(ch)}</pre>"
        res = _post_telegram(token, chat_id, f"{header}\n{body}")
        if not res.get("ok"):
            ok_all = False
            sys.stderr.write(f"[TG_WARN] Failed to send chunk {idx}/{total}: {res}\n")
        elif total > 1 and idx < total:
            time.sleep(0.5)
    return ok_all


class TelegramBufferedStreamer:
    def __init__(self, tag: str, log_file: Path | None = None, flush_interval: float = 4.0):
        self.tag = tag
        self.log_file = log_file
        self.flush_interval = flush_interval
        self.lock = threading.Lock()
        self.buf: list[str] = []
        self.buf_chars = 0
        self.last_flush = time.monotonic()
        self.stop_event = threading.Event()
        ALL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.worker = threading.Thread(target=self._loop, daemon=True)
        self.worker.start()

    def push_line(self, line: str):
        clean = line.rstrip("\r\n")
        if not clean:
            return
        ts = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        stamped = f"[{ts}] [{self.tag}] {clean}"
        with open(ALL_LOG_PATH, "a", encoding="utf-8", errors="replace") as af:
            af.write(stamped + "\n")
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8", errors="replace") as lf:
                lf.write(stamped + "\n")
        with self.lock:
            self.buf.append(clean)
            self.buf_chars += len(clean) + 1
            should_flush = self.buf_chars >= 3000
        if should_flush:
            self.flush()

    def flush(self):
        with self.lock:
            if not self.buf:
                self.last_flush = time.monotonic()
                return
            batch = "\n".join(self.buf)
            self.buf.clear()
            self.buf_chars = 0
            self.last_flush = time.monotonic()
        send_telegram(batch, tag=self.tag)

    def _loop(self):
        while not self.stop_event.wait(1.0):
            with self.lock:
                due = bool(self.buf) and (time.monotonic() - self.last_flush >= self.flush_interval)
            if due:
                self.flush()

    def close(self):
        self.stop_event.set()
        self.worker.join(timeout=2.0)
        self.flush()


def run_wrapped(tag: str, cmd: list[str], extra_log: Path | None = None) -> int:
    env = os.environ.copy()
    env["BABYBEATS_TG_PARENT"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"

    streamer = TelegramBufferedStreamer(tag=tag, log_file=extra_log)
    streamer.push_line(f"START: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        bufsize=0
    )

    assert proc.stdout is not None
    partial = bytearray()
    last_cr_emit = 0.0
    saw_cr = False
    while True:
        chunk = proc.stdout.read(256)
        if not chunk:
            break
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
        for b in chunk:
            if saw_cr:
                saw_cr = False
                if b == 10:  # Windows CRLF (\r\n) -> emit full normal line
                    txt = partial.decode("utf-8", errors="replace")
                    partial.clear()
                    streamer.push_line(txt)
                    continue
                # Standalone \r progress overwrite
                txt = partial.decode("utf-8", errors="replace").strip()
                partial.clear()
                now = time.monotonic()
                if txt and (now - last_cr_emit >= 2.0 or "frames" in txt or "100%" in txt):
                    streamer.push_line(txt)
                    last_cr_emit = now
            if b == 10:  # LF (\n)
                txt = partial.decode("utf-8", errors="replace")
                partial.clear()
                streamer.push_line(txt)
            elif b == 13:  # CR (\r) - wait for next byte to distinguish CRLF vs CR overwrite
                saw_cr = True
            else:
                partial.append(b)
    if partial:
        streamer.push_line(partial.decode("utf-8", errors="replace"))

    rc = proc.wait()
    streamer.push_line(f"EXIT CODE={rc}: {' '.join(cmd)}")
    streamer.close()
    return rc


def wrap_if_top_level(tag: str, script_file: str, argv: list[str]):
    if os.environ.get("BABYBEATS_TG_PARENT") == "1":
        return
    rc = run_wrapped(tag, [sys.executable, "-u", script_file, *argv])
    raise SystemExit(rc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="BABYBEATS")
    ap.add_argument("--message", help="Send a single log message immediately")
    ap.add_argument("--log-file", help="Optional mirror log file path")
    ap.add_argument("--run", action="store_true", help="Run command after '--' and stream all logs to Telegram")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    if args.message:
        ok = send_telegram(args.message, tag=args.tag)
        print("TG_OK" if ok else "TG_FAILED")
        return 0 if ok else 1

    if args.run:
        cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
        if not cmd:
            raise SystemExit("No command given after --run")
        extra = Path(args.log_file) if args.log_file else None
        return run_wrapped(args.tag, cmd, extra_log=extra)

    stdin_text = sys.stdin.read()
    if stdin_text.strip():
        ok = send_telegram(stdin_text, tag=args.tag)
        print("TG_OK" if ok else "TG_FAILED")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
