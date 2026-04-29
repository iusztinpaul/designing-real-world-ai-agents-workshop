"""Markdown formatting utilities for the Deep Research MCP server."""

import logging

logger = logging.getLogger(__name__)


def markdown_collapsible(title: str, body: str) -> str:
    """Return an HTML-style collapsible block.

    Args:
        title: The text shown in the <summary> element.
        body: The content placed inside the <details> block.

    Returns:
        A string of the form:
            <details>
            <summary>{title}</summary>

            {body.strip()}

            </details>
    """
    return f"<details>\n<summary>{title}</summary>\n\n{body.strip()}\n\n</details>"


def build_research_results_section(results: list[dict]) -> str:
    """Build the ## Research Results section from a list of research result dicts.

    Each dict is expected to have:
        - ``query`` (str): The research query.
        - ``answer`` (str): The Gemini answer text.
        - ``sources`` (list[dict]): Each source has ``url`` and ``title``.

    Args:
        results: List of research result dicts.

    Returns:
        A Markdown string containing one collapsible <details> block per query.
        When ``results`` is empty, returns the empty placeholder.
    """
    if not results:
        return "## Research Results\n\n_No research results found._\n"

    blocks: list[str] = []
    for item in results:
        query = item.get("query", "")
        answer = item.get("answer", "")
        sources: list[dict] = item.get("sources", [])

        body_parts = [answer]

        if sources:
            source_lines = ["", "**Sources:**"]
            for src in sources:
                title = src.get("title", "") or src.get("url", "")
                url = src.get("url", "")
                source_lines.append(f"- [{title}]({url})")
            body_parts.append("\n".join(source_lines))

        body = "\n\n".join(body_parts)
        blocks.append(markdown_collapsible(title=query, body=body))

    return "## Research Results\n\n" + "\n".join(blocks) + "\n"


def build_sources_section(
    section_title: str,
    sources: list[tuple[str, str]],
    empty_message: str,
) -> str:
    """Build a generic Markdown section from a list of (title, body) tuples.

    Used by the YouTube Video Transcripts section and any other section that
    renders a list of collapsible blocks.

    Args:
        section_title: The ``##`` heading for this section (e.g. "## YouTube Video Transcripts").
        sources: List of (title, body) tuples; each pair becomes one <details> block.
        empty_message: Italicised placeholder shown when ``sources`` is empty.

    Returns:
        A Markdown string for the section.
    """
    if not sources:
        return f"{section_title}\n\n{empty_message}\n"

    blocks = [markdown_collapsible(title=title, body=body) for title, body in sources]
    return section_title + "\n\n" + "\n".join(blocks) + "\n"


def combine_research_sections(*sections: str) -> str:
    """Join multiple Markdown sections under a single ``# Research`` header.

    Args:
        *sections: Any number of pre-formatted Markdown section strings.

    Returns:
        A string of the form ``# Research\\n\\n<section1>\\n\\n<section2>\\n…``.
    """
    return "\n\n".join(["# Research", *sections])
