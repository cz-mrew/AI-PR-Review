import os
import re
import httpx

from .models import (
    FileChange,
    GitHubChangedFile,
    GitHubCommit,
    GitHubPullRequest,
    GitHubUser,
    PRInfo,
)
from .parser import parse_file_change, parse_github_pr_url

GITHUB_API_BASE = "https://api.github.com"
GITHUB_PER_PAGE = 100
GITHUB_MAX_PAGES = 100

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
    def __init__(self, github_token: str | None = None, token: str | None = None):
        self._token = github_token if github_token is not None else token
        if self._token is None:
            self._token = os.environ.get("GITHUB_TOKEN", "")
        self._headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-pr-review",
        }
        if self._token:
            self._headers["Authorization"] = f"Bearer {self._token}"

    @staticmethod
    def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
        parsed = parse_github_pr_url(pr_url)
        return parsed.owner, parsed.repo, parsed.pull_number

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        url = f"{GITHUB_API_BASE}/{path.lstrip('/')}"
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()

    def _post(self, path: str, json: dict | None = None) -> dict | list:
        url = f"{GITHUB_API_BASE}/{path.lstrip('/')}"
        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=self._headers, json=json)
            response.raise_for_status()
            return response.json()

    def get_pull_request(self, owner: str, repo: str, pull_number: int) -> GitHubPullRequest:
        pr_data = self._get(f"repos/{owner}/{repo}/pulls/{pull_number}")

        user_data = pr_data.get("user") or {}
        base_data = pr_data.get("base") or {}
        head_data = pr_data.get("head") or {}

        return GitHubPullRequest(
            number=pr_data.get("number", pull_number),
            title=pr_data.get("title", ""),
            body=pr_data.get("body"),
            state=pr_data.get("state", ""),
            html_url=pr_data.get("html_url", ""),
            user=GitHubUser(
                login=user_data.get("login", ""),
                html_url=user_data.get("html_url", ""),
            ),
            base_branch=base_data.get("ref", ""),
            head_branch=head_data.get("ref", ""),
            head_sha=head_data.get("sha", ""),
            created_at=pr_data.get("created_at", ""),
            updated_at=pr_data.get("updated_at", ""),
        )

    def get_pull_request_files(self, owner: str, repo: str, pull_number: int) -> list[GitHubChangedFile]:
        path = f"repos/{owner}/{repo}/pulls/{pull_number}/files"
        files: list[GitHubChangedFile] = []

        for page in range(1, GITHUB_MAX_PAGES + 1):
            page_data = self._get(path, params={"per_page": GITHUB_PER_PAGE, "page": page})
            files.extend(self._map_changed_file(file_data) for file_data in page_data)

            if len(page_data) < GITHUB_PER_PAGE:
                break

        return files

    @staticmethod
    def _map_changed_file(file_data: dict) -> GitHubChangedFile:
        return GitHubChangedFile(
            filename=file_data.get("filename", ""),
            status=file_data.get("status", ""),
            additions=file_data.get("additions", 0),
            deletions=file_data.get("deletions", 0),
            changes=file_data.get("changes", 0),
            patch=file_data.get("patch"),
            raw_url=file_data.get("raw_url", ""),
            blob_url=file_data.get("blob_url", ""),
        )

    def get_pull_request_commits(self, owner: str, repo: str, pull_number: int) -> list[GitHubCommit]:
        commits_data = self._get(f"repos/{owner}/{repo}/pulls/{pull_number}/commits")

        return [
            GitHubCommit(
                sha=commit_data.get("sha", ""),
                message=(commit_data.get("commit") or {}).get("message", ""),
                author_name=((commit_data.get("commit") or {}).get("author") or {}).get("name", ""),
                author_email=((commit_data.get("commit") or {}).get("author") or {}).get("email", ""),
            )
            for commit_data in commits_data
        ]

    def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        result = self._post(
            f"repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )
        return result if isinstance(result, dict) else {"comments": result}

    def fetch_pr(self, pr_url: str) -> PRInfo:
        owner, repo, number = self.parse_pr_url(pr_url)
        pr_data = self._get(f"repos/{owner}/{repo}/pulls/{number}")
        files_data = self._get(f"repos/{owner}/{repo}/pulls/{number}/files")

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
