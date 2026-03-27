"""Dataset loader for LinkedIn posts with Pydantic models."""

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DATASET_DIR = (
    Path(__file__).parent.parent.parent.parent / "datasets" / "linkedin_paul_iusztin"
)


class DatasetEntry(BaseModel):
    """A single entry in the LinkedIn posts dataset."""

    slug: str
    local_post: str
    local_media: list[str] | None = None
    scope: list[str] | None = None

    def post_content(self, base_dir: Path) -> str:
        """Read the post text content."""

        path = base_dir / self.local_post.lstrip("./")
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def media_paths(self, base_dir: Path) -> list[Path]:
        """Resolve media file paths."""

        if not self.local_media:
            return []
        return [
            base_dir / m.lstrip("./")
            for m in self.local_media
            if (base_dir / m.lstrip("./")).exists()
        ]


class PostExample(BaseModel):
    """A few-shot example post for the writer."""

    slug: str
    content: str


class MediaExample(BaseModel):
    """A few-shot example media for the image generator."""

    slug: str
    media_path: Path


class DatasetExamples(BaseModel):
    """Container for few-shot examples loaded from the dataset."""

    post_examples: list[PostExample] = Field(default_factory=list)
    media_examples: list[MediaExample] = Field(default_factory=list)

    def format_post_examples(self) -> str:
        """Format post examples as text for prompt injection."""

        if not self.post_examples:
            return "<none>"

        parts: list[str] = []
        for i, ex in enumerate(self.post_examples, 1):
            parts.append(f"--- Example {i} ---\n{ex.content}\n--- End Example {i} ---")

        return "\n\n".join(parts)


def load_dataset() -> list[DatasetEntry]:
    """Load the full dataset index."""

    index_path = DATASET_DIR / "index.yaml"
    if not index_path.exists():
        logger.warning(f"Dataset index not found: {index_path}")
        return []

    raw = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    return [DatasetEntry(**entry) for entry in raw]


def load_examples() -> DatasetExamples:
    """Load few-shot examples from the dataset based on the scope field.

    - scope contains 'train_generator' → used as post text examples
    - scope contains 'train_image_generator' → used as media examples

    Returns:
        DatasetExamples with deterministic, always-identical examples.
    """

    entries = load_dataset()

    post_examples: list[PostExample] = []
    media_examples: list[MediaExample] = []

    for entry in entries:
        if not entry.scope:
            continue

        if "train_generator" in entry.scope:
            content = entry.post_content(DATASET_DIR)
            if content:
                post_examples.append(PostExample(slug=entry.slug, content=content))

        if "train_image_generator" in entry.scope:
            paths = entry.media_paths(DATASET_DIR)
            if paths:
                media_examples.append(
                    MediaExample(slug=entry.slug, media_path=paths[0])
                )

    return DatasetExamples(
        post_examples=post_examples,
        media_examples=media_examples,
    )
