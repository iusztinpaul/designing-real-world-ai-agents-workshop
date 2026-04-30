"""Streamlit chat UI orchestrating the deep-research and linkedin-writer MCP servers.

Run with:
    make run-ui
    # or directly:
    uv run streamlit run streamlit_app.py
"""

import asyncio
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import google.genai as genai
import streamlit as st
from fastmcp import Client
from pydantic import BaseModel, Field as PydanticField

# ---------------------------------------------------------------------------
# sys.path shim — makes `from writing.config.settings import get_settings` work
# ---------------------------------------------------------------------------
_SRC = str(Path(__file__).parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from writing.config.settings import get_settings  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.resolve()
RESEARCH_SERVER = str(REPO_ROOT / "src" / "research" / "server.py")
WRITING_SERVER = str(REPO_ROOT / "src" / "writing" / "server.py")
OUTPUTS_DIR = REPO_ROOT / "outputs"

DECOMPOSE_PROMPT = (
    "Break the following topic into 3-5 distinct, focused research queries suitable "
    "for separate web searches. Each query should explore a different facet of the topic. "
    "Return only the list of queries, nothing else.\n\nTopic: {topic}"
)

GUIDELINE_PROMPT = (
    "Draft a concise LinkedIn post guideline in markdown with the following H2 sections: "
    "## Topic, ## Angle, ## Target Audience, ## Key Points, ## Tone. "
    "Keep the total under 200 words. Base it on the following topic.\n\nTopic: {topic}"
)

# ---------------------------------------------------------------------------
# Indeterminate progress bar CSS + helper
# ---------------------------------------------------------------------------
INDETERMINATE_BAR_CSS = """
<style>
@keyframes shimmer {
    0%   { background-position: -600px 0; }
    100% { background-position: 600px 0; }
}
.indeterminate-bar {
    width: 100%;
    height: 8px;
    border-radius: 4px;
    background: linear-gradient(
        90deg,
        #e0e0e0 25%,
        #bdbdbd 50%,
        #e0e0e0 75%
    );
    background-size: 600px 100%;
    animation: shimmer 1.4s infinite linear;
    margin: 4px 0 8px 0;
}
.indeterminate-label {
    font-size: 0.85rem;
    color: #555;
    margin-bottom: 2px;
}
</style>
"""


def indeterminate_bar_html(label: str) -> str:
    """Return an indeterminate shimmer bar HTML fragment with a label."""
    return (
        f'<div class="indeterminate-label">{label}</div>'
        '<div class="indeterminate-bar"></div>'
    )


# ---------------------------------------------------------------------------
# Pydantic schema + helpers
# ---------------------------------------------------------------------------


class ResearchQueries(BaseModel):
    """Structured output schema for topic decomposition."""

    queries: list[str] = PydanticField(min_length=2, max_length=6)


def slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a URL-friendly slug.

    Lowercases the text, replaces spaces and non-alphanumeric characters with
    hyphens, collapses repeated hyphens, and trims to max_len.
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_len]


def unwrap(result: object) -> dict:
    """Extract the dict payload from a FastMCP CallToolResult.

    FastMCP's Client.call_tool returns a CallToolResult with a `.data`
    attribute that may be a dict, or may fall back to a content list.
    Tolerate both shapes.
    """
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    # Structured content fallback
    sc = getattr(result, "structured_content", None)
    if isinstance(sc, dict):
        return sc
    # Last resort: try to decode the first text content block
    content = getattr(result, "content", [])
    if content:
        raw = getattr(content[0], "text", "")
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"raw": raw}
    return {}


def gemini_client() -> genai.Client:
    """Return a new Gemini client using the API key from settings."""
    settings = get_settings()
    return genai.Client(api_key=settings.google_api_key.get_secret_value())


# ---------------------------------------------------------------------------
# Stage view dataclasses (own st.empty() placeholders)
# ---------------------------------------------------------------------------


