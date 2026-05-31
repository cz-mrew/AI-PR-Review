from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..github.client import GitHubClient
from ..review.service import ReviewService
from ..schemas import ApiResponse


class ReviewRequest(BaseModel):
    pr_url: str


class ReviewResponse(BaseModel):
    pr: dict
    summary: dict
    ai_summary: str | None
    risks: list
    review_suggestions: str | None


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

    return ApiResponse(
        success=True,
        message="PR review completed.",
        data=result,
        error=None,
    )
