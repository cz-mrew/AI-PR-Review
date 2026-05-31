from ai_pr_review.github.client import GITHUB_API_BASE, GitHubClient
from ai_pr_review.github.models import GitHubChangedFile, GitHubCommit, GitHubPullRequest, GitHubUser


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.raised = False

    def raise_for_status(self):
        self.raised = True

    def json(self):
        return self._payload


class FakeHttpxClient:
    calls = []
    payload = {"ok": True}

    def __init__(self, timeout):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def get(self, url, headers, params=None):
        self.calls.append({
            "url": url,
            "headers": headers,
            "params": params,
            "timeout": self.timeout,
        })
        return FakeResponse(self.payload)


def test_get_builds_github_api_path(monkeypatch):
    FakeHttpxClient.calls = []
    monkeypatch.setattr("ai_pr_review.github.client.httpx.Client", FakeHttpxClient)

    client = GitHubClient(github_token="")
    result = client._get("/repos/owner/repo", params={"state": "open"})

    assert result == {"ok": True}
    assert FakeHttpxClient.calls[0]["url"] == f"{GITHUB_API_BASE}/repos/owner/repo"
    assert FakeHttpxClient.calls[0]["params"] == {"state": "open"}


def test_get_request_headers_include_accept(monkeypatch):
    FakeHttpxClient.calls = []
    monkeypatch.setattr("ai_pr_review.github.client.httpx.Client", FakeHttpxClient)

    client = GitHubClient(github_token="")
    client._get("repos/owner/repo")

    assert FakeHttpxClient.calls[0]["headers"]["Accept"] == "application/vnd.github+json"


def test_get_request_headers_include_authorization_with_token(monkeypatch):
    FakeHttpxClient.calls = []
    monkeypatch.setattr("ai_pr_review.github.client.httpx.Client", FakeHttpxClient)

    client = GitHubClient(github_token="test-token")
    client._get("repos/owner/repo")

    assert FakeHttpxClient.calls[0]["headers"]["Authorization"] == "Bearer test-token"


def test_get_without_token_does_not_raise_or_send_authorization(monkeypatch):
    FakeHttpxClient.calls = []
    monkeypatch.setattr("ai_pr_review.github.client.httpx.Client", FakeHttpxClient)

    client = GitHubClient(github_token="")
    result = client._get("repos/owner/repo")

    assert result == {"ok": True}
    assert "Authorization" not in FakeHttpxClient.calls[0]["headers"]


def test_get_pull_request_returns_mapped_model(monkeypatch):
    calls = []
    mock_pr_json = {
        "number": 123,
        "title": "Add GitHub PR support",
        "body": "Fetches pull request metadata.",
        "state": "open",
        "html_url": "https://github.com/owner/repo/pull/123",
        "user": {
            "login": "octocat",
            "html_url": "https://github.com/octocat",
        },
        "base": {
            "ref": "main",
        },
        "head": {
            "ref": "feature/pr-support",
            "sha": "abc123",
        },
        "created_at": "2026-05-30T00:00:00Z",
        "updated_at": "2026-05-30T01:00:00Z",
    }

    def fake_get(self, path, params=None):
        calls.append({"path": path, "params": params})
        return mock_pr_json

    monkeypatch.setattr(GitHubClient, "_get", fake_get)

    client = GitHubClient(github_token="")
    pull_request = client.get_pull_request("owner", "repo", 123)

    assert calls == [{"path": "repos/owner/repo/pulls/123", "params": None}]
    assert isinstance(pull_request, GitHubPullRequest)
    assert pull_request.number == 123
    assert pull_request.title == "Add GitHub PR support"
    assert pull_request.body == "Fetches pull request metadata."
    assert pull_request.state == "open"
    assert pull_request.html_url == "https://github.com/owner/repo/pull/123"
    assert isinstance(pull_request.user, GitHubUser)
    assert pull_request.user.login == "octocat"
    assert pull_request.user.html_url == "https://github.com/octocat"
    assert pull_request.base_branch == "main"
    assert pull_request.head_branch == "feature/pr-support"
    assert pull_request.head_sha == "abc123"
    assert pull_request.created_at == "2026-05-30T00:00:00Z"
    assert pull_request.updated_at == "2026-05-30T01:00:00Z"


