"""
GitHub REST / Git Data API state synchronization for stateless cloud hosts (Render, Koyeb, etc.).
Pulls the latest queue/tracker state before a cloud run and commits changed state, SEO,
and dashboard files back to GitHub in one atomic `[skip ci]` commit.
"""
import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from repo_paths import AUTO_DIR, ROOT_DIR, to_repo_posix

DEFAULT_REPO = "akshayxt/Faceless-Shorts"
DEFAULT_BRANCH = "main"

PULL_PATHS = (
    "automation/data/upload_queue.json",
    "automation/data/30day_topic_queue.json",
    "automation/data/growth_tracker.json",
    "automation/data/bot_settings.json",
    "automation/data/agent_inbox.json",
)


def _gh_cfg() -> tuple[str, str, str]:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip() or DEFAULT_REPO
    branch = os.environ.get("GITHUB_BRANCH", "").strip() or os.environ.get("GITHUB_REF_NAME", "").strip() or DEFAULT_BRANCH
    return token, repo, branch


def _gh_request(method: str, path: str, token: str, payload: dict | None = None, accept: str = "application/vnd.github+json"):
    url = f"https://api.github.com{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "BabyBeatsCloudServer/1.0",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        if accept == "application/vnd.github.raw+json":
            return raw
        txt = raw.decode("utf-8", errors="replace")
        return json.loads(txt) if txt.strip() else {}


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def pull_state_files() -> dict:
    """Pull latest state JSON files from GitHub main so stateless hosts never replay uploaded videos."""
    token, repo, branch = _gh_cfg()
    if not token:
        return {"pulled": [], "skipped": "missing GITHUB_TOKEN"}

    pulled: list[str] = []
    for rel in PULL_PATHS:
        try:
            raw = _gh_request("GET", f"/repos/{repo}/contents/{rel}?ref={branch}", token, accept="application/vnd.github.raw+json")
            target = ROOT_DIR / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != raw:
                target.write_bytes(raw)
                pulled.append(rel)
        except urllib.error.HTTPError as exc:
            print(f"GITHUB_PULL_WARN {rel}: HTTP {exc.code}", flush=True)
        except Exception as exc:
            print(f"GITHUB_PULL_WARN {rel}: {exc}", flush=True)
    return {"pulled": pulled}


def _candidate_sync_paths() -> list[Path]:
    paths: list[Path] = [
        AUTO_DIR / "data" / "upload_queue.json",
        AUTO_DIR / "data" / "30day_topic_queue.json",
        AUTO_DIR / "data" / "growth_tracker.json",
        AUTO_DIR / "data" / "bot_settings.json",
        AUTO_DIR / "data" / "agent_inbox.json",
        AUTO_DIR / "dashboard.html",
        AUTO_DIR / "growth_dashboard.md",
    ]
    videos_dir = ROOT_DIR / "videos"
    if videos_dir.exists():
        for pat in ("*/seo.txt", "*/*_seo.txt", "*/seo_package.json", "*/data/seo_package.json"):
            paths.extend(sorted(videos_dir.glob(pat)))
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in paths:
        if p.exists() and p.is_file() and p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def push_changed_files(commit_message: str = "chore(cloud-server): sync SEO, upload status & dashboards [skip render] [skip ci]") -> dict:
    """Create one atomic commit on GitHub for any modified state, SEO, or dashboard files."""
    token, repo, branch = _gh_cfg()
    if not token:
        return {"committed": False, "skipped": "missing GITHUB_TOKEN"}

    tree_resp = _gh_request("GET", f"/repos/{repo}/git/trees/{branch}?recursive=1", token)
    remote_shas = {
        entry["path"]: entry["sha"]
        for entry in tree_resp.get("tree", [])
        if entry.get("type") == "blob"
    }

    changed: list[tuple[str, bytes]] = []
    for path in _candidate_sync_paths():
        rel = to_repo_posix(path)
        raw = path.read_bytes()
        if remote_shas.get(rel) != _git_blob_sha(raw):
            changed.append((rel, raw))

    if not changed:
        return {"committed": False, "changed": 0}

    for attempt in range(2):
        ref_resp = _gh_request("GET", f"/repos/{repo}/git/ref/heads/{branch}", token)
        parent_sha = ref_resp["object"]["sha"]
        commit_resp = _gh_request("GET", f"/repos/{repo}/git/commits/{parent_sha}", token)
        base_tree = commit_resp["tree"]["sha"]

        tree_entries = []
        for rel, raw in changed:
            blob_resp = _gh_request(
                "POST",
                f"/repos/{repo}/git/blobs",
                token,
                {"content": base64.b64encode(raw).decode("ascii"), "encoding": "base64"},
            )
            tree_entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob_resp["sha"]})

        new_tree = _gh_request(
            "POST",
            f"/repos/{repo}/git/trees",
            token,
            {"base_tree": base_tree, "tree": tree_entries},
        )
        new_commit = _gh_request(
            "POST",
            f"/repos/{repo}/git/commits",
            token,
            {"message": commit_message, "tree": new_tree["sha"], "parents": [parent_sha]},
        )
        try:
            _gh_request(
                "PATCH",
                f"/repos/{repo}/git/refs/heads/{branch}",
                token,
                {"sha": new_commit["sha"], "force": False},
            )
            return {"committed": True, "sha": new_commit["sha"], "files": [rel for rel, _ in changed]}
        except urllib.error.HTTPError as exc:
            if exc.code == 422 and attempt == 0:
                continue
            raise
    return {"committed": False, "changed": len(changed)}
