"""Generate image tool implementation for the LinkedIn Writer MCP server."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def generate_image_tool(working_dir: str) -> dict[str, Any]:
    """Generate a LinkedIn post image using Gemini Flash Image.

    Args:
        working_dir: Directory containing the post.md to generate an image for.

    Returns:
        A placeholder dict indicating the tool is not yet implemented.
    """
    return {
        "status": "not_implemented",
        "tool": "generate_image",
        "working_dir": working_dir,
        "message": "Shell only — implementation lands in task #015.",
    }
