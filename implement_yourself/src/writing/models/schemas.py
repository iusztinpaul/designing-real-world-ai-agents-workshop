"""Pydantic schemas for the LinkedIn Writer MCP server."""

from pydantic import BaseModel, Field


class Profile(BaseModel):
    """A single writing profile loaded from a markdown file."""

    name: str
    content: str


class Profiles(BaseModel):
    """Container for all four writing profiles."""

    structure: Profile
    terminology: Profile
    character: Profile
    branding: Profile


class Post(BaseModel):
    """A LinkedIn post with its text content."""

    content: str


class Review(BaseModel):
    """A single review comment on a post — placeholder for #013."""

    profile: str
    location: str
    comment: str


class PostReviews(BaseModel):
    """Collection of reviews for one review iteration — placeholder for #013."""

    reviews: list[Review] = Field(default_factory=list)


class GeneratePostResult(BaseModel):
    """Result of the full post generation pipeline."""

    post: Post
    versions: list[Post] = Field(default_factory=list)
    reviews: list[PostReviews] = Field(default_factory=list)
