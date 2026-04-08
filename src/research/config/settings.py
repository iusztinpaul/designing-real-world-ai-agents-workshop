"""Server configuration settings."""

import logging
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings for the Research MCP Server."""

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )

    # Server settings
    server_name: str = Field(
        default="Deep Research MCP Server", description="The name of the server"
    )
    version: str = Field(default="0.1.0", description="The version of the server")
    log_level: int = Field(
        default=logging.INFO, alias="LOG_LEVEL", description="The log level"
    )

    # LLM Configuration
    gemini_model: str = Field(
        default="gemini-3-flash-preview", description="Default Gemini model for general use"
    )
    youtube_transcription_model: str = Field(
        default="gemini-3.1-pro-preview", description="Model for YouTube video analysis"
    )

    # API Keys
    google_api_key: SecretStr = Field(
        alias="GOOGLE_API_KEY", description="The API key for the Google Gemini API"
    )

    # Opik Monitoring Configuration
    opik_api_key: SecretStr | None = Field(
        default=None,
        alias="OPIK_API_KEY",
        description="The API key to authenticate with Opik",
    )
    opik_workspace: str | None = Field(
        default=None, alias="OPIK_WORKSPACE", description="The Opik workspace name"
    )
    opik_project_name: str = Field(
        default="research-agent",
        alias="OPIK_PROJECT_NAME",
        description="Opik project name",
    )


@lru_cache
def get_settings() -> Settings:
    """Get the singleton settings instance."""

    return Settings()
