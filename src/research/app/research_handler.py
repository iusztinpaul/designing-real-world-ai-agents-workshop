"""Gemini grounded search logic."""

import logging

from research.config.prompts import PROMPT_RESEARCH
from research.models.schemas import ResearchResult, ResearchSource
from research.utils.llm import call_gemini_search

logger = logging.getLogger(__name__)


async def run_grounded_search(query: str) -> ResearchResult:
    """Run a Gemini grounded search for a single query.

    Uses Google Search grounding to get a comprehensive answer with source citations.

    Args:
        query: The research query to search for.

    Returns:
        A ResearchResult with the answer and extracted sources.
    """

    prompt = PROMPT_RESEARCH.format(query=query)

    answer_text, raw_sources = await call_gemini_search(prompt)

    sources = [
        ResearchSource(
            url=src["url"],
            title=src.get("title", ""),
            snippet="",
        )
        for src in raw_sources
    ]

    return ResearchResult(
        query=query,
        answer=answer_text,
        sources=sources,
    )