def test_get_pull_request_files_returns_changed_file_models(monkeypatch):
    calls = []
    mock_files_json = [
        {
            "filename": "src/app.py",
            "status": "modified",
            "additions": 12,
            "deletions": 3,
            "changes": 15,
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
            "raw_url": "https://github.com/owner/repo/raw/main/src/app.py",
            "blob_url": "https://github.com/owner/repo/blob/main/src/app.py",
        },
        {
            "filename": "assets/logo.png",
            "status": "added",
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "raw_url": "https://github.com/owner/repo/raw/main/assets/logo.png",
            "blob_url": "https://github.com/owner/repo/blob/main/assets/logo.png",
        },
    ]

    def fake_get(self, path, params=None):
        calls.append({"path": path, "params": params})
        return mock_files_json

    monkeypatch.setattr(GitHubClient, "_get", fake_get)

    client = GitHubClient(github_token="")
    files = client.get_pull_request_files("owner", "repo", 123)

    assert calls == [{
        "path": "repos/owner/repo/pulls/123/files",
        "params": {"per_page": 100, "page": 1},
    }]
    assert len(files) == 2
    assert all(isinstance(file, GitHubChangedFile) for file in files)

    assert files[0].filename == "src/app.py"
    assert files[0].status == "modified"
    assert files[0].additions == 12
    assert files[0].deletions == 3
    assert files[0].changes == 15
    assert files[0].patch == "@@ -1,1 +1,1 @@\n-old\n+new"
    assert files[0].raw_url == "https://github.com/owner/repo/raw/main/src/app.py"
    assert files[0].blob_url == "https://github.com/owner/repo/blob/main/src/app.py"

    assert files[1].filename == "assets/logo.png"
    assert files[1].patch is None


def test_get_pull_request_files_fetches_all_pages(monkeypatch):
    calls = []
    first_page = [
        {
            "filename": f"src/file_{index}.py",
            "status": "modified",
            "additions": index,
            "deletions": 0,
            "changes": index,
            "patch": None,
            "raw_url": f"https://github.com/owner/repo/raw/main/src/file_{index}.py",
            "blob_url": f"https://github.com/owner/repo/blob/main/src/file_{index}.py",
        }
        for index in range(100)
    ]
    second_page = [
        {
            "filename": f"tests/test_file_{index}.py",
            "status": "added",
            "additions": index,
            "deletions": 0,
            "changes": index,
            "patch": None,
            "raw_url": f"https://github.com/owner/repo/raw/main/tests/test_file_{index}.py",
            "blob_url": f"https://github.com/owner/repo/blob/main/tests/test_file_{index}.py",
        }
        for index in range(20)
    ]

    def fake_get(self, path, params=None):
        calls.append({"path": path, "params": params})
        if params["page"] == 1:
            return first_page
        if params["page"] == 2:
            return second_page
        return []

    monkeypatch.setattr(GitHubClient, "_get", fake_get)

    client = GitHubClient(github_token="")
    files = client.get_pull_request_files("owner", "repo", 123)

    assert len(files) == 120
    assert calls == [
        {
            "path": "repos/owner/repo/pulls/123/files",
            "params": {"per_page": 100, "page": 1},
        },
        {
            "path": "repos/owner/repo/pulls/123/files",
            "params": {"per_page": 100, "page": 2},
        },
    ]
    assert files[0].filename == "src/file_0.py"
    assert files[99].filename == "src/file_99.py"
    assert files[100].filename == "tests/test_file_0.py"
    assert files[119].filename == "tests/test_file_19.py"


def test_get_pull_request_commits_returns_commit_models(monkeypatch):
    calls = []
    mock_commits_json = [
        {
            "sha": "abc123",
            "commit": {
                "message": "Add review API models",
                "author": {
                    "name": "Alice",
                    "email": "alice@example.com",
                },
            },
        },
        {
            "sha": "def456",
            "commit": {
                "message": "Add commit tests",
                "author": {
                    "name": "Bob",
                    "email": "bob@example.com",
                },
            },
        },
    ]

    def fake_get(self, path, params=None):
        calls.append({"path": path, "params": params})
        return mock_commits_json

    monkeypatch.setattr(GitHubClient, "_get", fake_get)

    client = GitHubClient(github_token="")
    commits = client.get_pull_request_commits("owner", "repo", 123)

    assert calls == [{"path": "repos/owner/repo/pulls/123/commits", "params": None}]
    assert len(commits) == 2
    assert all(isinstance(commit, GitHubCommit) for commit in commits)

    assert commits[0].sha == "abc123"
    assert commits[0].message == "Add review API models"
    assert commits[0].author_name == "Alice"
    assert commits[0].author_email == "alice@example.com"

    assert commits[1].sha == "def456"
    assert commits[1].message == "Add commit tests"
    assert commits[1].author_name == "Bob"
    assert commits[1].author_email == "bob@example.com"
