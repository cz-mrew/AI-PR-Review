from pydantic import BaseModel


class ReviewRequest(BaseModel):
    pr_url: str


class ReviewResponse(BaseModel):
    pr: dict
    summary: dict
    ai_summary: str | None
    risks: list
    review_suggestions: str | None
