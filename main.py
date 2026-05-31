from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

try:
    from ai_pr_review.api import router as api_router
    from ai_pr_review.exceptions import AIPrReviewError
except ModuleNotFoundError:
    from src.ai_pr_review.api import router as api_router
    from src.ai_pr_review.exceptions import AIPrReviewError


async def ai_pr_review_error_handler(request: Request, exc: AIPrReviewError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
            "error": {
                "code": exc.code,
                "detail": exc.detail,
            },
        },
    )


def create_app() -> FastAPI:
    app = FastAPI(title="AI PR Review Assistant")
    app.add_exception_handler(AIPrReviewError, ai_pr_review_error_handler)
    app.include_router(api_router)
    return app


app = create_app()
