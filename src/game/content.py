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


def get_monster_pool() -> List[Dict[str, Any]]:
    """Return the available monsters for random encounters."""
    return [
        {
            "id": "bat",
            "name": "Cavern Bat",
            "asset": "Bat.png",
            "base_hp": 15,
            "base_xp": 10,
            "base_gold": [5, 10],
        },
        {
            "id": "skeleton",
            "name": "Rattle-Bone Skeleton",
            "asset": "skeleton.png",
            "base_hp": 25,
            "base_xp": 20,
            "base_gold": [10, 20],
        },
        {
            "id": "spider",
            "name": "Widow Spider",
            "asset": "spider.png",
            "base_hp": 20,
            "base_xp": 15,
            "base_gold": [8, 15],
        },
    ]


def calculate_monster_level(player_level: int) -> int:
    """Implement the scaling formula: monster_level = ceil(player_level / 2.0)."""
    import math
    return math.ceil(player_level / 2.0)
