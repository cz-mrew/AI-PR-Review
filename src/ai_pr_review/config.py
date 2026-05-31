from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="AI PR Review Assistant", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    request_timeout: float = Field(default=30.0, alias="REQUEST_TIMEOUT")
    max_diff_chars: int = Field(default=120_000, alias="MAX_DIFF_CHARS")
    max_patch_chars_per_file: int = Field(default=20_000, alias="MAX_PATCH_CHARS_PER_FILE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
