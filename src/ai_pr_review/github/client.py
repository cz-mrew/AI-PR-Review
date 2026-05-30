import os
import re
import httpx
from .models import PRInfo, FileChange
from .parser import parse_file_change, parse_github_pr_url

GITHUB_API_BASE = "https://api.github.com"

SKIP_PATTERNS = [
    r"^vendor/",
    r"/vendor/",
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"pnpm-lock\.yaml$",
    r"\.lock$",
    r"\.sum$",
    r"\.min\.js$",
    r"\.min\.css$",
    r"\.map$",
]


class GitHubClient:
    def __init__(self, token: str | None = None):
        self._token = token or os.environ.get("GITHUB_TOKEN", "")
        self._headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ai-pr-review",
        }
        if self._token:
            self._headers["Authorization"] = f"Bearer {self._token}"

    @staticmethod
    def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
        parsed = parse_github_pr_url(pr_url)
        return parsed.owner, parsed.repo, parsed.pull_number

    def fetch_pr(self, pr_url: str) -> PRInfo:
        owner, repo, number = self.parse_pr_url(pr_url)
        with httpx.Client(timeout=30) as client:
            pr_resp = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}",
                headers=self._headers,
            )
            pr_resp.raise_for_status()
            pr_data = pr_resp.json()

            files_resp = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}/files",
                headers=self._headers,
            )
            files_resp.raise_for_status()
            files_data = files_resp.json()

        return PRInfo(
            title=pr_data.get("title", ""),
            author=pr_data.get("user", {}).get("login", "unknown"),
            head_sha=pr_data.get("head", {}).get("sha", ""),
            base_sha=pr_data.get("base", {}).get("sha", ""),
            files_changed=pr_data.get("changed_files", 0),
            additions=pr_data.get("additions", 0),
            deletions=pr_data.get("deletions", 0),
            description=pr_data.get("body", "") or "",
            repo_owner=owner,
            repo_name=repo,
            pr_number=number,
            files=self._parse_files(files_data),
        )

    def _parse_files(self, files_data: list[dict]) -> list[FileChange]:
        result: list[FileChange] = []
        for f in files_data:
            filename = f.get("filename", "")
            if self._should_skip(filename):
                continue
            result.append(parse_file_change(
                filename=filename,
                status=f.get("status", "modified"),
                additions=f.get("additions", 0),
                deletions=f.get("deletions", 0),
                changes=f.get("changes", 0),
                patch=f.get("patch"),
            ))
        return result

    @staticmethod
    def _should_skip(filename: str) -> bool:
        for pattern in SKIP_PATTERNS:
            if re.search(pattern, filename):
                return True
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        skip_exts = {"lock", "sum", "jar", "war", "zip", "tar", "gz", "bz2", "xz",
                     "7z", "rar", "png", "jpg", "jpeg", "gif", "bmp", "ico", "pdf",
                     "mp3", "mp4", "mov", "avi", "woff", "woff2", "ttf", "eot",
                     "otf", "pyc", "class", "o", "so", "dll", "exe", "bin"}
        return ext in skip_exts
