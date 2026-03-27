"""Pydantic models for research operations."""

from pydantic import BaseModel, Field


class SeedExtraction(BaseModel):
    """Structured extraction from a seed document."""

    youtube_urls: list[str] = Field(
        default_factory=list, description="YouTube video URLs found in the seed"
    )
    topics: list[str] = Field(
        default_factory=list, description="Main topics and themes to research"
    )
    research_questions: list[str] = Field(
        default_factory=list,
        description="Specific questions to research",
    )


class QueryAndReason(BaseModel):
    """A single web-search query and the reason for it."""

    query: str = Field(description="The web-search question to research")
    reason: str = Field(description="Why this question is important for the research")


class GeneratedQueries(BaseModel):
    """A list of generated web-search queries and their reasons."""

    queries: list[QueryAndReason] = Field(
        description="A list of web-search queries and their reasons"
    )


class ResearchSource(BaseModel):
    """A single source from research results."""

    url: str = Field(description="The URL of the source")
    title: str = Field(default="", description="Title of the source")
    snippet: str = Field(default="", description="Relevant excerpt from the source")


class ResearchResult(BaseModel):
    """A single research result from a grounded search."""

    query: str = Field(description="The query that produced this result")
    answer: str = Field(description="The research answer")
    sources: list[ResearchSource] = Field(
        default_factory=list, description="Sources cited in the answer"
    )


class SelectedSources(BaseModel):
    """Result of source selection/filtering."""

    selected_sources: list[ResearchSource] = Field(
        description="Sources that passed quality filtering"
    )
    reasoning: str = Field(description="Explanation of the selection strategy")
