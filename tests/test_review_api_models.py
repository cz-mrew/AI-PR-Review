from ai_pr_review.schemas.review import ReviewRequest, ReviewResponse


def test_review_request_model_accepts_pr_url():
    request = ReviewRequest(pr_url="https://github.com/owner/repo/pull/123")

    assert request.pr_url == "https://github.com/owner/repo/pull/123"


def test_review_response_model_accepts_required_fields():
    response = ReviewResponse(
        pr={
            "number": 123,
            "title": "Add review API models",
        },
        summary={
            "files_changed": 2,
            "additions": 20,
            "deletions": 4,
        },
        ai_summary="This PR defines review API request and response models.",
        risks=[
            {
                "file": "src/ai_pr_review/api/review.py",
                "risk_level": "low",
                "message": "New API schema only.",
            }
        ],
        review_suggestions="Add endpoint implementation in a later PR.",
    )

    assert response.pr["number"] == 123
    assert response.summary["files_changed"] == 2
    assert response.ai_summary == "This PR defines review API request and response models."
    assert len(response.risks) == 1
    assert response.review_suggestions == "Add endpoint implementation in a later PR."


def test_review_response_optional_text_fields_can_be_none():
    response = ReviewResponse(
        pr={},
        summary={},
        ai_summary=None,
        risks=[],
        review_suggestions=None,
    )

    assert response.ai_summary is None
    assert response.review_suggestions is None
