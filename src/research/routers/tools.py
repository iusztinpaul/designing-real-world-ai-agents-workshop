"""MCP Tools registration for research operations."""

from typing import Any

from fastmcp import FastMCP

from research.tools.create_research_file_tool import create_research_file_tool
from research.tools.extract_seed_tool import extract_seed_tool
from research.tools.generate_queries_tool import generate_queries_tool
from research.tools.run_research_tool import run_research_tool
from research.tools.select_sources_tool import select_sources_tool
from research.tools.transcribe_youtube_tool import transcribe_youtube_tool


def register_mcp_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the server instance."""

    # ========================================================================
    # SEED EXTRACTION
    # ========================================================================

    @mcp.tool()
    async def extract_seed(
        working_dir: str, seed_filename: str = "seed.md"
    ) -> dict[str, Any]:
        """Extract topics, research questions, and YouTube URLs from a seed file.

        Reads the seed file in the working directory and uses Gemini to extract
        structured research information. Results are saved to
        .memory/seed_extraction.json.

        Args:
            working_dir: Path to the working directory containing the seed file.
            seed_filename: Name of the seed file (default: seed.md).
        """

        return await extract_seed_tool(working_dir, seed_filename)

    # ========================================================================
    # YOUTUBE TRANSCRIPTION
    # ========================================================================

    @mcp.tool()
    async def transcribe_youtube(
        working_dir: str, youtube_urls: list[str]
    ) -> dict[str, Any]:
        """Transcribe YouTube videos using Gemini.

        Processes each YouTube URL and saves the transcription as a markdown
        file in .memory/transcripts/.

        Args:
            working_dir: Path to the working directory.
            youtube_urls: List of YouTube video URLs to transcribe.
        """

        return await transcribe_youtube_tool(working_dir, youtube_urls)

    # ========================================================================
    # RESEARCH QUERY GENERATION
    # ========================================================================

    @mcp.tool()
    async def generate_next_queries(
        working_dir: str, n_queries: int = 3
    ) -> dict[str, Any]:
        """Generate research queries that fill knowledge gaps.

        Analyzes the seed context, past research results, and YouTube
        transcripts to identify gaps and propose new web-search questions.

        Args:
            working_dir: Path to the working directory containing .memory/ data.
            n_queries: Number of queries to generate (default: 3).
        """

        return await generate_queries_tool(working_dir, n_queries)

    # ========================================================================
    # GROUNDED RESEARCH
    # ========================================================================

    @mcp.tool()
    async def run_research(working_dir: str, queries: list[str]) -> dict[str, Any]:
        """Run Gemini grounded search for a list of research queries.

        Executes each query using Gemini with Google Search grounding and
        appends results to .memory/research_results.json.

        Args:
            working_dir: Path to the working directory.
            queries: List of research queries to execute.
        """

        return await run_research_tool(working_dir, queries)

    # ========================================================================
    # SOURCE SELECTION
    # ========================================================================

    @mcp.tool()
    async def select_sources(working_dir: str) -> dict[str, Any]:
        """Filter and select high-quality sources from research results.

        Uses Gemini to evaluate sources for trustworthiness, authority, and
        relevance. Results are saved to .memory/selected_sources.json.

        Args:
            working_dir: Path to the working directory.
        """

        return await select_sources_tool(working_dir)

    # ========================================================================
    # RESEARCH FILE CREATION
    # ========================================================================

    @mcp.tool()
    async def create_research_file(working_dir: str) -> dict[str, Any]:
        """Generate the final comprehensive research.md file.

        Combines all research data from .memory/ into a structured markdown
        file with collapsible sections for easy navigation.

        Args:
            working_dir: Path to the working directory containing .memory/ data.
        """

        return create_research_file_tool(working_dir)
