"""Grounded search logic with configurable search provider."""

import logging

from research.config.prompts import PROMPT_RESEARCH
from research.config.settings import get_settings
from research.models.schemas import ResearchResult, ResearchSource
from research.utils.llm import call_gemini_search, call_tavily_search

logger = logging.getLogger(__name__)


def _build_sources(raw_sources: list[dict[str, str]]) -> list[ResearchSource]:
    """Convert raw source dicts into typed Pydantic ResearchSource objects."""

    return [
        ResearchSource(
            url=src["url"],
            title=src.get("title", ""),
            snippet="",
        )
        for src in raw_sources
    ]


async def run_grounded_search(query: str) -> ResearchResult:
    """Run a grounded search for a single query using the configured provider.

    Dispatches to Google Search grounding, Tavily, or both based on
    the ``research_search_provider`` setting.

    Args:
        query: The research query to search for.

    Returns:
        A ResearchResult with the answer and extracted sources.
    """

    settings = get_settings()
    provider = settings.research_search_provider.lower()

    # Wrap the raw query in the research prompt template, which adds
    # instructions for the LLM to provide a detailed, well-sourced answer.
    prompt = PROMPT_RESEARCH.format(query=query)

    if provider == "tavily":
        answer_text, raw_sources = await call_tavily_search(query)
    elif provider == "both":
        # Run both providers and merge results.
        gemini_answer, gemini_sources = await call_gemini_search(prompt)
        tavily_answer, tavily_sources = await call_tavily_search(query)

        answer_text = f"{gemini_answer}\n\n{tavily_answer}"

        # Merge and deduplicate sources by URL.
        seen_urls: set[str] = set()
        raw_sources: list[dict[str, str]] = []
        for src in gemini_sources + tavily_sources:
            if src["url"] not in seen_urls:
                seen_urls.add(src["url"])
                raw_sources.append(src)
    else:
        # Default: google
        answer_text, raw_sources = await call_gemini_search(prompt)

    sources = _build_sources(raw_sources)

    # Package everything into a structured ResearchResult model
    return ResearchResult(
        query=query,
        answer=answer_text,
        sources=sources,
    )
