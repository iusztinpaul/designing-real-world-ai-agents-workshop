"""File I/O utilities for the Deep Research MCP server."""

import json
import logging
from pathlib import Path
from typing import Any

from research.config.constants import MEMORY_FOLDER

logger = logging.getLogger(__name__)


def ensure_memory_dir(working_dir: str) -> Path:
    """Ensure the .memory subdirectory exists under working_dir.

    Args:
        working_dir: The root working directory path.

    Returns:
        The Path to the .memory directory (created if absent).
    """
    memory_path = Path(working_dir) / MEMORY_FOLDER
    memory_path.mkdir(parents=True, exist_ok=True)
    return memory_path


def validate_directory(working_dir: str) -> Path:
    """Verify that working_dir exists and is a directory.

    Args:
        working_dir: The directory path to validate.

    Returns:
        A resolved Path object for working_dir.

    Raises:
        ValueError: If the path does not exist or is not a directory.
    """
    path = Path(working_dir)
    if not path.exists():
        raise ValueError(
            f"Working directory does not exist: '{working_dir}'. "
            "Please create it before calling this tool."
        )
    if not path.is_dir():
        raise ValueError(
            f"Path is not a directory: '{working_dir}'. "
            "Please provide a valid directory path."
        )
    return path


def read_file(path: Path) -> str:
    """Read and return the text content of a file.

    Args:
        path: The path to the file to read.

    Returns:
        The file's text content, or an empty string if the file is missing.
    """
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except IOError as exc:
        logger.error("Failed to read file %s: %s", path, exc)
        return ""


def write_file(path: Path, content: str) -> None:
    """Write text content to a file, creating parent directories as needed.

    Args:
        path: The destination file path.
        content: The text content to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    """Load and return parsed JSON from a file.

    Args:
        path: The path to the JSON file.
        default: Value to return if the file is missing or invalid.
                 Defaults to an empty dict when not provided.

    Returns:
        Parsed JSON data, or default if the file is absent or unreadable.
    """
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, IOError) as exc:
        logger.error("Failed to load JSON from %s: %s", path, exc)
        return default


def save_json(path: Path, data: Any) -> None:
    """Persist data as a pretty-printed JSON file.

    Args:
        path: The destination file path.
        data: The data to serialise.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8",
    )
