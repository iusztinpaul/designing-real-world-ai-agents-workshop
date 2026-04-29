"""Generate post tool implementation for the LinkedIn Writer MCP server."""

import logging
from pathlib import Path
from typing import Any

from writing.app.generate_post import generate_post
from writing.config.constants import GUIDELINE_FILE, POST_FILE, RESEARCH_FILE
from writing.config.settings import get_settings

logger = logging.getLogger(__name__)


async def generate_post_tool(
    working_dir: str, delete_iterations: bool = False
) -> dict[str, Any]:
    """Generate a LinkedIn post with an evaluate-optimize loop.

    Reads guideline.md and research.md from working_dir, calls generate_post,
    and saves the result. Intermediate versions are saved unless delete_iterations
    is True.

    Args:
        working_dir: Directory containing guideline.md and research.md.
        delete_iterations: Whether to delete intermediate post versions and reviews.

    Returns:
        A dict with status, review_iterations, output_path, message, and post.

    Raises:
        FileNotFoundError: If guideline.md or research.md is missing.
    """
    settings = get_settings()
    working_path = Path(working_dir)

    # Step 1: Validate inputs
    guideline_path = working_path / GUIDELINE_FILE
    research_path = working_path / RESEARCH_FILE
    if not guideline_path.exists():
        msg = f"{GUIDELINE_FILE} not found in {working_dir}"
        raise FileNotFoundError(msg)
    if not research_path.exists():
        msg = f"{RESEARCH_FILE} not found in {working_dir}"
        raise FileNotFoundError(msg)

    # Step 2: Read both files
    guideline = guideline_path.read_text(encoding="utf-8")
    research = research_path.read_text(encoding="utf-8")

    # Step 3: Generate the post
    result = await generate_post(guideline, research)

    # Step 4: Save intermediate versions (unless delete_iterations is set)
    if not delete_iterations:
        for idx, version in enumerate(result.versions):
            version_path = working_path / f"post_{idx}.md"
            version_path.write_text(version.content, encoding="utf-8")
            logger.info("Saved version %d to %s", idx, version_path.name)

    # Step 5: Always write the final post
    output_path = working_path / POST_FILE
    output_path.write_text(result.post.content, encoding="utf-8")
    logger.info("Final post saved to %s", output_path)

    # Step 6: Return the result dict
    return {
        "status": "success",
        "review_iterations": settings.num_reviews,
        "output_path": str(output_path.resolve()),
        "message": (
            f"Generated LinkedIn post with {settings.num_reviews} review/edit iterations. "
            f"Final post saved to {POST_FILE}"
        ),
        "post": result.post.content,
    }
