"""Final research.md compilation logic."""

import logging
from pathlib import Path

from research.config.constants import (
    NOVA_FOLDER,
    RESEARCH_RESULTS_FILE,
    SELECTED_SOURCES_FILE,
    TRANSCRIPTS_FOLDER,
)
from research.utils.file_utils import load_json, read_file
from research.utils.markdown_utils import (
    build_research_results_section,
    build_sources_section,
    combine_research_sections,
)

logger = logging.getLogger(__name__)


def compile_research_file(working_dir: str) -> str:
    """Compile all research data into a final markdown document.

    Reads all intermediate files from .nova/ and assembles them into a
    structured research.md with collapsible sections.

    Args:
        working_dir: Path to the working directory.

    Returns:
        The complete markdown document as a string.
    """

    nova_path = Path(working_dir) / NOVA_FOLDER

    # Load research results
    research_results = load_json(nova_path / RESEARCH_RESULTS_FILE, default=[])

    # Load selected sources
    selected_sources = load_json(nova_path / SELECTED_SOURCES_FILE, default=[])

    # Load YouTube transcripts
    transcripts_dir = nova_path / TRANSCRIPTS_FOLDER
    youtube_sources: list[tuple[str, str]] = []
    if transcripts_dir.exists():
        for md_file in sorted(transcripts_dir.glob("*.md")):
            content = read_file(md_file)
            if content:
                title = md_file.stem
                youtube_sources.append((title, content))

    # Build sections
    research_results_section = build_research_results_section(research_results)

    # Build selected sources section
    selected_source_items: list[tuple[str, str]] = []
    for src in selected_sources:
        title = src.get("title", src.get("url", "Unknown"))
        snippet = src.get("snippet", "")
        url = src.get("url", "")
        body = f"**URL:** {url}\n\n{snippet}" if snippet else f"**URL:** {url}"
        selected_source_items.append((title, body))

    selected_sources_section = build_sources_section(
        "## Selected Sources",
        selected_source_items,
        "No selected sources found.",
    )

    youtube_section = build_sources_section(
        "## YouTube Video Transcripts",
        youtube_sources,
        "No YouTube video transcripts found.",
    )

    return combine_research_sections(
        research_results_section,
        selected_sources_section,
        youtube_section,
    )
