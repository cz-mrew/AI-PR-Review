import re
from urllib.parse import urlparse

from .models import FileChange, FileStatus, DiffHunk, DiffLine, GitHubPRUrl

HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")

SKIP_EXTENSIONS = {
    ".lock", ".sum", ".jar", ".war", ".ear", ".zip", ".tar", ".gz",
    ".bz2", ".xz", ".7z", ".rar", ".png", ".jpg", ".jpeg", ".gif",
    ".bmp", ".ico", ".svg", ".pdf", ".mp3", ".mp4", ".mov", ".avi",
    ".woff", ".woff2", ".ttf", ".eot", ".otf", ".min.js", ".min.css",
    ".pyc", ".class", ".o", ".so", ".dll", ".exe", ".bin",
}


def parse_github_pr_url(pr_url: str) -> GitHubPRUrl:
    parsed = urlparse(pr_url.strip())
    path_parts = [part for part in parsed.path.split("/") if part]

    if (
        parsed.scheme not in {"http", "https"}
        or parsed.netloc.lower() != "github.com"
        or len(path_parts) != 4
        or path_parts[2] != "pull"
    ):
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")

    try:
        pull_number = int(path_parts[3])
    except ValueError as exc:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}") from exc

    return GitHubPRUrl(
        owner=path_parts[0],
        repo=path_parts[1],
        pull_number=pull_number,
    )


def is_binary_or_skip(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    return f".{ext}".lower() in SKIP_EXTENSIONS or filename.lower().endswith(tuple(SKIP_EXTENSIONS))


def parse_diff(filename: str, patch: str) -> list[DiffHunk]:
    if not patch:
        return []
    lines = patch.split("\n")
    hunks: list[DiffHunk] = []
    current_hunk: DiffHunk | None = None
    old_lineno = 0
    new_lineno = 0

    for line in lines:
        m = HUNK_HEADER_RE.match(line)
        if m:
            if current_hunk:
                hunks.append(current_hunk)
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) else 1
            new_start = int(m.group(3))
            new_count = int(m.group(4)) if m.group(4) else 1
            current_hunk = DiffHunk(
                header=line,
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
            )
            old_lineno = old_start
            new_lineno = new_start
            continue

        if current_hunk is None:
            continue

        if line.startswith(" "):
            current_hunk.lines.append(DiffLine(type="context", content=line[1:], old_lineno=old_lineno, new_lineno=new_lineno))
            old_lineno += 1
            new_lineno += 1
        elif line.startswith("-"):
            current_hunk.lines.append(DiffLine(type="remove", content=line[1:], old_lineno=old_lineno, new_lineno=None))
            old_lineno += 1
        elif line.startswith("+"):
            current_hunk.lines.append(DiffLine(type="add", content=line[1:], old_lineno=None, new_lineno=new_lineno))
            new_lineno += 1
        elif line.startswith("\\"):
            pass

    if current_hunk:
        hunks.append(current_hunk)
    return hunks


def parse_file_change(filename: str, status: str, additions: int, deletions: int, changes: int, patch: str | None) -> FileChange:
    file_status = FileStatus(status)
    patch_text = patch or ""
    return FileChange(
        filename=filename,
        status=file_status,
        additions=additions,
        deletions=deletions,
        changes=changes,
        patch=patch_text,
        hunks=parse_diff(filename, patch_text),
        is_binary=is_binary_or_skip(filename) or not patch_text,
    )
