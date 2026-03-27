"""MCP Resources registration for configuration and profiles."""

from typing import Any

from fastmcp import FastMCP

from writing.app.profile_loader import load_profiles
from writing.config.settings import get_settings


def register_mcp_resources(mcp: FastMCP) -> None:
    """Register all MCP resources with the server instance."""

    @mcp.resource("config://settings")
    async def get_config() -> dict[str, Any]:
        """Get the current writer configuration.

        Returns server settings including model names and review iterations.
        API key values are never exposed.
        """

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
        """Get all writing profiles content.

        Returns the full markdown content of all 4 profiles
        (structure, terminology, character, branding).
        """

        profiles = load_profiles()

        return {
            "structure": profiles.structure.content,
            "terminology": profiles.terminology.content,
            "character": profiles.character.content,
            "branding": profiles.branding.content,
        }
