"""
Cross-platform repository path resolution and GitHub CDN URL helpers.
Ensures automation scripts work identically on local Windows and Linux GitHub Actions runners.
"""
import os
import re
from pathlib import Path

AUTO_DIR = Path(__file__).resolve().parent
ROOT_DIR = AUTO_DIR.parent
IST_OFFSET_HOURS = 5
IST_OFFSET_MINUTES = 30

_WIN_PREFIX_RE = re.compile(r"^[A-Za-z]:/Faceless-Shorts/(.*)$", flags=re.IGNORECASE)
_GH_PREFIX_RE = re.compile(r"^/home/runner/work/[^/]+/[^/]+/(.*)$")


def resolve_repo_path(raw: str | Path) -> Path:
    """Resolve stored Windows/Linux/relative paths cleanly against the active repo checkout."""
    raw_str = str(raw or "").strip()
    if not raw_str:
        return ROOT_DIR
    norm = raw_str.replace("\\", "/")
    m_win = _WIN_PREFIX_RE.match(norm)
    if m_win:
        return ROOT_DIR / m_win.group(1)
    m_gh = _GH_PREFIX_RE.match(norm)
    if m_gh:
        return ROOT_DIR / m_gh.group(1)
    p = Path(raw_str)
    if p.is_absolute():
        return p
    return ROOT_DIR / norm.lstrip("/")


def to_repo_posix(raw: str | Path) -> str:
    """Return a clean repo-relative POSIX path when inside ROOT_DIR."""
    p = resolve_repo_path(raw)
    try:
        return p.resolve().relative_to(ROOT_DIR.resolve()).as_posix()
    except Exception:
        return p.as_posix()


def to_raw_github_url(
    raw: str | Path,
    repo: str | None = None,
    branch: str | None = None,
) -> str:
    """Build a permanent HTTPS raw.githubusercontent.com URL for a committed asset."""
    gh_repo = repo or os.environ.get("GITHUB_REPOSITORY") or "akshayxt/Faceless-Shorts"
    gh_branch = branch or os.environ.get("GITHUB_REF_NAME") or "main"
    rel = to_repo_posix(raw).lstrip("/")
    return f"https://raw.githubusercontent.com/{gh_repo}/{gh_branch}/{rel}"
