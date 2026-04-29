"""MCP resource registration for the Deep Research server."""

import logging
from typing import Any

from fastmcp import FastMCP

from research.config.settings import get_settings

logger = logging.getLogger(__name__)


def register_mcp_resources(mcp: FastMCP) -> None:
    """Register all MCP resources with the given FastMCP server instance.

    Args:
        mcp: The FastMCP server instance to register resources on.
    """

    @mcp.resource("resource://config/research")
    async def get_research_config() -> dict[str, Any]:
        """Get the current research agent configuration."""
        settings = get_settings()
        return {
            "server_name": settings.server_name,
            "version": settings.version,
            "gemini_model": settings.gemini_model,
            "youtube_transcription_model": settings.youtube_transcription_model,
            "has_google_api_key": settings.google_api_key is not None,
            "has_opik_api_key": settings.opik_api_key is not None,
            "opik_workspace": settings.opik_workspace,
            "opik_project_name": settings.opik_project_name,
        }
