"""
Helper utilities for paths, logging, and formatting.
"""

from pathlib import Path
from typing import Union


def get_project_root() -> Path:
    """Returns the absolute path to the project root directory."""
    # This file is in src/utilities/helpers.py -> parent.parent.parent is project root
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir(subdir: str = "raw") -> Path:
    """Returns the path to a data subdirectory ('raw' or 'processed')."""
    return get_project_root() / "data" / subdir


def format_currency(value: Union[int, float]) -> str:
    """Formats numeric values as USD currency strings."""
    return f"${value:,.2f}"


def format_percent(value: Union[int, float], decimals: int = 1) -> str:
    """Formats numeric values as percentage strings."""
    return f"{value:.{decimals}f}%"

