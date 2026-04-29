"""MCP tool registration for the Deep Research server."""

import logging
from typing import Any

from fastmcp import FastMCP

from research.tools.analyze_youtube_video_tool import analyze_youtube_video_tool
from research.tools.compile_research_tool import compile_research_tool
from research.tools.deep_research_tool import deep_research_tool

logger = logging.getLogger(__name__)


def register_mcp_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the given FastMCP server instance.

    Args:
        mcp: The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    async def deep_research(working_dir: str, query: str) -> dict[str, Any]:
        """Research a topic using Gemini with Google Search grounding."""
        return await deep_research_tool(working_dir=working_dir, query=query)

    @mcp.tool()
    async def analyze_youtube_video(
        working_dir: str, youtube_url: str
    ) -> dict[str, Any]:
        """Analyze a YouTube video using Gemini's native video understanding."""
        return await analyze_youtube_video_tool(
            working_dir=working_dir, youtube_url=youtube_url
        )

    @mcp.tool()
    async def compile_research(working_dir: str) -> dict[str, Any]:
        """Aggregate all collected research into a single markdown research brief."""
        return await compile_research_tool(working_dir=working_dir)