@dataclass
class ResearchStageView:
    """Manages the live-updating research progress display."""

    _header_slot: object = field(default=None, init=False)
    _counter_slot: object = field(default=None, init=False)
    _rows_slot: object = field(default=None, init=False)
    _compile_slot: object = field(default=None, init=False)

    # internal state
    _queries: list[str] = field(default_factory=list, init=False)
    _statuses: list[str] = field(
        default_factory=list, init=False
    )  # pending/running/done
    _sources: list[int] = field(default_factory=list, init=False)
    _total_sources: int = field(default=0, init=False)
    _done_count: int = field(default=0, init=False)

    def render_init(self, queries: list[str]) -> None:
        """Write the initial research stage scaffold into the parent container."""
        self._queries = queries
        self._statuses = ["pending"] * len(queries)
        self._sources = [0] * len(queries)

        self._header_slot = st.empty()
        self._counter_slot = st.empty()
        self._rows_slot = st.empty()
        self._compile_slot = st.empty()

        self._header_slot.markdown("### 🔎 Deep research")
        self._counter_slot.markdown(
            f"**0 / {len(queries)} searches done · 0 sources collected**"
        )
        self._rows_slot.markdown("\n".join(f"⚪️ {q}" for q in queries))

    def update(self, idx: int, *, status: str, sources: int = 0) -> None:
        """Flip query at *idx* to the given status and refresh counters."""
        self._statuses[idx] = status
        if status == "done":
            self._sources[idx] = sources
            self._total_sources += sources
            self._done_count += 1

        icon_map = {"pending": "⚪️", "running": "🟡", "done": "🟢"}

        rows = []
        for i, q in enumerate(self._queries):
            icon = icon_map.get(self._statuses[i], "⚪️")
            suffix = (
                f" — {self._sources[i]} sources" if self._statuses[i] == "done" else ""
            )
            rows.append(f"{icon} {q}{suffix}")

        self._rows_slot.markdown("\n".join(rows))
        self._counter_slot.markdown(
            f"**{self._done_count} / {len(self._queries)} searches done "
            f"· {self._total_sources} sources collected**"
        )

    def compile_running(self) -> None:
        """Show a compile-in-progress indicator."""
        self._compile_slot.markdown("📚 _Compiling research.md..._")

    def compile_done(self, output_path: str) -> None:
        """Replace the compile indicator with a success message."""
        size = Path(output_path).stat().st_size if Path(output_path).exists() else 0
        self._compile_slot.success(
            f"✅ research.md generated ({size:,} bytes) → `{output_path}`"
        )


@dataclass
class WritingStageView:
    """Manages the live-updating writing workflow display."""

    _header_slot: object = field(default=None, init=False)
    _progress_slot: object = field(default=None, init=False)
    _post_slot: object = field(default=None, init=False)
    _image_running_slot: object = field(default=None, init=False)
    _image_slot: object = field(default=None, init=False)

    def render_init(self, num_reviews: int) -> None:
        """Write the initial writing stage scaffold."""
        self._header_slot = st.empty()
        self._progress_slot = st.empty()
        self._post_slot = st.empty()
        self._image_running_slot = st.empty()
        self._image_slot = st.empty()

        self._header_slot.markdown("### ✍️ Writing workflow")
        self._post_slot.caption(
            f"Evaluator-optimizer loop · up to {num_reviews} review/edit iterations"
        )

    def writing_running(self) -> None:
        """Paint the indeterminate bar for the writing stage."""
        self._progress_slot.markdown(
            indeterminate_bar_html("Running evaluator-optimizer loop..."),
            unsafe_allow_html=True,
        )

    def writing_done(self, post_text: str, post_path: str) -> None:
        """Flip the bar to success and show the post in an expander."""
        self._progress_slot.success("✅ Post finalized")
        with self._post_slot.expander("📄 View post", expanded=False):
            st.markdown(post_text)

    def image_running(self) -> None:
        """Paint the indeterminate bar for the image generation stage."""
        self._image_running_slot.markdown(
            indeterminate_bar_html("Generating image with Gemini Flash Image..."),
            unsafe_allow_html=True,
        )

    def image_done(self, image_path: str) -> None:
        """Clear the running bar and render the generated image."""
        self._image_running_slot.empty()
        with self._image_slot.container():
            st.markdown("### 🖼️ Generated image")
            st.image(image_path, width=520)
            st.caption(f"Saved to: `{image_path}`")


# ---------------------------------------------------------------------------
# Async pipeline functions
# ---------------------------------------------------------------------------


async def decompose_topic(topic: str) -> list[str]:
    """Call Gemini to break *topic* into 3–5 distinct research queries."""
    import google.genai.types as gtypes

    client = gemini_client()
    settings = get_settings()
    prompt = DECOMPOSE_PROMPT.format(topic=topic)

    config = gtypes.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ResearchQueries,
    )
    response = await client.aio.models.generate_content(
        model=settings.writer_model,
        contents=prompt,
        config=config,
    )
    parsed = ResearchQueries.model_validate_json(response.text)
    logger.info("Decomposed topic into %d queries", len(parsed.queries))
    return parsed.queries


