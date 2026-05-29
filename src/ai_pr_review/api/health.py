from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    return {
        "success": True,
        "message": "AI PR Review Assistant is running.",
        "data": {"status": "ok", "app_env": settings.app_env},
        "error": None,
    }
