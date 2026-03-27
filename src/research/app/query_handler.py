"""Query generation logic."""

import logging

from research.config.prompts import PROMPT_GENERATE_QUERIES
from research.config.settings import get_settings
from research.models.schemas import GeneratedQueries, QueryAndReason
from research.utils.llm import call_gemini

logger = logging.getLogger(__name__)


async def generate_queries(
    seed_context: str,
    past_research: str,
    youtube_transcripts: str,
    n_queries: int = 2,
) -> list[QueryAndReason]:
    """Generate research queries that fill knowledge gaps.

    Args:
        seed_context: The seed document context.
        past_research: Previously collected research results (may be empty).
        youtube_transcripts: Concatenated YouTube transcripts (may be empty).
        n_queries: Number of queries to generate.

    Returns:
        A list of QueryAndReason objects.
    """

    settings = get_settings()

    prompt = PROMPT_GENERATE_QUERIES.format(
        n_queries=n_queries,
        seed_context=seed_context or "<none>",
        past_research=past_research or "<none>",
        youtube_transcripts=youtube_transcripts or "<none>",
    )

    response_text = await call_gemini(
        prompt,
        model=settings.query_generation_model,
        response_schema=GeneratedQueries,
    )
    result = GeneratedQueries.model_validate_json(response_text)

    return result.queries[:n_queries]