async def synthesize_guideline(topic: str) -> str:
    """Call Gemini to produce a markdown guideline for *topic*."""
    import google.genai.types as gtypes

    client = gemini_client()
    settings = get_settings()
    prompt = GUIDELINE_PROMPT.format(topic=topic)

    config = gtypes.GenerateContentConfig()
    response = await client.aio.models.generate_content(
        model=settings.writer_model,
        contents=prompt,
        config=config,
    )
    logger.info("Synthesized guideline (%d chars)", len(response.text))
    return response.text


async def run_research_pipeline(
    working_dir: str,
    queries: list[str],
    view: ResearchStageView,
) -> str:
    """Open the research MCP server and run all queries, then compile.

    Returns the output path of the compiled research.md.
    """
    async with Client(RESEARCH_SERVER) as client:
        view.render_init(queries)

        for idx, query in enumerate(queries):
            view.update(idx, status="running")
            result = await client.call_tool(
                "deep_research",
                {"working_dir": working_dir, "query": query},
            )
            data = unwrap(result)
            sources = data.get("total_sources", 0)
            view.update(idx, status="done", sources=sources)
            logger.info("Query %d/%d done: %d sources", idx + 1, len(queries), sources)

        view.compile_running()
        compile_result = await client.call_tool(
            "compile_research",
            {"working_dir": working_dir},
        )
        compile_data = unwrap(compile_result)
        output_path = compile_data.get(
            "output_path", str(Path(working_dir) / "research.md")
        )
        view.compile_done(output_path)
        logger.info("Compiled research to %s", output_path)
        return output_path


async def fetch_num_reviews(client: Client) -> int:
    """Read config://settings from the writing server and return num_reviews.

    Falls back to the local settings value on any error.
    """
    try:
        contents = await client.read_resource("config://settings")
        if contents:
            text = contents[0].text
            cfg = json.loads(text)
            return int(cfg.get("num_reviews", get_settings().num_reviews))
    except Exception:
        logger.exception("Failed to fetch num_reviews from writing server")
    return get_settings().num_reviews


async def run_writing_pipeline(
    working_dir: str,
    skip_image: bool,
    view: WritingStageView,
) -> dict[str, str]:
    """Open the writing MCP server, run generate_post and (optionally) generate_image.

    Returns a dict with post_path and image_path keys.
    """
    async with Client(WRITING_SERVER) as client:
        num_reviews = await fetch_num_reviews(client)
        view.render_init(num_reviews)

        view.writing_running()
        post_result = await client.call_tool(
            "generate_post",
            {"working_dir": working_dir, "delete_iterations": False},
        )
        post_data = unwrap(post_result)
        post_text = post_data.get("post", "")
        post_path = post_data.get("output_path", str(Path(working_dir) / "post.md"))
        view.writing_done(post_text, post_path)
        logger.info("Post generated at %s", post_path)

        image_path = ""
        if not skip_image:
            view.image_running()
            image_result = await client.call_tool(
                "generate_image",
                {"working_dir": working_dir},
            )
            image_data = unwrap(image_result)
            image_path = image_data.get(
                "image_path", str(Path(working_dir) / "post_image.png")
            )
            view.image_done(image_path)
            logger.info("Image generated at %s", image_path)

        return {"post_path": post_path, "image_path": image_path}


async def run_pipeline(
    topic: str,
    research_view: ResearchStageView,
    writing_view: WritingStageView,
) -> dict[str, str]:
    """Top-level orchestrator: research → writing → image.

    Returns artifact paths: working_dir, research, post, image.
    """
    slug = slugify(topic)
    working_dir = OUTPUTS_DIR / slug
    working_dir.mkdir(parents=True, exist_ok=True)

    # Persist seed
    seed_path = working_dir / "seed.md"
    seed_path.write_text(topic, encoding="utf-8")

    # Synthesize guideline
    guideline_text = await synthesize_guideline(topic)
    guideline_path = working_dir / "guideline.md"
    guideline_path.write_text(guideline_text, encoding="utf-8")
    logger.info("Guideline written to %s", guideline_path)

    # Decompose topic into queries
    queries = await decompose_topic(topic)

    # Research pipeline
    research_path = await run_research_pipeline(
        str(working_dir), queries, research_view
    )

    # Writing pipeline (hardcode skip_image=False per ticket notes)
    writing_result = await run_writing_pipeline(
        str(working_dir), skip_image=False, view=writing_view
    )

    return {
        "working_dir": str(working_dir),
        "research": research_path,
        "post": writing_result["post_path"],
        "image": writing_result["image_path"],
    }


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Research → Writer",
    page_icon="✍️",
    layout="wide",
)

# Inject CSS once
st.markdown(INDETERMINATE_BAR_CSS, unsafe_allow_html=True)

