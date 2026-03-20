"""Placeholder quest board and arena roster content for LoreForge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Dict

ASSET_DIR = Path(__file__).parent.parent.parent / "assets" / "game"


def _load_json(filename: str) -> List[Dict[str, Any]]:
    path = ASSET_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_quest_board() -> List[Dict[str, Any]]:
    """Return placeholder guild quest offerings."""
    return _load_json("quest_board.json")


def load_arena_roster() -> List[Dict[str, Any]]:
    """Return placeholder arena challengers."""
    return _load_json("arena_roster.json")
