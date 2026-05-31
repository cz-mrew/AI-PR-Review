from fastapi.testclient import TestClient

from ai_pr_review.exceptions import GitHubAPIError, InvalidPRUrlError
from main import create_app


class InvalidUrlReviewService:
    def review(self, pr_url: str) -> dict:
        raise InvalidPRUrlError(f"Unsupported PR URL: {pr_url}")


class GitHubErrorReviewService:
    def review(self, pr_url: str) -> dict:
        raise GitHubAPIError("GitHub request failed with status 500")


def test_review_api_returns_structured_error_for_invalid_pr_url(monkeypatch):
    monkeypatch.setattr("ai_pr_review.api.review.ReviewService", InvalidUrlReviewService)
    client = TestClient(create_app())

    response = client.post("/api/review", json={"pr_url": "not-a-pr-url"})

    assert response.status_code == 400
    body = response.json()
    assert body == {
        "success": False,
        "message": "Invalid GitHub PR URL",
        "data": None,
        "error": {
            "code": "INVALID_PR_URL",
            "detail": "Unsupported PR URL: not-a-pr-url",
        },
    }


def test_review_api_returns_structured_error_for_github_api_error(monkeypatch):
    monkeypatch.setattr("ai_pr_review.api.review.ReviewService", GitHubErrorReviewService)
    client = TestClient(create_app())

    response = client.post(
        "/api/review",
        json={"pr_url": "https://github.com/owner/repo/pull/123"},
    )

    assert response.status_code == 502
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "GitHub API error"
    assert body["data"] is None
    assert body["error"]["code"] == "GITHUB_API_ERROR"
    assert body["error"]["detail"] == "GitHub request failed with status 500"
