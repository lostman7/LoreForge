"""
Player management system for LoreForge.
Handles player creation, loading, and player-character relationships.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Player:
    """Player character data class."""
    name: str
    race: str
    profession: str
    notes: str = ""
    reputation: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        if self.reputation is None:
            self.reputation = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        """Create Player from dictionary data."""
        return cls(
            name=data.get('name', 'Unknown'),
            race=data.get('race', 'Human'),
            profession=data.get('profession', 'Adventurer'),
            notes=data.get('notes', ''),
            reputation=data.get('reputation', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Player to dictionary for JSON storage."""
        return {
            'name': self.name,
            'race': self.race,
            'profession': self.profession,
            'notes': self.notes,
            'reputation': self.reputation,
            'created': '2024-01-01T00:00:00'  # Would use real timestamp
        }

    def get_reputation_with(self, character_name: str) -> Dict[str, Any]:
        """Get reputation data with a specific character."""
        return self.reputation.get(character_name, {
            'respect': 0,
            'trust': 0,
            'fear': 0,
            'anger': 0,
            'friendship': 0,
            'interaction_count': 0
        })

    def update_reputation(self, character_name: str, emotion: str, delta: int):
        """Update reputation with a character."""
        if character_name not in self.reputation:
            self.reputation[character_name] = self.get_reputation_with(character_name)

        current = self.reputation[character_name].get(emotion, 0)
        self.reputation[character_name][emotion] = max(-100, min(100, current + delta))
        self.reputation[character_name]['interaction_count'] += 1


class PlayerManager:
    """Manages player characters and their data."""

    def __init__(self, players_dir: Optional[str] = None):
        self.players_dir = Path(players_dir) if players_dir else Path(__file__).parent.parent.parent / 'Players'
        self.players_dir.mkdir(exist_ok=True)
        self._players_cache: Dict[str, Player] = {}

    def get_player_names(self) -> List[str]:
        """Get list of available player names."""
        if not self.players_dir.exists():
            return []

        return [f.stem for f in self.players_dir.glob('*.json')]

    def load_player(self, name: str) -> Optional[Player]:
        """Load a player by name."""
        if name in self._players_cache:
            return self._players_cache[name]

        player_file = self.players_dir / f'{name}.json'
        if not player_file.exists():
            return None

        try:
            with open(player_file, 'r') as f:
                data = json.load(f)
            player = Player.from_dict(data)
            self._players_cache[name] = player
            return player
        except Exception as e:
            print(f"Error loading player {name}: {e}")
            return None

    def save_player(self, player: Player) -> bool:
        """Save a player to disk."""
        try:
            player_file = self.players_dir / f'{player.name}.json'
            with open(player_file, 'w') as f:
                json.dump(player.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving player {player.name}: {e}")
            return False

    def create_player(self, name: str, race: str, profession: str, notes: str = "") -> Optional[Player]:
        """Create a new player."""
        if self.load_player(name):
            return None  # Player already exists

        player = Player(name=name, race=race, profession=profession, notes=notes)
        if self.save_player(player):
            self._players_cache[name] = player
            return player
        return None

    def delete_player(self, name: str) -> bool:
        """Delete a player and all associated data."""
        player_file = self.players_dir / f'{name}.json'
        if player_file.exists():
            try:
                player_file.unlink()
                if name in self._players_cache:
                    del self._players_cache[name]

                # Also clean up memory files for this player
                self._cleanup_player_memories(name)
                return True
            except Exception as e:
                print(f"Error deleting player {name}: {e}")
        return False

    def _cleanup_player_memories(self, player_name: str):
        """Clean up memory files associated with a player."""
        memory_dir = Path(__file__).parent.parent.parent / 'Memory'
        if memory_dir.exists():
            # Remove memory files that contain this player's name
            for mem_file in memory_dir.glob('*.json'):
                if f'_{player_name}' in mem_file.name or player_name in mem_file.name:
                    try:
                        mem_file.unlink()
                        print(f"Cleaned up memory file: {mem_file.name}")
                    except Exception as e:
                        print(f"Error cleaning up {mem_file.name}: {e}")

    def get_all_players(self) -> List[Player]:
        """Get all loaded players."""
        names = self.get_player_names()
        players = []
        for name in names:
            player = self.load_player(name)
            if player:
                players.append(player)
        return players

    def validate_player_data(self, player_name: str) -> Dict[str, Any]:
        """Validate player data and return status."""
        player_file = self.players_dir / f'{player_name}.json'
        validation = {
            'exists': False,
            'valid_json': False,
            'has_required_fields': False,
            'errors': [],
            'warnings': []
        }

        if not player_file.exists():
            validation['errors'].append('Player file does not exist')
            return validation

        validation['exists'] = True

        try:
            with open(player_file, 'r') as f:
                data = json.load(f)
            validation['valid_json'] = True
        except json.JSONDecodeError as e:
            validation['errors'].append(f'Invalid JSON: {e}')
            return validation
        except Exception as e:
            validation['errors'].append(f'Error reading file: {e}')
            return validation

        # Check required fields
        required_fields = ['name', 'race', 'profession']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            validation['errors'].extend([f'Missing required field: {field}' for field in missing_fields])
        else:
            validation['has_required_fields'] = True

        # Check data types
        if 'name' in data and not isinstance(data['name'], str):
            validation['warnings'].append('Name should be a string')
        if 'race' in data and not isinstance(data['race'], str):
            validation['warnings'].append('Race should be a string')
        if 'profession' in data and not isinstance(data['profession'], str):
            validation['warnings'].append('Profession should be a string')

        return validation