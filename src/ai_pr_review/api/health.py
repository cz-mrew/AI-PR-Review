from fastapi import APIRouter

from ..config import get_settings
from ..schemas import ApiResponse
from ..utils import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", response_model=ApiResponse[dict])
def health_check() -> ApiResponse[dict]:
    settings = get_settings()
    logger.info("Health check requested.")
    return ApiResponse(
        success=True,
        message="AI PR Review Assistant is running.",
        data={"status": "ok", "app_env": settings.app_env},
        error=None,
    )
