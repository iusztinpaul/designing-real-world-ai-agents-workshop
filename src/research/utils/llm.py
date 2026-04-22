"""Gemini client helpers for LLM interactions."""

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tavily import AsyncTavilyClient

from google import genai
from google.genai import types
from pydantic import BaseModel

from research.config.settings import get_settings
from research.utils.opik_utils import track_genai_client

logger = logging.getLogger(__name__)


# Singleton pattern: lru_cache ensures only one Gemini client is created
# across the entire application lifetime.
@lru_cache
def get_client() -> genai.Client:
    """Create and cache a Gemini client, with Opik tracking if configured."""

    settings = get_settings()
    # Initialize the Gemini client with the API key from settings.
    # get_secret_value() unwraps the Pydantic SecretStr to a plain string.
    client = genai.Client(api_key=settings.google_api_key.get_secret_value())

    # Wrap the client with Opik observability tracking (if configured),
    # so all LLM calls are automatically logged for monitoring/evals.
    return track_genai_client(client)


async def call_gemini(
    prompt: str,
    model: str | None = None,
    response_schema: type[BaseModel] | None = None,
    system_instruction: str | None = None,
) -> str:
    """Call Gemini with optional structured output.

    Args:
        prompt: The prompt to send to Gemini.
        model: Model name override. Defaults to settings.gemini_model.
        response_schema: If provided, Gemini returns JSON matching this Pydantic model.
        system_instruction: Optional system instruction for the model.

    Returns:
        The response text from Gemini.
    """

    settings = get_settings()
    client = get_client()
    # Use the provided model or fall back to the default from settings
    model_name = model or settings.gemini_model

    # Build config kwargs dynamically based on which options are provided
    config_kwargs: dict[str, Any] = {}
    if response_schema is not None:
        # When a Pydantic schema is given, tell Gemini to return structured JSON
        # that conforms to the schema (instead of free-form text)
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = response_schema
    if system_instruction is not None:
        config_kwargs["system_instruction"] = system_instruction

    # Only create a config object if we have options to set; otherwise pass None
    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    # Make the async API call to Gemini via the google-genai SDK.
    # client.aio provides the async interface for non-blocking calls.
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )

    return response.text


async def call_gemini_search(
    prompt: str,
    model: str | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """Call Gemini with Google Search grounding.

    Google Search grounding and structured output cannot be used simultaneously,
    so this function returns raw text + programmatically extracted sources.

    Args:
        prompt: The search prompt to send to Gemini.
        model: Model name override. Defaults to settings.gemini_model.

    Returns:
        A tuple of (answer_text, sources_list) where sources_list contains
        dicts with 'url' and 'title' keys.
    """

    settings = get_settings()
    client = get_client()
    model_name = model or settings.gemini_model

    # Enable Google Search grounding — this tells Gemini to search the live web
    # before generating a response, producing answers backed by real-time sources.
    # Note: grounding and structured output (response_schema) are mutually exclusive
    # in the Gemini API, which is why this is a separate function from call_gemini.
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )

    # Extract the text answer (fallback to empty string if None)
    answer_text = response.text or ""
    # Parse the grounding metadata to extract deduplicated source URLs/titles
    sources = extract_grounding_sources(response)

    return answer_text, sources


@lru_cache
def get_tavily_client() -> "AsyncTavilyClient":
    """Create and cache an async Tavily client."""

    from tavily import AsyncTavilyClient

    settings = get_settings()
    if not settings.tavily_api_key:
        raise ValueError(
            "TAVILY_API_KEY must be set when using the tavily search provider"
        )

    return AsyncTavilyClient(api_key=settings.tavily_api_key.get_secret_value())


async def call_tavily_search(
    query: str,
) -> tuple[str, list[dict[str, str]]]:
    """Call Tavily search API and return results in the same shape as call_gemini_search.

    Args:
        query: The search query to send to Tavily.

    Returns:
        A tuple of (answer_text, sources_list) where sources_list contains
        dicts with 'url' and 'title' keys.
    """

    client = get_tavily_client()

    response = await client.search(
        query=query,
        max_results=10,
        search_depth="advanced",
        include_answer="advanced",
    )

    answer_text = response.get("answer", "") or ""
    sources = [
        {"url": r["url"], "title": r.get("title", "")}
        for r in response.get("results", [])
        if r.get("url")
    ]

    return answer_text, sources


def extract_grounding_sources(
    response: types.GenerateContentResponse,
) -> list[dict[str, str]]:
    """Extract source URLs and titles from grounding metadata.

    Args:
        response: The Gemini response object.

    Returns:
        A list of dicts with 'url' and 'title' keys.
    """

    sources: list[dict[str, str]] = []
    # Track seen URLs to deduplicate (Gemini may cite the same source multiple times)
    seen_urls: set[str] = set()

    # Early return if the response has no candidates (e.g. blocked by safety filters)
    if not response.candidates:
        return sources

    # Only look at the first candidate (Gemini typically returns one)
    candidate = response.candidates[0]

    # Navigate the nested grounding metadata structure safely using getattr,
    # since these attributes may not exist depending on the response type.
    grounding_metadata = getattr(candidate, "grounding_metadata", None)
    if grounding_metadata is None:
        return sources

    grounding_chunks = getattr(grounding_metadata, "grounding_chunks", None)
    if grounding_chunks is None:
        return sources

    # Each grounding chunk may contain a "web" object with a URI and title.
    # We extract these and deduplicate by URL.
    for chunk in grounding_chunks:
        web = getattr(chunk, "web", None)
        if web is None:
            continue
        url = getattr(web, "uri", "") or ""
        title = getattr(web, "title", "") or ""
        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append({"url": url, "title": title})

    return sources
