from fastapi import APIRouter

from ..schemas.review import ReviewRequest, ReviewResponse

router = APIRouter()

__all__ = ["ReviewRequest", "ReviewResponse", "router"]
