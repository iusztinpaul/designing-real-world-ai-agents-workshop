"""MCP Resources registration for configuration exposure."""

from typing import Any

from fastmcp import FastMCP

from research.config.settings import get_settings


def register_mcp_resources(mcp: FastMCP) -> None:
    """Register all MCP resources with the server instance."""

    @mcp.resource("config://settings")
    async def get_config() -> dict[str, Any]:
        """Get the current research agent configuration.

        Returns server settings including model names and feature flags.
        API key values are never exposed — only their presence is indicated.
        """

        settings = get_settings()

        return {
            "server_name": settings.server_name,
            "version": settings.version,
            "gemini_model": settings.gemini_model,
            "query_generation_model": settings.query_generation_model,
            "youtube_transcription_model": settings.youtube_transcription_model,
            "source_selection_model": settings.source_selection_model,
            "has_google_api_key": settings.google_api_key is not None,
            "has_opik_api_key": settings.opik_api_key is not None,
            "opik_workspace": settings.opik_workspace,
            "opik_project_name": settings.opik_project_name,
        }
