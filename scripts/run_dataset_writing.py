"""Run the LinkedIn writing workflow on every post in the dataset.

For each post in the dataset index, this script:
1. Creates a temporary working directory with guideline.md and research.md
2. Runs the writing MCP server to generate the post (and optionally an image)
3. Copies the output back to the dataset root as {slug}_generated.md (and {slug}_generated.png)

Usage:
    uv run python scripts/run_dataset_writing.py [--skip-image] [--slug SLUG]
"""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

import click
import yaml
from fastmcp import Client

logger = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).parent.parent / "datasets" / "linkedin_paul_iusztin"
SERVER_PATH = str(Path(__file__).parent.parent / "src" / "writing" / "server.py")


async def run_writing_workflow(
    working_dir: str, skip_image: bool = False
) -> dict[str, str]:
    """Run the writing workflow for a single post."""

    client = Client(SERVER_PATH)
    results = {}

    async with client:
        # Generate post (includes review/edit loop)
        result = await client.call_tool("generate_post", {"working_dir": working_dir})
        data = getattr(result, "data", {})
        results["status"] = (
            data.get("status", "unknown") if isinstance(data, dict) else "unknown"
        )
        results["post"] = data.get("post", "") if isinstance(data, dict) else ""

        # Generate image
        if not skip_image:
            try:
                result = await client.call_tool(
                    "generate_image", {"working_dir": working_dir}
                )
                data = getattr(result, "data", {})
                results["image"] = (
                    data.get("image_path", "") if isinstance(data, dict) else ""
                )
            except Exception as e:
                logger.warning(f"Image generation failed: {e}")
                results["image"] = "failed"

    return results


@click.command()
@click.option("--skip-image", is_flag=True, help="Skip image generation")
@click.option("--slug", default=None, help="Process only this slug (default: all)")
def main(skip_image: bool, slug: str | None) -> None:
    """Run the writing workflow on the dataset."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Load index
    index_path = DATASET_DIR / "index.yaml"
    entries = yaml.safe_load(index_path.read_text(encoding="utf-8"))

    # Filter to single slug if specified
    if slug:
        entries = [e for e in entries if e["slug"] == slug]
        if not entries:
            logger.error(f"Slug not found: {slug}")
            return

    logger.info(f"Processing {len(entries)} posts (skip_image={skip_image})")

    succeeded = 0
    failed = 0

    for i, entry in enumerate(entries):
        entry_slug = entry["slug"]
        logger.info(f"[{i + 1}/{len(entries)}] {entry_slug}")

        # Skip if already generated
        generated_post = DATASET_DIR / f"{entry_slug}_generated.md"
        if generated_post.exists():
            logger.info("  Skipping (already exists)")
            succeeded += 1
            continue

        # Check required files
        guideline_src = DATASET_DIR / f"{entry_slug}_guideline.md"
        seed_src = DATASET_DIR / f"{entry_slug}_seed.md"
        if not guideline_src.exists() or not seed_src.exists():
            logger.warning("  Missing guideline or seed, skipping")
            failed += 1
            continue

        # Use a temp directory as the working dir, then copy results back
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            shutil.copy2(guideline_src, tmp_path / "guideline.md")
            shutil.copy2(seed_src, tmp_path / "research.md")

            try:
                results = asyncio.run(
                    run_writing_workflow(str(tmp_path), skip_image=skip_image)
                )

                if results.get("status") != "success":
                    logger.warning(f"  Failed: {results.get('status')}")
                    failed += 1
                    continue

                # Copy post back to dataset root
                post_src = tmp_path / "post.md"
                if post_src.exists():
                    shutil.copy2(post_src, generated_post)

                # Copy image back to dataset root
                image_src = tmp_path / "post_image.png"
                if image_src.exists():
                    shutil.copy2(image_src, DATASET_DIR / f"{entry_slug}_generated.png")

                logger.info(
                    f"  Done: {entry_slug}_generated.md "
                    f"({len(results.get('post', ''))} chars)"
                )
                succeeded += 1

            except Exception as e:
                logger.error(f"  Error: {e}")
                failed += 1

    logger.info(
        f"\nResults: {succeeded} succeeded, {failed} failed out of {len(entries)}"
    )


if __name__ == "__main__":
    main()
