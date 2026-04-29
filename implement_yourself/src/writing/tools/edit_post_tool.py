"""Edit post tool implementation for the LinkedIn Writer MCP server."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def edit_post_tool(
    working_dir: str, human_feedback: str, delete_iterations: bool = False
) -> dict[str, Any]:
    """Edit an existing LinkedIn post based on human feedback.

    Args:
        working_dir: Directory containing the existing post.md.
        human_feedback: Feedback from the human on how to edit the post.
        delete_iterations: Whether to delete intermediate post versions and reviews.

    Returns:
        A placeholder dict indicating the tool is not yet implemented.
    """
    return {
        "status": "not_implemented",
        "tool": "edit_post",
        "working_dir": working_dir,
        "message": "Shell only — implementation lands in task #014.",
    }
