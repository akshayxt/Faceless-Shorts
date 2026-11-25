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
    "automation/data/uploaded_videos_archive.json",
    "automation/data/30day_topic_queue.json",
    "automation/data/growth_tracker.json",
    "automation/data/bot_settings.json",
    "automation/data/agent_inbox.json",
    "automation/data/moderation_data.json",
    "automation/data/bot_audit_logs.json",
    "automation/data/chatdata.json",
    "automation/data/chat_sync_settings.json",
    "automation/data/make_config.json",
    "automation/dashboard.html",
    "automation/growth_dashboard.md",
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
    pulled: list[str] = []
    for rel in PULL_PATHS:
        try:
            raw = None
            if token:
                try:
                    raw = _gh_request("GET", f"/repos/{repo}/contents/{rel}?ref={branch}", token, accept="application/vnd.github.raw+json")
                except Exception:
                    raw = None
            if raw is None:
                url = f"https://raw.githubusercontent.com/{repo}/{branch}/{rel}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw = resp.read()
            target = ROOT_DIR / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != raw:
                target.write_bytes(raw)
                pulled.append(rel)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                print(f"GITHUB_PULL_WARN {rel}: HTTP {exc.code}", flush=True)
        except Exception as exc:
            print(f"GITHUB_PULL_WARN {rel}: {exc}", flush=True)
    return {"pulled": pulled}


def _merge_remote_upload_queue(repo: str, branch: str, token: str, uq_path: Path) -> None:
    """Merge remote upload_queue.json into local file so no videos are ever accidentally removed."""
    try:
        raw_remote = None
        if token:
            try:
                raw_remote = _gh_request("GET", f"/repos/{repo}/contents/automation/data/upload_queue.json?ref={branch}", token, accept="application/vnd.github.raw+json")
            except Exception:
                pass
        if not raw_remote:
            url = f"https://raw.githubusercontent.com/{repo}/{branch}/automation/data/upload_queue.json"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw_remote = resp.read()
        remote_data = json.loads(raw_remote.decode("utf-8"))
        local_data = json.loads(uq_path.read_text(encoding="utf-8"))

        merged = {x["id"]: x for x in remote_data.get("items", [])}
        for it in local_data.get("items", []):
            iid = it.get("id")
            if iid in merged:
                if it.get("status") in ("UPLOADED", "SCHEDULED", "UPLOADED_PRIVATE") or it.get("youtube_video_id"):
                    merged[iid] = it
            else:
                merged[iid] = it

        items_sorted = sorted(merged.values(), key=lambda x: x.get("scheduled_publish_est") or x.get("scheduled_time") or "")
        local_data["items"] = items_sorted
        uq_path.write_text(json.dumps(local_data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        print(f"MERGE_REMOTE_UQ_WARN: {exc}", flush=True)


def _candidate_sync_paths() -> list[Path]:
    paths: list[Path] = [
        AUTO_DIR / "data" / "upload_queue.json",
        AUTO_DIR / "data" / "uploaded_videos_archive.json",
        AUTO_DIR / "data" / "30day_topic_queue.json",
        AUTO_DIR / "data" / "growth_tracker.json",
        AUTO_DIR / "data" / "bot_settings.json",
        AUTO_DIR / "data" / "agent_inbox.json",
        AUTO_DIR / "data" / "moderation_data.json",
        AUTO_DIR / "data" / "bot_audit_logs.json",
        AUTO_DIR / "data" / "chatdata.json",
        AUTO_DIR / "data" / "chat_sync_settings.json",
        AUTO_DIR / "data" / "make_config.json",
        AUTO_DIR / "dashboard.html",
        AUTO_DIR / "growth_dashboard.md",
    ]
    chat_logs_dir = AUTO_DIR / "data" / "chat_logs"
    if chat_logs_dir.exists():
        paths.extend(sorted(chat_logs_dir.glob("*.json")))
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


def push_changed_files(
    commit_message: str = "chore(cloud-server): sync SEO, upload status & dashboards [skip render] [skip ci]",
    candidate_paths: list[Path] | None = None,
) -> dict:
    """Create one atomic commit on GitHub for any modified state, SEO, or dashboard files."""
    token, repo, branch = _gh_cfg()
    if not token:
        return {"committed": False, "skipped": "missing GITHUB_TOKEN"}

    uq_path = AUTO_DIR / "data" / "upload_queue.json"
    effective_paths = candidate_paths if candidate_paths is not None else _candidate_sync_paths()
    if uq_path in effective_paths and uq_path.exists():
        _merge_remote_upload_queue(repo, branch, token, uq_path)

    tree_resp = _gh_request("GET", f"/repos/{repo}/git/trees/{branch}?recursive=1", token)
    remote_shas = {
        entry["path"]: entry["sha"]
        for entry in tree_resp.get("tree", [])
        if entry.get("type") == "blob"
    }

    changed: list[tuple[str, bytes]] = []
    for path in effective_paths:
        if not (path.exists() and path.is_file()):
            continue
        rel = to_repo_posix(path)
        raw = path.read_bytes()
        if remote_shas.get(rel) != _git_blob_sha(raw):
            changed.append((rel, raw))

    # Automatically purge uploaded video projects and media files from remote GitHub repository tree
    to_delete_remote: list[str] = []
    uq_path = AUTO_DIR / "data" / "upload_queue.json"
    if uq_path.exists():
        try:
            from auto_clean_archive import archive_and_clean_all
            archive_and_clean_all(remove_from_disk=False, git_rm=False)
            uq = json.loads(uq_path.read_text(encoding="utf-8"))
            for it in uq.get("items", []):
                if it.get("status") in ("UPLOADED", "SCHEDULED", "UPLOADED_PRIVATE") or it.get("youtube_video_id"):
                    iid = it.get("id")
                    prefix = f"videos/{iid}/"
                    for remote_path in remote_shas:
                        if remote_path.startswith(prefix):
                            to_delete_remote.append(remote_path)
        except Exception as exc:
            print(f"GITHUB_SYNC_PRUNE_WARN: {exc}", flush=True)

    if not changed and not to_delete_remote:
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

        for rel_del in to_delete_remote:
            tree_entries.append({"path": rel_del, "mode": "100644", "type": "blob", "sha": None})

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
