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

    # Wrap the raw query in the research prompt template, which adds
    # instructions for Gemini to provide a detailed, well-sourced answer.
    prompt = PROMPT_RESEARCH.format(query=query)

    # Call Gemini with Google Search grounding enabled.
    # Returns the answer text and a list of raw source dicts (url + title)
    # extracted from the grounding metadata.
    answer_text, raw_sources = await call_gemini_search(prompt)

    # Convert raw source dicts into typed Pydantic ResearchSource objects.
    # snippet is left empty because grounding metadata doesn't provide one.
    sources = [
        ResearchSource(
            url=src["url"],
            title=src.get("title", ""),
            snippet="",
        )
        for src in raw_sources
    ]

    # Package everything into a structured ResearchResult model
    return ResearchResult(
        query=query,
        answer=answer_text,
        sources=sources,
    )
