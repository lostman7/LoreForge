"""
Player management system for LoreForge.
Handles player creation, loading, and player-character relationships.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from src.game.economy import (
    default_player_equipment,
    default_player_inventory,
    ensure_player_state,
)


def default_arena_record() -> Dict[str, Any]:
    """Build default arena progress for a player."""
    return {
        "wins": 0,
        "losses": 0,
        "rank": "Bronze Initiate",
        "signature_style": "Measured footwork and patient strikes.",
    }


def default_player_quests() -> List[Dict[str, Any]]:
    """Default quest hooks for a newly created hero."""
    return [
        {
            "title": "First Steps in the Hall",
            "status": "active",
            "summary": "Speak with a guild contact and take on your first contract.",
            "reward": "15g and a warm meal",
        }
    ]


@dataclass
class Player:
    """Player character data class."""

    name: str
    race: str
    profession: str
    title: str = "Wanderer"
    pronouns: str = "they/them"
    origin: str = "Unknown Roads"
    motivation: str = "Seeking coin, lore, and a place to belong."
    demeanor: str = "Steady"
    notes: str = ""
    traits: List[str] = field(default_factory=list)
    specialties: List[str] = field(default_factory=list)
    companions: str = ""
    reputation: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    gold: int = 150
    inventory: List[Dict[str, Any]] = field(default_factory=default_player_inventory)
    equipment: Dict[str, Optional[Dict[str, Any]]] = field(default_factory=default_player_equipment)
    quest_log: List[Dict[str, Any]] = field(default_factory=default_player_quests)
    arena_record: Dict[str, Any] = field(default_factory=default_arena_record)

    def __post_init__(self):
        if self.reputation is None:
            self.reputation = {}
        self.traits = self._normalize_tag_list(self.traits)
        self.specialties = self._normalize_tag_list(self.specialties)
        self.quest_log = self._normalize_quest_log(self.quest_log)
        self.arena_record = self._normalize_arena_record(self.arena_record)
        ensure_player_state(self)

    @staticmethod
    def _normalize_tag_list(values: List[str] | str | None) -> List[str]:
        """Normalize comma-separated or list-like tags."""
        if values is None:
            return []
        if isinstance(values, str):
            values = values.split(',')
        normalized = []
        for value in values:
            text = str(value).strip()
            if text and text not in normalized:
                normalized.append(text)
        return normalized

    @staticmethod
    def _normalize_quest_log(entries: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
        """Normalize stored quest data."""
        if not entries:
            return default_player_quests()
        normalized = []
        for entry in entries:
            normalized.append({
                "title": entry.get("title", "Unnamed Quest"),
                "status": entry.get("status", "active"),
                "summary": entry.get("summary", "No summary recorded."),
                "reward": entry.get("reward", "Unknown"),
            })
        return normalized

    @staticmethod
    def _normalize_arena_record(record: Dict[str, Any] | None) -> Dict[str, Any]:
        """Normalize arena record fields."""
        merged = default_arena_record()
        if record:
            merged.update(record)
        return merged

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Create Player from dictionary data."""
        return cls(
            name=data.get("name", "Unknown"),
            race=data.get("race", "Human"),
            profession=data.get("profession", "Adventurer"),
            title=data.get("title", "Wanderer"),
            pronouns=data.get("pronouns", "they/them"),
            origin=data.get("origin", "Unknown Roads"),
            motivation=data.get("motivation", "Seeking coin, lore, and a place to belong."),
            demeanor=data.get("demeanor", "Steady"),
            notes=data.get("notes", ""),
            traits=data.get("traits", []),
            specialties=data.get("specialties", []),
            companions=data.get("companions", ""),
            reputation=data.get("reputation", {}),
            gold=data.get("gold", 150),
            inventory=data.get("inventory"),
            equipment=data.get("equipment"),
            quest_log=data.get("quest_log"),
            arena_record=data.get("arena_record"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Player to dictionary for JSON storage."""
        return {
            "name": self.name,
            "race": self.race,
            "profession": self.profession,
            "title": self.title,
            "pronouns": self.pronouns,
            "origin": self.origin,
            "motivation": self.motivation,
            "demeanor": self.demeanor,
            "notes": self.notes,
            "traits": self.traits,
            "specialties": self.specialties,
            "companions": self.companions,
            "reputation": self.reputation,
            "gold": self.gold,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "quest_log": self.quest_log,
            "arena_record": self.arena_record,
            "created": "2024-01-01T00:00:00",  # Would use real timestamp
        }

    @property
    def display_name(self) -> str:
        """Get a richer player label for UI presentation."""
        if self.title:
            return f"{self.name}, {self.title}"
        return self.name

    def persona_summary(self) -> str:
        """Build a one-line summary for UI cards and AI context."""
        summary_bits = [self.race, self.profession, self.origin]
        summary = " • ".join(bit for bit in summary_bits if bit)
        if self.motivation:
            summary += f" | Drive: {self.motivation}"
        return summary

    def get_reputation_with(self, character_name: str) -> Dict[str, Any]:
        """Get reputation data with a specific character."""
        return self.reputation.get(character_name, {
            "respect": 0,
            "trust": 0,
            "fear": 0,
            "anger": 0,
            "friendship": 0,
            "interaction_count": 0,
        })

    def update_reputation(self, character_name: str, emotion: str, delta: int):
        """Update reputation with a character."""
        if character_name not in self.reputation:
            self.reputation[character_name] = self.get_reputation_with(character_name)

        current = self.reputation[character_name].get(emotion, 0)
        self.reputation[character_name][emotion] = max(-100, min(100, current + delta))
        self.reputation[character_name]["interaction_count"] += 1

    def add_gold(self, amount: int):
        """Add gold to the player."""
        self.gold += amount

    def remove_gold(self, amount: int) -> bool:
        """Remove gold from the player if they have enough."""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def add_item(self, item: Dict[str, Any]) -> Tuple[bool, str]:
        """Add an item to the player's inventory."""
        from src.game.economy import add_item_to_inventory
        return add_item_to_inventory(self, item)

    def remove_item(self, item_name: str, quantity: int = 1) -> Tuple[bool, str]:
        """Remove an item from the player's inventory."""
        from src.game.economy import remove_item_from_inventory
        return remove_item_from_inventory(self, item_name, quantity)


class PlayerManager:
    """Manages player characters and their data."""

    def __init__(self, players_dir: Optional[str] = None):
        self.players_dir = Path(players_dir) if players_dir else Path(__file__).parent.parent.parent / "Players"
        self.players_dir.mkdir(exist_ok=True)
        self._players_cache: Dict[str, Player] = {}

    def get_player_names(self) -> List[str]:
        """Get list of available player names."""
        if not self.players_dir.exists():
            return []

        return sorted(f.stem for f in self.players_dir.glob("*.json"))

    def load_player(self, name: str) -> Optional[Player]:
        """Load a player by name."""
        if name in self._players_cache:
            return self._players_cache[name]

        player_file = self.players_dir / f"{name}.json"
        if not player_file.exists():
            return None

        try:
            with open(player_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            player = Player.from_dict(data)
            self._players_cache[name] = player
            return player
        except Exception as e:
            print(f"Error loading player {name}: {e}")
            return None

    def save_player(self, player: Player, *, previous_name: Optional[str] = None) -> bool:
        """Save a player to disk, optionally renaming the backing file."""
        try:
            if previous_name and previous_name != player.name:
                previous_file = self.players_dir / f"{previous_name}.json"
                if previous_file.exists():
                    previous_file.unlink()
                self._players_cache.pop(previous_name, None)

            player_file = self.players_dir / f"{player.name}.json"
            with open(player_file, "w", encoding="utf-8") as f:
                json.dump(player.to_dict(), f, indent=2)
            self._players_cache[player.name] = player
            return True
        except Exception as e:
            print(f"Error saving player {player.name}: {e}")
            return False

    def create_player(
        self,
        name: str,
        race: str,
        profession: str,
        notes: str = "",
        **extra_fields: Any,
    ) -> Optional[Player]:
        """Create a new player."""
        if self.load_player(name):
            return None

        player = Player(name=name, race=race, profession=profession, notes=notes, **extra_fields)
        if self.save_player(player):
            self._players_cache[name] = player
            return player
        return None

    def upsert_player(self, payload: Dict[str, Any], previous_name: Optional[str] = None) -> Optional[Player]:
        """Create or update a player from UI payload data."""
        player = Player.from_dict(payload)
        if self.save_player(player, previous_name=previous_name):
            return player
        return None

    def delete_player(self, name: str) -> bool:
        """Delete a player and all associated data."""
        player_file = self.players_dir / f"{name}.json"
        if player_file.exists():
            try:
                player_file.unlink()
                if name in self._players_cache:
                    del self._players_cache[name]

                self._cleanup_player_memories(name)
                return True
            except Exception as e:
                print(f"Error deleting player {name}: {e}")
        return False

    def _cleanup_player_memories(self, player_name: str):
        """Clean up memory files associated with a player."""
        memory_dir = Path(__file__).parent.parent.parent / "Memory"
        if memory_dir.exists():
            for mem_file in memory_dir.glob("*.json"):
                if f"_{player_name}" in mem_file.name or player_name in mem_file.name:
                    try:
                        mem_file.unlink()
                        print(f"Cleaned up memory file: {mem_file.name}")
                    except Exception as e:
                        print(f"Error cleaning up {mem_file.name}: {e}")

    def get_all_players(self) -> List[Player]:
        """Get all loaded players."""
        players = []
        for name in self.get_player_names():
            player = self.load_player(name)
            if player:
                players.append(player)
        return players

    def validate_player_data(self, player_name: str) -> Dict[str, Any]:
        """Validate player data and return status."""
        player_file = self.players_dir / f"{player_name}.json"
        validation = {
            "exists": False,
            "valid_json": False,
            "has_required_fields": False,
            "errors": [],
            "warnings": [],
        }

        if not player_file.exists():
            validation["errors"].append("Player file does not exist")
            return validation

        validation["exists"] = True

        try:
            with open(player_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            validation["valid_json"] = True
        except json.JSONDecodeError as e:
            validation["errors"].append(f"Invalid JSON: {e}")
            return validation
        except Exception as e:
            validation["errors"].append(f"Error reading file: {e}")
            return validation

        required_fields = ["name", "race", "profession"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            validation["errors"].extend([f"Missing required field: {field}" for field in missing_fields])
        else:
            validation["has_required_fields"] = True

        for field_name in ["name", "race", "profession", "title", "pronouns", "origin"]:
            if field_name in data and not isinstance(data[field_name], str):
                validation["warnings"].append(f"{field_name.replace('_', ' ').title()} should be a string")

        return validation
