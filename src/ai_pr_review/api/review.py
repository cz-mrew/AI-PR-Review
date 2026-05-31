from fastapi import APIRouter, Depends

from ..github.client import GitHubClient
from ..github.comment import build_issue_comment_body
from ..review.service import ReviewService
from ..schemas import ApiResponse
from ..schemas.review import ReviewRequest, ReviewResponse


class ReviewService:
    def review(self, pr_url: str) -> ReviewResponse:
        return ReviewResponse(
            pr={"url": pr_url},
            summary={},
            ai_summary=None,
            risks=[],
            review_suggestions=None,
        )

    def publish_review_comment(self, pr_url: str, review: ReviewResponse) -> str | None:
        owner, repo, pull_number = GitHubClient.parse_pr_url(pr_url)
        comment_body = build_issue_comment_body(_format_review_comment_report(review))
        comment = GitHubClient().create_issue_comment(owner, repo, pull_number, comment_body)
        return comment.get("html_url")


router = APIRouter()


def get_review_service() -> ReviewService:
    return ReviewService(GitHubClient())


@router.post("/review", response_model=ApiResponse[ReviewResponse])
def review_pull_request(
    request: ReviewRequest,
    service: ReviewService = Depends(get_review_service),
) -> ApiResponse[ReviewResponse]:
    result = service.review(request.pr_url)
    if isinstance(result, dict):
        result = ReviewResponse.model_validate(result)

    if request.publish:
        result.comment_url = service.publish_review_comment(request.pr_url, result)
        result.comment_published = True

    return ApiResponse(
        success=True,
        message="PR review completed.",
        data=result,
        error=None,
    )


def _format_review_comment_report(review: ReviewResponse) -> str:
    lines = ["# PR Review Report", "", "## PR"]
    for key, value in review.pr.items():
        lines.append(f"- **{key}**: {value}")

    lines.extend(["", "## Summary"])
    for key, value in review.summary.items():
        lines.append(f"- **{key}**: {value}")

    lines.extend(["", "## AI Summary", review.ai_summary or "No AI summary available."])

    lines.extend(["", "## Risks"])
    if review.risks:
        for risk in review.risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- No risks found.")

    lines.extend([
        "",
        "## Review Suggestions",
        review.review_suggestions or "No review suggestions available.",
    ])
    return "\n".join(lines)
