"""Pydantic schemas for grounded research results."""

from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    """A single grounded source returned by Gemini search."""

    url: str
    title: str = ""
    snippet: str = ""


class ResearchResult(BaseModel):
    """The result of a single grounded research query."""

    query: str
    answer: str
    sources: list[ResearchSource] = Field(default_factory=list)
