"""MCP prompt registration for the LinkedIn Writer server."""

import logging

import opik
from fastmcp import FastMCP

from writing.utils.opik_utils import opik_context

logger = logging.getLogger(__name__)

WORKFLOW_INSTRUCTIONS = """
Your job is to execute the LinkedIn post writing workflow below.

All the tools require a `working_dir` parameter — the path to the working directory.
If the user doesn't provide it, ask for it before executing any tool.

The working directory must contain:
- `guideline.md` — describes what the post should be about (topic, angle, audience)
- `research.md` — provides factual material to draw from (from the research agent)

## Workflow

1. **Setup:**

    1.1. Explain the numbered steps of the workflow to the user. Be concise.

    1.2. Ask the user for the working directory path, if not provided. Verify that
    `guideline.md` and `research.md` exist in it.

2. **Generate the LinkedIn post:**

    Call the `generate_post` tool with the `working_dir`.

    This internally runs:
    - Generates an initial post from the guideline + research + writing profiles.
    - Runs N rounds of review + edit (evaluator-optimizer loop).
    - Saves intermediate versions in `.memory/` as `reviews_1.json`, `reviews_2.json`, etc.
    - Saves each intermediate post as `post_0.md`, `post_1.md`, `post_2.md`, etc.
    - Saves the final post as `post.md`.

    Present the final post to the user.

3. **Generate an image:**

    Call the `generate_image` tool with the `working_dir`.

    This generates a professional LinkedIn-appropriate image based on the post content
    and saves it as `post_image.png` inside the working directory.

    Present both the final post and the image to the user.

4. **Edit with feedback (optional, repeat as needed):**

    If the user wants changes, call the `edit_post` tool with the `working_dir`
    and the user's `human_feedback` string.

    This runs one review + edit pass guided by the human feedback, which takes
    highest priority over all other constraints.

    Present the updated post to the user. Repeat this phase as many times as the
    user requests.

## File Structure After Completion

```
working_dir/
├── guideline.md
├── research.md
├── .memory/
│   ├── reviews_1.json
│   └── reviews_2.json
├── post_0.md
├── post_1.md
├── post_2.md
├── post.md
└── post_image.png
```

## Critical Failure Policy

If any tool reports a failure, halt the workflow immediately:
1. Name the exact tool that failed.
2. Quote the tool's output verbatim.
3. Ask the user how to proceed.
""".strip()


def register_mcp_prompts(mcp: FastMCP) -> None:
    """Register all MCP prompts with the given FastMCP server instance.

    Args:
        mcp: The FastMCP server instance to register prompts on.
    """

    @mcp.prompt()
    @opik.track(type="general")
    async def linkedin_post_workflow() -> str:
        """Complete LinkedIn post writing workflow instructions."""
        opik_context.initialize_thread_id()
        return WORKFLOW_INSTRUCTIONS
