from ai_pr_review.github.client import GITHUB_API_BASE, GitHubClient


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
