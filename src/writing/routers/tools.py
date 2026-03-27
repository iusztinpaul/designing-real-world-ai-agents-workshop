"""MCP Tools registration for writing operations."""

from typing import Any

from fastmcp import FastMCP

from writing.tools.edit_post_tool import edit_post_tool
from writing.tools.generate_image_tool import generate_image_tool
from writing.tools.generate_post_tool import generate_post_tool


def register_mcp_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the server instance."""

    # ========================================================================
    # POST GENERATION (with evaluate-optimize loop)
    # ========================================================================

    @mcp.tool()
    async def generate_post(working_dir: str) -> dict[str, Any]:
        """Generate a LinkedIn post with an evaluate-optimize loop.

        Reads guideline.md and research.md from the working directory, generates
        an initial post, then runs N rounds of review + edit to refine it.
        All intermediate versions are saved in .memory/.

        The final post is saved as post.md in the working directory.

        Args:
            working_dir: Path to the directory containing guideline.md and research.md.
        """

        return await generate_post_tool(working_dir)

    # ========================================================================
    # POST EDITING (single review+edit pass with human feedback)
    # ========================================================================

    @mcp.tool()
    async def edit_post(working_dir: str, human_feedback: str) -> dict[str, Any]:
        """Edit an existing LinkedIn post based on human feedback.

        Reads the existing post.md, runs a review pass with the human feedback
        as highest priority, then edits the post. The updated post.md is saved
        in place.

        Args:
            working_dir: Path to the directory containing post.md, guideline.md, research.md.
            human_feedback: The user's feedback on what to change in the post.
        """

        return await edit_post_tool(working_dir, human_feedback)

    # ========================================================================
    # IMAGE GENERATION
    # ========================================================================

    @mcp.tool()
    async def generate_image(working_dir: str) -> dict[str, Any]:
        """Generate a LinkedIn post image using Gemini Flash Image.

        Reads the existing post.md and generates a professional image
        following the branding and character profiles. Saved as post_image.png.

        Args:
            working_dir: Path to the directory containing post.md.
        """

        return await generate_image_tool(working_dir)
