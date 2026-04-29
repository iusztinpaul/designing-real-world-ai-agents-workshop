"""Pydantic Settings configuration for the Deep Research MCP Server."""

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

    server_name: str = "Deep Research MCP Server"
    version: str = "0.1.0"
    log_level: int = Field(default=logging.INFO, alias="LOG_LEVEL")

    gemini_model: str = "gemini-3-flash-preview"
    youtube_transcription_model: str = "gemini-3.1-pro-preview"

    google_api_key: SecretStr = Field(alias="GOOGLE_API_KEY")
    opik_api_key: SecretStr | None = Field(default=None, alias="OPIK_API_KEY")
    opik_workspace: str | None = Field(default=None, alias="OPIK_WORKSPACE")
    opik_project_name: str = Field(default="research-agent", alias="OPIK_PROJECT_NAME")


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()
