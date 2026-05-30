from fastapi import FastAPI

try:
    from ai_pr_review.api import router as api_router
except ModuleNotFoundError:
    from src.ai_pr_review.api import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI PR Review Assistant")
    app.include_router(api_router)
    return app


app = create_app()
