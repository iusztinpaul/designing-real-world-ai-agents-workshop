"""Logging utilities for the LinkedIn Writer MCP Server."""

import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging with a standard format.

    Args:
        level: The logging level to apply (e.g. logging.INFO, logging.DEBUG).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
