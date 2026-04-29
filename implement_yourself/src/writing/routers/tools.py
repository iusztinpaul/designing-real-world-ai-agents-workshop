"""MCP tool registration for the LinkedIn Writer server."""

import logging
from typing import Any

from fastmcp import FastMCP

from writing.tools.edit_post_tool import edit_post_tool
from writing.tools.generate_image_tool import generate_image_tool
from writing.tools.generate_post_tool import generate_post_tool

logger = logging.getLogger(__name__)


def register_mcp_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the given FastMCP server instance.

    Args:
        mcp: The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    async def generate_post(
        working_dir: str, delete_iterations: bool = False
    ) -> dict[str, Any]:
        """Generate a LinkedIn post with an evaluate-optimize loop."""
        return await generate_post_tool(
            working_dir=working_dir, delete_iterations=delete_iterations
        )

    @mcp.tool()
    async def edit_post(
        working_dir: str, human_feedback: str, delete_iterations: bool = False
    ) -> dict[str, Any]:
        """Edit an existing LinkedIn post based on human feedback."""
        return await edit_post_tool(
            working_dir=working_dir,
            human_feedback=human_feedback,
            delete_iterations=delete_iterations,
        )

    @mcp.tool()
    async def generate_image(working_dir: str) -> dict[str, Any]:
        """Generate a LinkedIn post image using Gemini Flash Image."""
        return await generate_image_tool(working_dir=working_dir)
