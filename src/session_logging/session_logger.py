"""
Session logger for recording chat interactions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class SessionLogger:
    """Logs chat sessions with summarized interactions."""

    def __init__(self, log_dir: str = "./Logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_session = None
        self.session_data: List[Dict] = []

    def start_session(self, preset_name: str, player_name: Optional[str] = None):
        """Start a new chat session."""
        self.current_session = preset_name
        self.current_player = player_name or "Player"
        self.session_data = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create session file with player context if available
        if player_name:
            session_dir = self.log_dir / f"{preset_name}_{player_name}"
            self.session_file = session_dir / f"session_{timestamp}.txt"
        else:
            session_dir = self.log_dir / preset_name
            self.session_file = session_dir / f"session_{timestamp}.txt"

        # Ensure session directory exists
        self.session_file.parent.mkdir(exist_ok=True)

    def log_interaction(self, user_message: str, ai_response: str, player: str = "Player"):
        """Log a user-AI interaction with player context."""
        if not self.current_session:
            return

        interaction = {
            'timestamp': datetime.now().isoformat(),
            'player': player,
            'user': user_message,
            'ai': ai_response,
            'summary': self._summarize_interaction(user_message, ai_response)
        }

        self.session_data.append(interaction)

        # Write to file
        with open(self.session_file, 'a', encoding='utf-8') as f:
            f.write(f"[{interaction['timestamp']}]\n")
            f.write(f"User: {user_message}\n")
            f.write(f"AI: {ai_response}\n")
            f.write(f"Summary: {interaction['summary']}\n\n")

    def _summarize_interaction(self, user_message: str, ai_response: str) -> str:
        """Create a summary of the interaction."""
        # Simple summarization - in production, use AI for better summaries
        user_words = len(user_message.split())
        ai_words = len(ai_response.split())

        return f"User asked ({user_words} words), AI responded ({ai_words} words) about {self._extract_topic(user_message)}"

    def _extract_topic(self, message: str) -> str:
        """Extract main topic from message (simplified)."""
        words = message.lower().split()
        # Very basic topic extraction
        if any(word in words for word in ['what', 'how', 'why', 'when', 'where']):
            return "question"
        elif any(word in words for word in ['tell', 'story', 'remember']):
            return "narrative"
        else:
            return "conversation"

    def get_session_summary(self) -> Dict:
        """Get summary of current session."""
        if not self.session_data:
            return {}

        total_interactions = len(self.session_data)
        total_user_words = sum(len(interaction['user'].split()) for interaction in self.session_data)
        total_ai_words = sum(len(interaction['ai'].split()) for interaction in self.session_data)

        return {
            'session': self.current_session,
            'total_interactions': total_interactions,
            'total_user_words': total_user_words,
            'total_ai_words': total_ai_words,
            'average_user_length': total_user_words / total_interactions if total_interactions > 0 else 0,
            'average_ai_length': total_ai_words / total_interactions if total_interactions > 0 else 0,
            'topics': [interaction['summary'] for interaction in self.session_data[-5:]]  # Last 5 summaries
        }