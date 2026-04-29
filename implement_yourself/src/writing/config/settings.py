"""Pydantic Settings configuration for the LinkedIn Writer MCP Server."""

import logging
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    server_name: str = "LinkedIn Writer MCP Server"
    version: str = "0.1.0"
    log_level: int = Field(default=logging.INFO, alias="LOG_LEVEL")

    writer_model: str = "gemini-3-flash-preview"
    reviewer_model: str = "gemini-3-flash-preview"
    image_model: str = "gemini-2.5-flash-image"

    num_reviews: int = 4

    google_api_key: SecretStr = Field(alias="GOOGLE_API_KEY")
    opik_api_key: SecretStr | None = Field(default=None, alias="OPIK_API_KEY")
    opik_workspace: str | None = Field(default=None, alias="OPIK_WORKSPACE")
    opik_project_name: str = Field(
        default="writing-workflow", alias="OPIK_PROJECT_NAME"
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()
