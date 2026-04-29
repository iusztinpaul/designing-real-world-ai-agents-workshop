"""Exploration budget tracker for the Deep Research MCP server.

Keeps a shared call count across all exploration tools (deep_research and
analyze_youtube_video). Once the cap is reached, the agent must call
compile_research to finalise research.md before further exploration is allowed.
"""

import logging
import time
from pathlib import Path

from research.config.constants import EXPLORATION_STATE_FILE, MAX_EXPLORATION_CALLS
from research.utils.file_utils import load_json, save_json

logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """Raised when the exploration call budget has been exhausted.

    Attributes:
        used_calls: The number of exploration calls already recorded.
        max_calls: The maximum number of exploration calls allowed.
    """

    def __init__(self, used_calls: int, max_calls: int) -> None:
        self.used_calls = used_calls
        self.max_calls = max_calls
        super().__init__(str(self))

    def __str__(self) -> str:
        return (
            f"Exploration budget exhausted: {self.used_calls}/{self.max_calls} calls used. "
            "Call `compile_research` now to finalize research.md from the results collected so far."
        )


def record_exploration_call(
    memory_path: Path,
    tool: str,
    query: str,
    *,
    max_calls: int = MAX_EXPLORATION_CALLS,
) -> tuple[int, int]:
    """Append an entry to .memory/exploration_state.json.

    Checks the budget BEFORE appending. If the cap is already met, raises
    BudgetExceededError without writing a new entry to the state file.

    Args:
        memory_path: Path to the .memory directory.
        tool: Name of the tool making the call (e.g. "deep_research").
        query: The query or URL being explored.
        max_calls: Maximum allowed exploration calls (default: MAX_EXPLORATION_CALLS).

    Returns:
        A tuple of (call_index, calls_remaining) where call_index is the 1-based
        index of the current call, and calls_remaining is how many are left after
        this call.

    Raises:
        BudgetExceededError: If the cap was already met before this call.
    """
    state_path = memory_path / EXPLORATION_STATE_FILE
    state = load_json(state_path, default={"calls": []})

    calls: list[dict] = state.get("calls", [])

    # Check BEFORE appending — if already at cap, do not write a new entry.
    if len(calls) >= max_calls:
        raise BudgetExceededError(used_calls=len(calls), max_calls=max_calls)

    calls.append({"tool": tool, "query": query, "at": time.time()})
    state["calls"] = calls
    save_json(state_path, state)

    call_index = len(calls)
    calls_remaining = max_calls - call_index

    logger.info(
        "Exploration call recorded: tool=%s call=%d/%d remaining=%d",
        tool,
        call_index,
        max_calls,
        calls_remaining,
    )

    return call_index, calls_remaining


def reset_exploration_budget(memory_path: Path) -> None:
    """Delete .memory/exploration_state.json to reset the budget.

    Used by compile_research (ticket #005) after producing research.md.

    Args:
        memory_path: Path to the .memory directory.
    """
    state_path = memory_path / EXPLORATION_STATE_FILE
    if state_path.exists():
        state_path.unlink()
        logger.info("Exploration budget reset: deleted %s", state_path)
    else:
        logger.debug(
            "Exploration budget already clear (file not found): %s", state_path
        )
