"""Run the LinkedIn writing workflow on every post in the dataset.

For each post in the dataset index, this script:
1. Creates a working directory under {output_dir}/{slug}/
2. Copies the guideline and seed as research.md
3. Runs the writing MCP server to generate the post (and optionally an image)
4. Results stay in the output directory

Usage:
    uv run python scripts/run_dataset_writing.py [--output-dir DIR] [--skip-image] [--slug SLUG]
"""

import asyncio
import logging
import shutil
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
        result = await client.call_tool("generate_post", {"working_dir": working_dir})
        data = getattr(result, "data", {})
        results["status"] = (
            data.get("status", "unknown") if isinstance(data, dict) else "unknown"
        )
        results["post"] = data.get("post", "") if isinstance(data, dict) else ""

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
@click.option(
    "--output-dir",
    "-o",
    default="test_all",
    help="Output directory for generated posts (default: test_all)",
)
@click.option("--skip-image", is_flag=True, help="Skip image generation")
@click.option("--slug", default=None, help="Process only this slug (default: all)")
def main(output_dir: str, skip_image: bool, slug: str | None) -> None:
    """Run the writing workflow on the dataset."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load index
    index_path = DATASET_DIR / "index.yaml"
    entries = yaml.safe_load(index_path.read_text(encoding="utf-8"))

    if slug:
        entries = [e for e in entries if e["slug"] == slug]
        if not entries:
            logger.error(f"Slug not found: {slug}")
            return

    logger.info(
        f"Processing {len(entries)} posts → {output_path} (skip_image={skip_image})"
    )

    succeeded = 0
    failed = 0

    for i, entry in enumerate(entries):
        entry_slug = entry["slug"]
        work_dir = output_path / entry_slug
        logger.info(f"[{i + 1}/{len(entries)}] {entry_slug}")

        # Skip if already processed
        if (work_dir / "post.md").exists():
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

        # Prepare working directory
        work_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(guideline_src, work_dir / "guideline.md")
        shutil.copy2(seed_src, work_dir / "research.md")

        try:
            results = asyncio.run(
                run_writing_workflow(str(work_dir), skip_image=skip_image)
            )

            if results.get("status") != "success":
                logger.warning(f"  Failed: {results.get('status')}")
                failed += 1
                continue

            logger.info(
                f"  Done: {work_dir / 'post.md'} ({len(results.get('post', ''))} chars)"
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
