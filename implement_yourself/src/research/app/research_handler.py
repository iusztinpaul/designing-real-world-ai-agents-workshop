"""Business logic handler for grounded Gemini search queries."""

import logging

from research.config.prompts import PROMPT_RESEARCH
from research.models.schemas import ResearchResult, ResearchSource
from research.utils.llm import call_gemini_search

logger = logging.getLogger(__name__)


async def run_grounded_search(query: str) -> ResearchResult:
    """Run a grounded Gemini search for the given query.

    Formats the PROMPT_RESEARCH template, calls call_gemini_search, and
    converts the returned raw source dicts into ResearchSource objects.

    Args:
        query: The research query or topic to investigate.

    Returns:
        A ResearchResult containing the query, the Gemini answer text,
        and a list of grounding sources.
    """
    prompt = PROMPT_RESEARCH.format(query=query)
    logger.info("Running grounded search for query: %s", query)

    answer_text, raw_sources = await call_gemini_search(prompt)

    sources = [
        ResearchSource(url=src["url"], title=src.get("title", ""), snippet="")
        for src in raw_sources
    ]

    logger.info(
        "Grounded search complete: query=%r answer_len=%d sources=%d",
        query,
        len(answer_text),
        len(sources),
    )

    return ResearchResult(query=query, answer=answer_text, sources=sources)
