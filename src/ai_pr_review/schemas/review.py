from pydantic import BaseModel


class ReviewRequest(BaseModel):
    pr_url: str
    publish: bool = False


class ReviewResponse(BaseModel):
    pr: dict
    summary: dict
    ai_summary: str | None
    risks: list
    review_suggestions: str | None
    comment_published: bool = False
    comment_url: str | None = None
