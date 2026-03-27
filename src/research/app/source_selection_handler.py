"""Source selection operations."""

import logging

from research.config.prompts import PROMPT_SELECT_SOURCES
from research.config.settings import get_settings
from research.models.schemas import SelectedSources
from research.utils.llm import call_gemini

logger = logging.getLogger(__name__)


def build_sources_data_text(results: list[dict]) -> str:
    """Format research results into a text block for the selection prompt."""

    lines: list[str] = []
    source_id = 1
    for result in results:
        query = result.get("query", "")
        sources = result.get("sources", [])
        for src in sources:
            url = src.get("url", "")
            title = src.get("title", url)
            snippet = src.get("snippet", "")
            lines.append(f"### Source {source_id}: {url}")
            lines.append(f"**Title:** {title}")
            lines.append(f"**Query:** {query}")
            if snippet:
                lines.append(f"**Snippet:** {snippet}")
            lines.append("---")
            lines.append("")
            source_id += 1

    return "\n".join(lines)


async def select_sources(
    seed_context: str,
    research_results: list[dict],
) -> SelectedSources:
    """Use Gemini to select the best subset of sources from research results.

    Args:
        seed_context: The seed document context for relevance evaluation.
        research_results: List of research result dicts.

    Returns:
        A SelectedSources object with filtered sources and reasoning.
    """

    settings = get_settings()
    sources_data_text = build_sources_data_text(research_results)

    if not sources_data_text.strip():
        return SelectedSources(
            selected_sources=[], reasoning="No sources available to select from."
        )

    prompt = PROMPT_SELECT_SOURCES.format(
        seed_context=seed_context or "<none>",
        sources_data=sources_data_text,
    )

    response_text = await call_gemini(
        prompt,
        model=settings.source_selection_model,
        response_schema=SelectedSources,
    )
    result = SelectedSources.model_validate_json(response_text)

    logger.info(f"{len(result.selected_sources)} sources selected.")

    return result


def merge_selected_sources(
    existing: list[dict], new_selection: SelectedSources
) -> list[dict]:
    """Merge newly selected sources into the existing selected list, deduplicating by URL."""

    seen_urls: set[str] = {s.get("url", "") for s in existing}
    merged = list(existing)
    for src in new_selection.selected_sources:
        if src.url not in seen_urls:
            seen_urls.add(src.url)
            merged.append(src.model_dump())

    return merged
