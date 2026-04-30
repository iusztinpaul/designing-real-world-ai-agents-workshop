"""MCP resource registration for the LinkedIn Writer server."""

import logging
from typing import Any

from fastmcp import FastMCP

from writing.app.profile_loader import load_profiles
from writing.config.settings import get_settings

logger = logging.getLogger(__name__)


def register_mcp_resources(mcp: FastMCP) -> None:
    """Register all MCP resources with the given FastMCP server instance.

    Args:
        mcp: The FastMCP server instance to register resources on.
    """

    @mcp.resource("config://settings")
    async def get_config() -> dict[str, Any]:
        """Get the current LinkedIn Writer server configuration."""
        settings = get_settings()
        return {
            "server_name": settings.server_name,
            "version": settings.version,
            "writer_model": settings.writer_model,
            "reviewer_model": settings.reviewer_model,
            "image_model": settings.image_model,
            "num_reviews": settings.num_reviews,
            "has_google_api_key": settings.google_api_key is not None,
            "has_opik_api_key": settings.opik_api_key is not None,
        }

    @mcp.resource("profiles://all")
    async def get_profiles() -> dict[str, str]:
        """Get the full markdown content of all four shipped writing profiles."""
        profiles = load_profiles()
        return {
            "structure": profiles.structure.content,
            "terminology": profiles.terminology.content,
            "character": profiles.character.content,
            "branding": profiles.branding.content,
        }
