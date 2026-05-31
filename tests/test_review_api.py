from fastapi.testclient import TestClient

from main import create_app


class FakeReviewService:
    called_with: str | None = None

    def __init__(self, github_client=None) -> None:
        pass

    def review(self, pr_url: str) -> dict:
        self.__class__.called_with = pr_url
        return {
            "pr": {
                "url": pr_url,
                "number": 123,
                "title": "Test PR",
            },
            "summary": {
                "files_changed": 2,
                "additions": 10,
                "deletions": 3,
            },
            "ai_summary": "Mock review summary.",
            "risks": [
                {
                    "file": "src/app.py",
                    "risk_level": "low",
                    "message": "Mock risk.",
                }
            ],
            "review_suggestions": "Mock suggestion.",
        }


def test_review_api_returns_success_response(monkeypatch):
    FakeReviewService.called_with = None
    monkeypatch.setattr("ai_pr_review.api.review.ReviewService", FakeReviewService)
    client = TestClient(create_app())

    response = client.post(
        "/api/review",
        json={"pr_url": "https://github.com/owner/repo/pull/123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "PR review completed."
    assert body["error"] is None
    assert body["data"]["pr"]["number"] == 123
    assert body["data"]["summary"]["files_changed"] == 2
    assert body["data"]["ai_summary"] == "Mock review summary."
    assert len(body["data"]["risks"]) == 1
    assert body["data"]["review_suggestions"] == "Mock suggestion."
    assert FakeReviewService.called_with == "https://github.com/owner/repo/pull/123"
