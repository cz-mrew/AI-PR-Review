from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {
        "success": True,
        "message": "AI PR Review Assistant is running.",
        "data": {"status": "ok"},
        "error": None,
    }
