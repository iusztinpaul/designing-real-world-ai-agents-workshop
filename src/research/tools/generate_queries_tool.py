"""Query generation tool implementation."""

import logging
from typing import Any

from research.app.query_handler import generate_queries
from research.config.constants import (
    MEMORY_FOLDER,
    QUERIES_FILE,
    RESEARCH_RESULTS_FILE,
    SEED_EXTRACTION_FILE,
    TRANSCRIPTS_FOLDER,
)
from research.utils.file_utils import (
    ensure_memory_dir,
    load_json,
    read_file,
    save_json,
    validate_directory,
)

logger = logging.getLogger(__name__)


async def generate_queries_tool(working_dir: str, n_queries: int = 2) -> dict[str, Any]:
    """Generate research queries that fill knowledge gaps.

    Analyzes the seed context, past research results, and YouTube transcripts
    to identify gaps and propose new web-search questions.

    Args:
        working_dir: Path to the working directory containing .memory/ data.
        n_queries: Number of queries to generate (default: 2).

    Returns:
        Dict with status, generated queries, and output file path.
    """

    validate_directory(working_dir)
    memory_path = ensure_memory_dir(working_dir)

    # Load seed context
    seed_data = load_json(memory_path / SEED_EXTRACTION_FILE)
    seed_context = seed_data.get("raw_context", "")

    # Load past research results
    research_results = load_json(memory_path / RESEARCH_RESULTS_FILE, default=[])
    past_research = ""
    if research_results:
        parts = []
        for r in research_results:
            parts.append(f"Query: {r.get('query', '')}\nAnswer: {r.get('answer', '')}")
        past_research = "\n\n---\n\n".join(parts)

    # Load YouTube transcripts
    transcripts_dir = memory_path / TRANSCRIPTS_FOLDER
    youtube_transcripts = ""
    if transcripts_dir.exists():
        transcript_parts = []
        for md_file in sorted(transcripts_dir.glob("*.md")):
            content = read_file(md_file)
            if content:
                transcript_parts.append(content)
        youtube_transcripts = "\n\n---\n\n".join(transcript_parts)

    queries = await generate_queries(
        seed_context=seed_context,
        past_research=past_research,
        youtube_transcripts=youtube_transcripts,
        n_queries=n_queries,
    )

    # Save queries
    queries_data = [q.model_dump() for q in queries]
    output_path = memory_path / QUERIES_FILE
    save_json(output_path, queries_data)

    # Format for display
    display_lines = []
    for i, q in enumerate(queries, 1):
        display_lines.append(f"{i}. {q.query}\n   Reason: {q.reason}")
    queries_display = "\n\n".join(display_lines)

    return {
        "status": "success",
        "queries_count": len(queries),
        "queries": queries_data,
        "output_path": str(output_path.resolve()),
        "message": (
            f"Generated {len(queries)} research queries. "
            f"Saved to {MEMORY_FOLDER}/{QUERIES_FILE}\n\n{queries_display}"
        ),
    }
