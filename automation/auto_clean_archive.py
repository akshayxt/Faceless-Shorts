"""
Automated Uploaded Video Cleaner & Archive Manager.

Automatically archives uploaded videos metadata (file_name, uploaded_date, publish_date)
and purges the uploaded video projects and media from GitHub and disk so the repository
remains lightweight and never stores videos that are already safely hosted on YouTube.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from repo_paths import AUTO_DIR, ROOT_DIR, resolve_repo_path

UPLOAD_Q_PATH = AUTO_DIR / "data" / "upload_queue.json"
ARCHIVE_PATH = AUTO_DIR / "data" / "uploaded_videos_archive.json"
IST = timezone(timedelta(hours=5, minutes=30))


def load_archive() -> dict:
    if ARCHIVE_PATH.exists():
        try:
            return json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_updated_ist": None, "total_archived": 0, "videos": []}


def save_archive(data: dict) -> None:
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def is_item_uploaded(it: dict) -> bool:
    status = (it.get("status") or "").upper()
    return status in ("UPLOADED", "SCHEDULED", "UPLOADED_PRIVATE") or bool(it.get("youtube_video_id"))


def archive_and_clean_all(remove_from_disk: bool = True, git_rm: bool = True) -> dict:
    """
    Find all uploaded videos in upload_queue.json:
    1. Save their file_name, uploaded_date, and publish_date to uploaded_videos_archive.json.
    2. Delete the video folders from Git and disk so GitHub doesn't store uploaded videos.
    """
    if not UPLOAD_Q_PATH.exists():
        return {"archived": 0, "deleted_folders": []}

    try:
        uq = json.loads(UPLOAD_Q_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"AUTO_CLEAN_ERROR: Failed to read {UPLOAD_Q_PATH}: {exc}", flush=True)
        return {"archived": 0, "deleted_folders": []}

    items = uq.get("items", [])
    archive = load_archive()
    archived_list = archive.setdefault("videos", [])
    archived_by_id = {v["id"]: v for v in archived_list}

    uploaded_items = [it for it in items if is_item_uploaded(it)]
    newly_archived = []
    folders_to_delete = []

    for it in uploaded_items:
        iid = it.get("id")
        if not iid:
            continue

        raw_path = it.get("video_path") or f"videos/{iid}/renders/{iid}.mp4"
        file_name = Path(raw_path).name or f"{iid}.mp4"

        uploaded_date = (
            it.get("uploaded_at_ist")
            or it.get("updated_at_ist")
            or datetime.now(IST).isoformat()
        )
        publish_date = (
            it.get("publish_at")
            or it.get("scheduled_publish_est")
            or it.get("scheduled_publish_ist")
            or "N/A"
        )

        entry = {
            "id": iid,
            "file_name": file_name,
            "title": it.get("title", ""),
            "youtube_video_id": it.get("youtube_video_id"),
            "uploaded_date": uploaded_date,
            "publish_date": publish_date,
            "format": it.get("format", "short"),
            "archived_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        }

        if iid in archived_by_id:
            archived_by_id[iid].update(entry)
        else:
            archived_list.append(entry)
            archived_by_id[iid] = entry
            newly_archived.append(iid)

        vdir = ROOT_DIR / "videos" / iid
        if vdir.exists():
            folders_to_delete.append(iid)

    archive["last_updated_ist"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    archive["total_archived"] = len(archived_list)
    save_archive(archive)
    print(f"ARCHIVE_UPDATED: {len(archived_list)} total uploaded videos archived in {ARCHIVE_PATH.name}")

    # Remove from Git and disk
    deleted_folders = []
    for iid in folders_to_delete:
        vdir = ROOT_DIR / "videos" / iid
        rel_posix = f"videos/{iid}"

        if git_rm:
            try:
                subprocess.run(
                    ["git", "rm", "-r", "-f", "--ignore-unmatch", rel_posix],
                    cwd=str(ROOT_DIR),
                    capture_output=True,
                    text=True,
                    check=False
                )
            except Exception as exc:
                print(f"GIT_RM_WARN {iid}: {exc}", flush=True)

        if remove_from_disk and vdir.exists():
            try:
                shutil.rmtree(vdir, ignore_errors=True)
                deleted_folders.append(iid)
                print(f"DELETED_FROM_REPO: {rel_posix} removed successfully.")
            except Exception as exc:
                print(f"RM_DISK_WARN {iid}: {exc}", flush=True)

    return {
        "total_archived": len(archived_list),
        "newly_archived": len(newly_archived),
        "deleted_folders": deleted_folders
    }


def archive_single_item(item_id: str) -> None:
    """Archive a single video item right after it is uploaded."""
    if not UPLOAD_Q_PATH.exists():
        return
    try:
        uq = json.loads(UPLOAD_Q_PATH.read_text(encoding="utf-8"))
        item = next((it for it in uq.get("items", []) if it.get("id") == item_id), None)
        if not item:
            return
        
        archive = load_archive()
        archived_list = archive.setdefault("videos", [])
        archived_by_id = {v["id"]: v for v in archived_list}

        raw_path = item.get("video_path") or f"videos/{item_id}/renders/{item_id}.mp4"
        file_name = Path(raw_path).name or f"{item_id}.mp4"

        entry = {
            "id": item_id,
            "file_name": file_name,
            "title": item.get("title", ""),
            "youtube_video_id": item.get("youtube_video_id"),
            "uploaded_date": item.get("uploaded_at_ist") or datetime.now(IST).isoformat(),
            "publish_date": item.get("publish_at") or item.get("scheduled_publish_est") or "N/A",
            "format": item.get("format", "short"),
            "archived_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        }

        if item_id in archived_by_id:
            archived_by_id[item_id].update(entry)
        else:
            archived_list.append(entry)

        archive["last_updated_ist"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        archive["total_archived"] = len(archived_list)
        save_archive(archive)

        # Delete project folder
        vdir = ROOT_DIR / "videos" / item_id
        rel_posix = f"videos/{item_id}"
        subprocess.run(
            ["git", "rm", "-r", "-f", "--ignore-unmatch", rel_posix],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            check=False
        )
        if vdir.exists():
            shutil.rmtree(vdir, ignore_errors=True)
        print(f"ARCHIVED_AND_PURGED: {item_id} (only metadata retained in {ARCHIVE_PATH.name})", flush=True)
    except Exception as exc:
        print(f"ARCHIVE_SINGLE_WARN {item_id}: {exc}", flush=True)


if __name__ == "__main__":
    res = archive_and_clean_all()
    print("RESULT:", json.dumps(res, indent=2))
