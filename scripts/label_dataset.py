"""Label the dataset by comparing generated posts against ground truth.

For each post in the dataset, compares the generated post with the original
ground truth post and assigns a binary pass/fail label with a critique.

Usage:
    uv run python scripts/label_dataset.py [--slug SLUG]
"""

import asyncio
import logging
from pathlib import Path

import click
import yaml
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).parent.parent / "datasets" / "linkedin_paul_iusztin"
PROFILES_DIR = Path(__file__).parent.parent / "src" / "writing" / "profiles"

PROMPT_LABEL = """
You are an expert LinkedIn content evaluator. Your job is to compare a generated
LinkedIn post against the original ground truth post and determine if the
generated version is acceptable.

You have access to the writing profiles that define the quality constraints.
Use them to judge the generated post.

**IMPORTANT GUIDELINES FOR LABELING:**

- LinkedIn writing is highly subjective. Leave room for creativity and exploration.
- Do NOT flag minor stylistic differences, word choice variations, or different
  paragraph orderings. These are acceptable creative variations.
- Flag as "fail" ONLY for major violations:
  - Uses banned AI slop expressions from the terminology profile
  - Completely misses the core topic or key points of the ground truth
  - Violates major structural rules (e.g., way too long, no hook, no CTA)
  - Sounds robotic/corporate when the character profile demands direct/casual
  - Fundamentally different tone (e.g., salesy when it should be authentic)
- If the generated post captures the same core message, follows the profiles
  reasonably well, and reads naturally — label it "pass" even if it's different
  from the ground truth in style or structure.

<structure_profile>
{structure_profile}
</structure_profile>

<terminology_profile>
{terminology_profile}
</terminology_profile>

<character_profile>
{character_profile}
</character_profile>

<ground_truth_post>
{ground_truth}
</ground_truth_post>

<generated_post>
{generated}
</generated_post>

Return a JSON object with:
- "label": "pass" or "fail"
- "critique": 1-3 sentences explaining why. Be specific and concise.
""".strip()


class LabelResult(BaseModel):
    label: str = Field(description="'pass' or 'fail'")
    critique: str = Field(description="1-3 sentence explanation")


class ScriptSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )
    google_api_key: SecretStr


async def label_post(
    client: genai.Client,
    ground_truth: str,
    generated: str,
    profiles: dict[str, str],
) -> LabelResult:
    """Compare a generated post against ground truth and return a label."""

    prompt = PROMPT_LABEL.format(
        structure_profile=profiles["structure"],
        terminology_profile=profiles["terminology"],
        character_profile=profiles["character"],
        ground_truth=ground_truth,
        generated=generated,
    )

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=LabelResult,
    )

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )

    return LabelResult.model_validate_json(response.text)


def load_profiles() -> dict[str, str]:
    """Load all profile markdown files."""

    return {
        "structure": (PROFILES_DIR / "structure_profile.md").read_text(
            encoding="utf-8"
        ),
        "terminology": (PROFILES_DIR / "terminology_profile.md").read_text(
            encoding="utf-8"
        ),
        "character": (PROFILES_DIR / "character_profile.md").read_text(
            encoding="utf-8"
        ),
    }


@click.command()
@click.option("--slug", default=None, help="Label only this slug (default: all)")
def main(slug: str | None) -> None:
    """Label the dataset by comparing generated posts to ground truth."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    settings = ScriptSettings()
    client = genai.Client(api_key=settings.google_api_key.get_secret_value())
    profiles = load_profiles()

    # Load index
    index_path = DATASET_DIR / "index.yaml"
    entries = yaml.safe_load(index_path.read_text(encoding="utf-8"))

    if slug:
        entries = [e for e in entries if e["slug"] == slug]
        if not entries:
            logger.error(f"Slug not found: {slug}")
            return

    logger.info(f"Labeling {len(entries)} posts...")

    pass_count = 0
    fail_count = 0
    skipped = 0

    for i, entry in enumerate(entries):
        entry_slug = entry["slug"]
        logger.info(f"[{i + 1}/{len(entries)}] {entry_slug}")

        # Skip if already labeled
        if "label" in entry and entry["label"] is not None:
            logger.info(f"  Already labeled: {entry['label']}")
            if entry["label"] == "pass":
                pass_count += 1
            else:
                fail_count += 1
            continue

        # Load posts
        gt_path = DATASET_DIR / f"{entry_slug}.md"
        gen_path = DATASET_DIR / f"{entry_slug}_generated.md"

        if not gt_path.exists() or not gen_path.exists():
            logger.warning("  Missing ground truth or generated post, skipping")
            skipped += 1
            continue

        ground_truth = gt_path.read_text(encoding="utf-8")
        generated = gen_path.read_text(encoding="utf-8")

        result = asyncio.run(label_post(client, ground_truth, generated, profiles))

        entry["label"] = result.label
        entry["critique"] = result.critique

        icon = "✓" if result.label == "pass" else "✗"
        logger.info(f"  {icon} {result.label}: {result.critique}")

        if result.label == "pass":
            pass_count += 1
        else:
            fail_count += 1

    # Save updated index
    header = "# Dataset Index - 20 sampled LinkedIn posts (>150 engagement, last 6 months)\n\n"
    yaml_content = yaml.dump(
        entries, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    index_path.write_text(header + yaml_content, encoding="utf-8")

    logger.info(f"\nUpdated {index_path}")
    logger.info(
        f"Results: {pass_count} pass, {fail_count} fail, {skipped} skipped "
        f"out of {len(entries)}"
    )


if __name__ == "__main__":
    main()
