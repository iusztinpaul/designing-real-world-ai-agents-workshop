"""Generate seed and guideline files for each LinkedIn post in the dataset.

For each post in the dataset, this script:
1. Reads the post content (and optionally the image)
2. Calls Gemini to generate a guideline (used to reproduce the post via the writing workflow)
3. Calls Gemini to generate a seed (used to research topics related to the post)
4. Saves them as {slug}_guideline.md and {slug}_seed.md
5. Updates the index.yaml with the new file references

Usage:
    uv run python scripts/generate_dataset.py
"""

import asyncio
import logging
from pathlib import Path

import yaml
from google import genai
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from writing.utils.logging import setup_logging

logger = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).parent.parent / "datasets" / "linkedin_paul_iusztin"

PROMPT_GENERATE_GUIDELINE = """
You are analyzing a real LinkedIn post to reverse-engineer a guideline that could
be used to reproduce a similar post using an AI writing workflow.

The guideline should capture the INTENT behind the post, not the post itself.
It should be written as instructions for a ghostwriter who has NOT seen the post.

<post_content>
{post_content}
</post_content>

Generate a guideline in this exact markdown format:

# LinkedIn Post Guideline

## Topic
[One sentence: what is this post about?]

## Angle
[2-3 sentences: what perspective or approach should the post take? What makes it unique?]

## Target Audience
[1-2 sentences: who is this post for?]

## Key Points to Cover
[3-5 bullet points of the main ideas that should be in the post]

## Tone
[1-2 sentences: what tone should the post have?]

Return ONLY the markdown guideline, nothing else.
""".strip()

PROMPT_GENERATE_SEED = """
You are analyzing a real LinkedIn post to create a research seed document.
The seed will be used by a deep research agent to gather information on the
topics covered in this post.

The seed should identify the core research topics WITHOUT reproducing the post
content. Think of it as: "What would someone need to research to write this post?"

<post_content>
{post_content}
</post_content>

Generate a seed document in this exact markdown format:

# Research Topic: [Main topic in 5-10 words]

[1-2 sentences describing what to research and why]

## Key Questions

[3-5 numbered questions that a researcher should investigate to gather the
knowledge needed to write this post]

## References

[If the post mentions specific tools, frameworks, papers, or companies,
list them as bullet points. Otherwise, leave this section empty with just
a dash: - ]

Return ONLY the markdown seed, nothing else.
""".strip()


class ScriptSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )
    google_api_key: SecretStr


async def process_post(
    client: genai.Client, slug: str, post_path: Path
) -> tuple[str, str]:
    """Generate guideline and seed for a single post."""

    post_content = post_path.read_text(encoding="utf-8")

    # Extract just the content section (after "## Content")
    content_marker = "## Content"
    if content_marker in post_content:
        content_only = post_content.split(content_marker, 1)[1].strip()
    else:
        content_only = post_content

    # Generate guideline
    guideline_prompt = PROMPT_GENERATE_GUIDELINE.format(post_content=content_only)
    guideline_response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=guideline_prompt,
    )
    guideline = guideline_response.text

    # Generate seed
    seed_prompt = PROMPT_GENERATE_SEED.format(post_content=content_only)
    seed_response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=seed_prompt,
    )
    seed = seed_response.text

    return guideline, seed


async def main() -> None:
    setup_logging()

    settings = ScriptSettings()
    client = genai.Client(api_key=settings.google_api_key.get_secret_value())

    # Load index
    index_path = DATASET_DIR / "index.yaml"
    index_text = index_path.read_text(encoding="utf-8")

    # Parse YAML (skip the comment line)
    entries = yaml.safe_load(index_text)

    logger.info(f"Processing {len(entries)} posts...")

    for i, entry in enumerate(entries):
        slug = entry["slug"]
        post_path = DATASET_DIR / f"{slug}.md"

        if not post_path.exists():
            logger.warning(f"Post file not found: {post_path}")
            continue

        guideline_path = DATASET_DIR / f"{slug}_guideline.md"
        seed_path = DATASET_DIR / f"{slug}_seed.md"

        # Skip if already generated
        if guideline_path.exists() and seed_path.exists():
            logger.info(f"[{i + 1}/{len(entries)}] Skipping {slug} (already exists)")
            entry["local_guideline"] = f"./{slug}_guideline.md"
            entry["local_seed"] = f"./{slug}_seed.md"
            continue

        logger.info(f"[{i + 1}/{len(entries)}] Processing: {slug}")

        guideline, seed = await process_post(client, slug, post_path)

        # Save files
        guideline_path.write_text(guideline, encoding="utf-8")
        seed_path.write_text(seed, encoding="utf-8")

        # Update entry
        entry["local_guideline"] = f"./{slug}_guideline.md"
        entry["local_seed"] = f"./{slug}_seed.md"

        logger.info(f"  Saved: {slug}_guideline.md, {slug}_seed.md")

    # Write updated index
    header = "# Dataset Index - 20 sampled LinkedIn posts (>150 engagement, last 6 months)\n\n"
    yaml_content = yaml.dump(
        entries, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    index_path.write_text(header + yaml_content, encoding="utf-8")

    logger.info(f"Updated {index_path}")
    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
