from fastapi.testclient import TestClient

from main import create_app


class FakeReviewService:
    called_with: str | None = None
    publish_called = False

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

    def publish_review_comment(self, pr_url, review):
        self.__class__.publish_called = True
        raise AssertionError("publish_review_comment should not be called by default")


class PublishingReviewService(FakeReviewService):
    publish_called_with: tuple[str, object] | None = None

    def publish_review_comment(self, pr_url, review):
        self.__class__.publish_called = True
        self.__class__.publish_called_with = (pr_url, review)
        return "https://github.com/owner/repo/issues/123#issuecomment-456"


def test_review_api_returns_success_response(monkeypatch):
    FakeReviewService.called_with = None
    FakeReviewService.publish_called = False
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
    assert body["data"]["comment_published"] is False
    assert body["data"]["comment_url"] is None
    assert FakeReviewService.called_with == "https://github.com/owner/repo/pull/123"
    assert FakeReviewService.publish_called is False


def test_review_api_publishes_comment_only_when_publish_is_true(monkeypatch):
    PublishingReviewService.called_with = None
    PublishingReviewService.publish_called = False
    PublishingReviewService.publish_called_with = None
    monkeypatch.setattr("ai_pr_review.api.review.ReviewService", PublishingReviewService)
    client = TestClient(create_app())

    response = client.post(
        "/api/review",
        json={
            "pr_url": "https://github.com/owner/repo/pull/123",
            "publish": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["comment_published"] is True
    assert body["data"]["comment_url"] == "https://github.com/owner/repo/issues/123#issuecomment-456"
    assert PublishingReviewService.called_with == "https://github.com/owner/repo/pull/123"
    assert PublishingReviewService.publish_called is True
    assert PublishingReviewService.publish_called_with[0] == "https://github.com/owner/repo/pull/123"