# Title + caption
st.title("✍️ Research → Writer")
st.caption(
    "End-to-end pipeline: deep research → LinkedIn post → image. "
    "Drives the deep-research and linkedin-writer MCP servers via FastMCP."
)

# Session state initialisation
st.session_state.setdefault("run_count", 0)
st.session_state.setdefault("processed_seed_file_id", None)
st.session_state.setdefault("prefill", None)

# Suggestion pills (first run only)
SUGGESTIONS = [
    "Why single agents beat multi-agent setups",
    "How LLMs reason step-by-step with chain-of-thought",
    "The future of AI agents in software engineering",
]

if st.session_state.run_count == 0:
    selected = st.pills(
        "Try a topic:",
        SUGGESTIONS,
        label_visibility="collapsed",
    )
    if selected:
        st.session_state.prefill = selected
        st.rerun()

# Two-column input row:
#   col_chat (4-wide)  | col_upload (1-wide)
# Note: st.chat_input has special fixed-bottom positioning in Streamlit and
# cannot be reliably placed inside st.columns without breaking its layout.
# As a pragmatic compromise the file uploader is placed above the chat input
# so both are reachable without harming usability.
seed_file = st.file_uploader(
    "Or upload a seed file (.md / .txt)",
    type=["md", "txt"],
    label_visibility="visible",
)

chat_input_text = st.chat_input("Paste a topic / seed text...")

# Topic resolution priority:
#   1. prefill (one-shot from suggestion pill)
#   2. typed chat input
#   3. freshly uploaded seed file (not already processed)
topic_text: str | None = None

if st.session_state.prefill:
    topic_text = st.session_state.prefill
    st.session_state.prefill = None

elif chat_input_text:
    topic_text = chat_input_text

elif (
    seed_file is not None
    and seed_file.file_id != st.session_state.processed_seed_file_id
):
    topic_text = seed_file.read().decode("utf-8", errors="replace")
    st.session_state.processed_seed_file_id = seed_file.file_id

if topic_text:
    st.session_state.run_count += 1

    # User message bubble
    with st.chat_message("user"):
        display_text = topic_text[:500] + "..." if len(topic_text) > 500 else topic_text
        if len(topic_text) > 200:
            with st.expander("Seed text"):
                st.markdown(display_text)
        else:
            st.markdown(display_text)

    # Assistant bubble containing both stage views and the footer
    with st.chat_message("assistant"):
        research_container = st.container()
        writing_container = st.container()
        footer = st.empty()

        research_view = ResearchStageView()
        writing_view = WritingStageView()

        # Inject stage views into their containers
        with research_container:
            pass  # render_init is called from inside run_pipeline
        with writing_container:
            pass  # render_init is called from inside run_pipeline

        # We need the views to render into their containers, so wrap the
        # entire pipeline inside each container using a context-manager trick.
        # The stage view render_init methods call st.empty() — they need to be
        # invoked while the right container is active.

        try:
            # Run both stages, sharing the containers
            async def _pipeline() -> dict[str, str]:
                with research_container:
                    # Research stage renders here
                    pass
                with writing_container:
                    # Writing stage renders here
                    pass
                return await run_pipeline(topic_text, research_view, writing_view)

            # Re-implement to render into the correct containers
            async def _run_with_containers() -> dict[str, str]:
                slug = slugify(topic_text)
                working_dir = OUTPUTS_DIR / slug
                working_dir.mkdir(parents=True, exist_ok=True)

                seed_path = working_dir / "seed.md"
                seed_path.write_text(topic_text, encoding="utf-8")

                guideline_text = await synthesize_guideline(topic_text)
                guideline_path = working_dir / "guideline.md"
                guideline_path.write_text(guideline_text, encoding="utf-8")

                queries = await decompose_topic(topic_text)

                with research_container:
                    research_path = await run_research_pipeline(
                        str(working_dir), queries, research_view
                    )

                with writing_container:
                    writing_result = await run_writing_pipeline(
                        str(working_dir), skip_image=False, view=writing_view
                    )

                return {
                    "working_dir": str(working_dir),
                    "research": research_path,
                    "post": writing_result["post_path"],
                    "image": writing_result["image_path"],
                }

            artifacts = asyncio.run(_run_with_containers())

            footer.markdown(
                f"### 📁 Artifacts\n"
                f"- **Working dir:** `{artifacts['working_dir']}`\n"
                f"- **research.md:** `{artifacts['research']}`\n"
                f"- **post.md:** `{artifacts['post']}`\n"
                f"- **post_image.png:** `{artifacts['image']}`"
            )

        except Exception as exc:
            logger.exception("Pipeline failed")
            footer.error(f"Pipeline failed: {exc}")
