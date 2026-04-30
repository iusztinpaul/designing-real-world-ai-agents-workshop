"""MCP tool registration for the Deep Research server."""

import logging
from typing import Any

import opik
from fastmcp import FastMCP

from research.tools.analyze_youtube_video_tool import analyze_youtube_video_tool
from research.tools.compile_research_tool import compile_research_tool
from research.tools.deep_research_tool import deep_research_tool
from research.utils.opik_utils import opik_context

logger = logging.getLogger(__name__)


def register_mcp_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the given FastMCP server instance.

    Args:
        mcp: The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    @opik.track(type="tool")
    async def deep_research(working_dir: str, query: str) -> dict[str, Any]:
        """Research a topic using Gemini with Google Search grounding."""
        opik_context.update_thread_id()
        return await deep_research_tool(working_dir=working_dir, query=query)

    @mcp.tool()
    @opik.track(type="tool")
    async def analyze_youtube_video(
        working_dir: str, youtube_url: str
    ) -> dict[str, Any]:
        """Analyze a YouTube video using Gemini's native video understanding."""
        opik_context.update_thread_id()
        return await analyze_youtube_video_tool(
            working_dir=working_dir, youtube_url=youtube_url
        )

    @mcp.tool()
    @opik.track(type="tool")
    async def compile_research(working_dir: str) -> dict[str, Any]:
        """Aggregate all collected research into a single markdown research brief."""
        opik_context.update_thread_id()
        return await compile_research_tool(working_dir=working_dir)
