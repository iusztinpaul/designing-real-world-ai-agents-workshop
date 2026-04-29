"""String constants used across the research package."""

RESEARCH_MD_FILE = "research.md"
RESEARCH_RESULTS_FILE = "research_results.json"
MEMORY_FOLDER = ".memory"
TRANSCRIPTS_FOLDER = "transcripts"

EXPLORATION_STATE_FILE = "exploration_state.json"

# The budget is capped at total calls (not rounds) because per-call latency
# overlaps with the gap between LLM turns, making it unreliable to detect
# "rounds" from server-side timing alone. Six calls ≈ "3 rounds × 2 queries" —
# enough breadth for solid research without allowing runaway agent loops.
MAX_EXPLORATION_CALLS = 6
