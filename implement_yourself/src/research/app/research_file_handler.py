"""Research file handler: reads accumulated research data and compiles Markdown."""

import logging
from pathlib import Path

from research.config.constants import (
    MEMORY_FOLDER,
    RESEARCH_RESULTS_FILE,
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
    """Read accumulated research data and compile it into a single Markdown document.

    Reads:
        - ``<working_dir>/.memory/research_results.json`` for grounded search results.
        - All ``*.md`` files under ``<working_dir>/.memory/transcripts/`` for YouTube
          transcripts.

    If either source is missing the corresponding section uses its empty placeholder.

    Args:
        working_dir: The root working directory that contains ``.memory/``.

    Returns:
        A Markdown string starting with ``# Research`` that combines the Research
        Results section and the YouTube Video Transcripts section.
    """
    memory_path = Path(working_dir) / MEMORY_FOLDER

    # ------------------------------------------------------------------ #
    # Section 1: Research Results                                          #
    # ------------------------------------------------------------------ #
    results_path = memory_path / RESEARCH_RESULTS_FILE
    results: list[dict] = load_json(results_path, default=[])
    logger.info("Loaded %d research result(s) from %s", len(results), results_path)

    research_section = build_research_results_section(results)

    # ------------------------------------------------------------------ #
    # Section 2: YouTube Video Transcripts                                 #
    # ------------------------------------------------------------------ #
    transcripts_dir = memory_path / TRANSCRIPTS_FOLDER
    transcript_pairs: list[tuple[str, str]] = []

    if transcripts_dir.is_dir():
        for md_file in sorted(transcripts_dir.glob("*.md")):
            title = md_file.stem
            body = read_file(md_file)
            transcript_pairs.append((title, body))
            logger.info("Loaded transcript: %s (%d bytes)", md_file.name, len(body))
    else:
        logger.debug(
            "Transcripts directory not found: %s — using empty placeholder",
            transcripts_dir,
        )

    youtube_section = build_sources_section(
        section_title="## YouTube Video Transcripts",
        sources=transcript_pairs,
        empty_message="_No YouTube video transcripts found._",
    )

    return combine_research_sections(research_section, youtube_section)
