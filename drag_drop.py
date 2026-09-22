"""Small platform-neutral helpers for native file drag-and-drop."""

from pathlib import Path
from typing import Any


def parse_drop_paths(data: str, split_list: Any) -> list[Path]:
    """Parse Tk's platform-specific dropped-file list without reordering it."""
    return [Path(value) for value in split_list(data) if value]
