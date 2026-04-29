"""Deep research tool implementation for the Deep Research MCP server."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def deep_research_tool(working_dir: str, query: str) -> dict[str, Any]:
    """Research a topic using Gemini with Google Search grounding.

    Args:
        working_dir: Directory where research outputs are stored.
        query: The research query or topic to investigate.

    Returns:
        A dict with the tool result or placeholder status.
    """
    return {
        "status": "not_implemented",
        "tool": "deep_research",
        "working_dir": working_dir,
        "message": "Shell only — implementation lands in task #004.",
    }
