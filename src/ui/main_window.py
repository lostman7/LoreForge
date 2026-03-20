"""
Main application window for LoreForge.
"""

import json
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QTextEdit, QPushButton, QScrollArea, QLabel,
    QFrame, QSizePolicy, QDialog, QLineEdit, QFormLayout, QMessageBox,
    QMenuBar, QMenu, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPixmap, QPalette, QColor, QKeySequence, QShortcut, QAction, QMovie, QIcon

from src.presets.preset_manager import PresetManager
from src.audio.tts_manager import TTSManager
from src.audio.stt_manager import STTManager
from src.memory.memory_manager import MemoryManager
from src.ai.ai_model import AIModel
from src.game.economy import (
    ensure_player_state,
    inventory_capacity,
    inventory_weight,
    summarize_equipment,
    summarize_inventory,
)
from src.players.player_manager import PlayerManager
from src.session_logging.session_logger import SessionLogger
from src.ui.adventure_board_dialog import AdventureBoardDialog
from src.ui.inventory_dialog import InventoryDialog
from src.ui.options_dialog import OptionsDialog
from src.ui.player_creator_dialog import PlayerCreatorDialog
from src.ui.simple_character_dialog import SimpleCharacterDialog


class PresetComboBox(QComboBox):
    """Custom combo box that displays character avatars."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets_data = []  # List of (name, avatar_path) tuples

    def add_preset_item(self, name: str, avatar_path: Optional[str] = None):
        """Add a preset item with optional avatar."""
        self.presets_data.append((name, avatar_path))

        # Create icon from avatar if available
        if avatar_path and os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio)
            icon = QIcon(pixmap)
            self.addItem(icon, name)
        else:
            # Default icon
            self.addItem("👤 " + name)

    def clear_presets(self):
        """Clear all preset items."""
        self.clear()
        self.presets_data.clear()


class ChatBubble(QFrame):
    """Custom widget for chat messages with avatar."""

    def __init__(self, message: str, is_user: bool = False, avatar_path: Optional[str] = None):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)

        layout = QHBoxLayout(self)

        # Avatar
        if avatar_path and os.path.exists(avatar_path):
            avatar_label = QLabel()
            pixmap = QPixmap(avatar_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio)
            avatar_label.setPixmap(pixmap)
            layout.addWidget(avatar_label)
        else:
            # Default avatar placeholder
            avatar_label = QLabel("👤" if is_user else "🤖")
            avatar_label.setFixedSize(40, 40)
            layout.addWidget(avatar_label)

        # Message text
        text_label = QLabel(message)
        text_label.setWordWrap(True)
        text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(text_label)

        # Styling
        if is_user:
            self.setStyleSheet("""
                ChatBubble {
                    background-color: #444444;
                    border-radius: 10px;
                    margin: 5px;
                    padding: 5px;
                }
                QLabel { color: white; }
            """)
        else:
            self.setStyleSheet("""
                ChatBubble {
                    background-color: #666666;
                    border-radius: 10px;
                    margin: 5px;
                    padding: 5px;
                }
                QLabel { color: white; }
            """)


class MainWindow(QMainWindow):
    """Main application window."""
    voice_input_received = pyqtSignal(str)

    def __init__(self, initial_character: Optional[str] = None, initial_player: Optional[str] = None):
        super().__init__()
        self.config = self.load_config()
        self.current_preset = None
        self.current_player = initial_player
        self.initial_character = initial_character

        # Initialize managers
        self.preset_manager = PresetManager()
        self.player_manager = PlayerManager()
        self.tts_manager = TTSManager(self.config)
        self.stt_manager = STTManager(self.config)
        self.memory_manager = MemoryManager(self.config)
        self.ai_model = AIModel(self.config)
        self.session_logger = SessionLogger()
        self.voice_input_received.connect(self.apply_voice_input)
        self.character_speech_enabled = self.config.get('tts', {}).get('character_speech_enabled', False)
        self.current_player_data = None

        # Set up fallback assets
        self.setup_fallback_assets()

    def setup_fallback_assets(self):
        """Set up fallback assets for missing character resources."""
        # Create defaults directory if it doesn't exist
        defaults_dir = Path(__file__).parent.parent / 'defaults'
        defaults_dir.mkdir(exist_ok=True)

        # Default avatar (simple colored circle or emoji)
        # For now, we'll just use text fallbacks in the UI
        self.default_avatar_emoji = "👤"
        self.default_background_color = QColor(33, 33, 33)  # Dark theme background

        self.init_ui()
        self.create_menu_bar()
        self.apply_theme()
        self.load_presets()

    def load_config(self) -> dict:
        """Load application configuration."""
        config_path = Path(__file__).parent.parent.parent / 'config.json'
        with open(config_path, 'r') as f:
            return json.load(f)

    def init_ui(self):
        """Initialize the user interface with central chat layout."""
        self.setWindowTitle("LoreForge - RPG AI Chat Client")
        self.setGeometry(100, 100, 1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)

        # Left sidebar
        self.setup_sidebar(main_layout)

        # Central chat area
        self.setup_chat_area(main_layout)

        # Set up hotkeys
        self.setup_hotkeys()

        # Auto-load initial character if specified
        if self.initial_character:
            QTimer.singleShot(100, lambda: self.load_initial_character())

        # Set up periodic memory maintenance
        self.memory_update_timer = QTimer()
        self.memory_update_timer.timeout.connect(self.update_memory_periodically)
        self.memory_update_timer.start(600000)  # 10 minutes

    def setup_sidebar(self, parent_layout):
        """Set up the left sidebar with controls."""
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border-right: 1px solid #444;
            }
            QPushButton {
                background-color: #444;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 8px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
            QLabel {
                color: white;
                font-size: 11px;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)

        # Top control buttons
        control_layout = QVBoxLayout()

        # Options button
        self.options_button = QPushButton("⚙️ Options")
        self.options_button.clicked.connect(self.show_options)
        control_layout.addWidget(self.options_button)

        # Add Character button
        self.add_char_button = QPushButton("➕ Add Character")
        self.add_char_button.clicked.connect(self.show_character_creation)
        control_layout.addWidget(self.add_char_button)

        sidebar_layout.addLayout(control_layout)

        # Audio controls
        audio_group = QWidget()
        audio_layout = QVBoxLayout(audio_group)

        audio_label = QLabel("🎵 Audio Controls")
        audio_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        audio_layout.addWidget(audio_label)

        # TTS toggle
        self.tts_toggle = QPushButton("🔊 TTS: ON")
        self.tts_toggle.setCheckable(True)
        self.tts_toggle.setChecked(True)
        self.tts_toggle.clicked.connect(self.toggle_tts)
        audio_layout.addWidget(self.tts_toggle)

        # STT toggle
        self.stt_toggle = QPushButton("🎤 STT: OFF")
        self.stt_toggle.setCheckable(True)
        self.stt_toggle.setChecked(False)
        self.stt_toggle.clicked.connect(self.toggle_stt)
        audio_layout.addWidget(self.stt_toggle)

        self.character_speech_toggle = QPushButton()
        self.character_speech_toggle.setCheckable(True)
        self.character_speech_toggle.setChecked(self.character_speech_enabled)
        self.character_speech_toggle.clicked.connect(self.toggle_character_speech)
        self.character_speech_toggle.setToolTip(
            "Uses the local Qwen3-TTS model with voice_reference.wav and voice_reference.txt from the selected character."
        )
        audio_layout.addWidget(self.character_speech_toggle)
        self.update_character_speech_button()

        sidebar_layout.addWidget(audio_group)

        # Character selection
        char_group = QWidget()
        char_layout = QVBoxLayout(char_group)

        char_label = QLabel("🎭 Character")
        char_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        char_layout.addWidget(char_label)

        self.preset_combo = PresetComboBox()
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        char_layout.addWidget(self.preset_combo)

        sidebar_layout.addWidget(char_group)

        # Player management
        self.setup_player_management(sidebar_layout)

        # Add stretch to push everything to top
        sidebar_layout.addStretch()

        parent_layout.addWidget(sidebar)

    def setup_player_management(self, parent_layout):
        """Set up player management section."""
        player_group = QWidget()
        player_layout = QVBoxLayout(player_group)

        player_label = QLabel("👥 Players")
        player_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        player_layout.addWidget(player_label)

        # Current player selector
        self.player_combo = QComboBox()
        self.player_combo.setStyleSheet("""
            QComboBox {
                background-color: #444;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 5px;
                color: white;
                font-size: 11px;
            }
        """)
        self.player_combo.currentTextChanged.connect(self.on_player_changed)
        player_layout.addWidget(self.player_combo)

        add_player_btn = QPushButton("➕ Forge Hero")
        add_player_btn.clicked.connect(self.add_player)
        player_layout.addWidget(add_player_btn)

        self.edit_player_btn = QPushButton("✏️ Edit Persona")
        self.edit_player_btn.clicked.connect(self.edit_current_player)
        player_layout.addWidget(self.edit_player_btn)

        self.player_summary_label = QLabel("No hero selected.")
        self.player_summary_label.setWordWrap(True)
        self.player_summary_label.setStyleSheet("color: #ddd; font-size: 10px; margin-bottom: 4px;")
        player_layout.addWidget(self.player_summary_label)

        self.player_gold_label = QLabel("💰 Player Gold: --")
        player_layout.addWidget(self.player_gold_label)

        self.npc_gold_label = QLabel("🏪 NPC Gold: --")
        player_layout.addWidget(self.npc_gold_label)

        self.carry_label = QLabel("🎒 Carry: --")
        player_layout.addWidget(self.carry_label)

        self.hall_button = QPushButton("🎒 Hall of Heroes")
        self.hall_button.clicked.connect(self.show_inventory_dialog)
        player_layout.addWidget(self.hall_button)

        self.adventure_board_button = QPushButton("📜 Adventure Board")
        self.adventure_board_button.clicked.connect(self.show_adventure_board)
        player_layout.addWidget(self.adventure_board_button)

        parent_layout.addWidget(player_group)
        self.load_players()

    def setup_chat_area(self, parent_layout):
        """Set up the central chat area."""
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)

        # Background label (for dynamic backgrounds)
        self.background_label = QLabel()
        self.background_label.setScaledContents(True)
        self.background_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chat_layout.addWidget(self.background_label)

        # Chat overlay
        chat_overlay = QWidget()
        chat_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.8);")
        overlay_layout = QVBoxLayout(chat_overlay)

        # Chat display area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch()  # Push messages to top
        self.chat_scroll.setWidget(self.chat_widget)
        overlay_layout.addWidget(self.chat_scroll)

        # Input area
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background-color: rgba(50, 50, 50, 0.9);
                border-top: 1px solid #444;
            }
        """)
        input_layout = QHBoxLayout(input_container)

        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(80)
        self.input_field.setPlaceholderText("Type your message...")
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                border: 1px solid #666;
                border-radius: 5px;
                color: white;
                font-size: 12px;
                padding: 5px;
            }
        """)
        input_layout.addWidget(self.input_field)

        self.voice_button = QPushButton("🎤")
        self.voice_button.clicked.connect(self.toggle_voice_input)
        self.voice_button.setFixedWidth(48)
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #5b4b8a;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6c5da0;
            }
        """)
        input_layout.addWidget(self.voice_button)

        # Send button
        self.send_button = QPushButton("📤 Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        input_layout.addWidget(self.send_button)

        overlay_layout.addWidget(input_container)
        chat_layout.addWidget(chat_overlay)

        parent_layout.addWidget(chat_container)

        # Add back button to return to character select
        self.back_button = QPushButton("← Back to Characters")
        self.back_button.clicked.connect(self.return_to_character_select)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #666;
                border: 1px solid #888;
                border-radius: 5px;
                padding: 5px 10px;
                color: white;
                font-size: 10px;
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 1000;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        # Position the back button (this would need proper layout management in production)

    def load_initial_character(self):
        """Load the initially selected character."""
        if self.initial_character:
            # Find the character in the preset combo and select it
            index = self.preset_combo.findText(self.initial_character)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)
                # This will trigger on_preset_changed automatically

    def return_to_character_select(self):
        """Return to character selection screen."""
        from .character_select_dialog import CharacterSelectDialog

        # Hide current window
        self.hide()

        # Show character select dialog
        config = self.load_config()
        char_select = CharacterSelectDialog(config)
        if char_select.exec() == QDialog.DialogCode.Accepted:
            selected_character = char_select.get_selected_character()
            if selected_character and selected_character != self.initial_character:
                # Load new character
                self.initial_character = selected_character
                self.load_initial_character()
                self.show()
            elif selected_character:
                # Same character, just show
                self.show()
            else:
                # No selection, exit
                self.close()
        else:
            # Cancelled, exit
            self.close()

    def toggle_tts(self):
        """Toggle TTS on/off."""
        enabled = self.tts_toggle.isChecked()
        self.tts_toggle.setText("🔊 TTS: ON" if enabled else "🔇 TTS: OFF")
        # Store preference
        self.config['tts']['enabled'] = enabled
        self.save_config()

    def toggle_stt(self):
        """Toggle STT on/off."""
        enabled = self.stt_toggle.isChecked()
        if enabled:
            started = self.stt_manager.start_listening(self.handle_voice_input)
            if not started:
                self.stt_toggle.setChecked(False)
                self.stt_toggle.setText("🔇 STT: OFF")
                self.voice_button.setText("🎤")
                QMessageBox.warning(
                    self,
                    "STT Unavailable",
                    "Speech-to-text could not start. Check your microphone and local STT dependencies."
                )
                return
            self.stt_toggle.setText("🎤 STT: ON")
            self.voice_button.setText("⏹️")
        else:
            self.stt_manager.stop_listening()
            self.stt_toggle.setText("🔇 STT: OFF")
            self.voice_button.setText("🎤")

    def toggle_character_speech(self):
        """Toggle offline character speech generation."""
        enabled = self.character_speech_toggle.isChecked()

        if enabled:
            can_speak, message = self.tts_manager.can_speak_with_qwen3(self.current_preset)
            if not can_speak:
                self.character_speech_toggle.setChecked(False)
                self.character_speech_enabled = False
                self.update_character_speech_button()
                QMessageBox.warning(
                    self,
                    "Character Speech Unavailable",
                    message
                )
                return

        self.character_speech_enabled = enabled
        self.config.setdefault('tts', {})['character_speech_enabled'] = enabled
        self.save_config()
        self.update_character_speech_button()

    def update_character_speech_button(self):
        """Refresh the sidebar button for offline character speech."""
        enabled = self.character_speech_toggle.isChecked() if hasattr(self, 'character_speech_toggle') else False
        label = "🗣 Character Speech: ON" if enabled else "🗣 Character Speech: OFF"
        self.character_speech_toggle.setText(label)

    def add_player(self):
        """Create a richer player persona."""
        dialog = PlayerCreatorDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dialog.get_player_payload()
        if self.player_manager.load_player(payload['name']):
            QMessageBox.warning(self, "Hero Persona", f"A hero named '{payload['name']}' already exists.")
            return

        created_player = self.player_manager.upsert_player(payload)
        self.load_players(selected_name=payload['name'])
        if not created_player:
            QMessageBox.warning(self, "Player", f"Could not create hero persona '{payload['name']}'.")

    def load_players(self, selected_name: Optional[str] = None):
        """Load persistent players into the sidebar."""
        player_names = self.player_manager.get_player_names()
        if not player_names:
            default_player = self.player_manager.create_player(
                "Player 1",
                "Human",
                "Adventurer",
                title="Guild Rookie",
                origin="The training yard",
                motivation="To prove they belong among the guild's legends.",
                demeanor="Steady",
            )
            if default_player:
                player_names = [default_player.name]

        self.player_combo.blockSignals(True)
        self.player_combo.clear()
        self.player_combo.addItems(player_names)
        self.player_combo.blockSignals(False)

        desired_player = selected_name or self.current_player or (player_names[0] if player_names else None)
        if desired_player and desired_player in player_names:
            self.player_combo.setCurrentText(desired_player)
            self.on_player_changed(desired_player)

    def on_player_changed(self, player_name: str):
        """Load the selected player's state."""
        if not player_name:
            return

        self.current_player = player_name
        self.current_player_data = self.player_manager.load_player(player_name)
        if self.current_player_data:
            ensure_player_state(self.current_player_data)
        self.update_gold_display()
        self.update_player_summary()

    def update_player_summary(self):
        """Refresh the richer player persona summary in the sidebar."""
        if not hasattr(self, 'player_summary_label'):
            return
        if not self.current_player_data:
            self.player_summary_label.setText("No hero selected.")
            return

        player = self.current_player_data
        traits = ', '.join(player.traits[:3]) or 'no traits listed'
        self.player_summary_label.setText(
            f"{player.display_name}\n"
            f"{player.race} {player.profession} from {player.origin}\n"
            f"Demeanor: {player.demeanor} | Pronouns: {player.pronouns}\n"
            f"Traits: {traits}"
        )

    def edit_current_player(self):
        """Edit the currently selected player persona."""
        if not self.current_player_data:
            QMessageBox.information(self, "Hero Persona", "Select a hero first.")
            return

        dialog = PlayerCreatorDialog(self.current_player_data, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dialog.get_player_payload()
        if payload['name'] != dialog.original_name and self.player_manager.load_player(payload['name']):
            QMessageBox.warning(self, "Hero Persona", f"A hero named '{payload['name']}' already exists.")
            return

        updated_player = self.player_manager.upsert_player(payload, previous_name=dialog.original_name)
        if not updated_player:
            QMessageBox.warning(self, "Hero Persona", "Failed to save the updated hero persona.")
            return

        self.current_player = updated_player.name
        self.current_player_data = updated_player
        self.load_players(selected_name=updated_player.name)

    def show_adventure_board(self):
        """Open placeholder quests and arena hooks for the selected hero."""
        if not self.current_player_data:
            QMessageBox.warning(self, "Adventure Board", "Select a player first.")
            return

        dialog = AdventureBoardDialog(self.current_player_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Check for result and persist state
            self.player_manager.save_player(self.current_player_data)
            self.update_gold_display()

    def update_gold_display(self):
        """Refresh sidebar gold and carry information."""
        if self.current_player_data:
            ensure_player_state(self.current_player_data)
            self.player_gold_label.setText(f"💰 Player Gold: {self.current_player_data.gold}g")
            self.carry_label.setText(
                f"🎒 Carry: {inventory_weight(self.current_player_data)}/{inventory_capacity(self.current_player_data)}"
            )
        else:
            self.player_gold_label.setText("💰 Player Gold: --")
            self.carry_label.setText("🎒 Carry: --")

        npc_gold = "--"
        if self.current_preset:
            npc_gold = str(self.current_preset.config.get("economy", {}).get("gold", "--"))
        self.npc_gold_label.setText(f"🏪 NPC Gold: {npc_gold}g")

    def show_inventory_dialog(self):
        """Open the Hall of Heroes inventory/equipment/shop dialog."""
        if not self.current_player_data:
            QMessageBox.warning(self, "Hall of Heroes", "Select a player first.")
            return

        dialog = InventoryDialog(self.current_player_data, self.current_preset, self.player_manager, self)
        dialog.exec()
        self.current_player_data = self.player_manager.load_player(self.current_player_data.name)
        if self.current_player_data:
            ensure_player_state(self.current_player_data)
        if self.current_preset:
            self.current_preset = self.preset_manager.reload_preset(self.current_preset.name) or self.current_preset
        self.update_gold_display()

    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        # Options action
        options_action = QAction('Options...', self)
        options_action.triggered.connect(self.show_options)
        options_action.setShortcut('Ctrl+O')
        file_menu.addAction(options_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def apply_theme(self):
        """Apply dark theme with accent colors."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(33, 33, 33))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        QApplication.setPalette(palette)

    def load_presets(self):
        """Load available character presets with avatars."""
        self.preset_combo.clear_presets()
        preset_names = self.preset_manager.get_preset_names()

        for name in preset_names:
            # Load preset to get avatar path
            preset = self.preset_manager.load_preset(name)
            avatar_path = preset.avatar_path if preset else None
            self.preset_combo.add_preset_item(name, avatar_path)

        if preset_names:
            self.preset_combo.setCurrentIndex(0)
            self.on_preset_changed(preset_names[0])

    def on_preset_changed(self, preset_name: str):
        """Handle preset selection change with validation."""
        if not preset_name:
            return

        # Validate preset before loading
        validation = self.preset_manager.validate_preset(preset_name)

        if not validation['valid']:
            error_msg = f"Preset '{preset_name}' has validation errors:\n\n"
            error_msg += "\n".join(f"• {error}" for error in validation['errors'])
            QMessageBox.warning(self, "Preset Validation Failed", error_msg)
            return

        # Show warnings if any
        if validation['warnings']:
            warning_msg = f"Preset '{preset_name}' loaded with warnings:\n\n"
            warning_msg += "\n".join(f"• {warning}" for warning in validation['warnings'])
            QMessageBox.information(self, "Preset Warnings", warning_msg)

        # Load preset
        try:
            self.current_preset = self.preset_manager.load_preset(preset_name)
            self.update_background()
            self.memory_manager.load_preset_memory(preset_name, self.current_player)
            self.session_logger.start_session(preset_name, self.current_player)
            self.update_character_speech_button()
            self.update_gold_display()

            # Update window title with character info
            if self.current_preset:
                char_name = self.current_preset.config.get('character_name', preset_name)
                job = self.current_preset.config.get('job_title', '')
                location = self.current_preset.config.get('location', '')
                title_info = f"{char_name}"
                if job:
                    title_info += f" - {job}"
                if location:
                    title_info += f" ({location})"
                self.setWindowTitle(f"LoreForge - {title_info}")

        except Exception as e:
            QMessageBox.critical(self, "Preset Load Error", f"Failed to load preset '{preset_name}': {e}")

    def update_background(self):
        """Update the background image with animation support."""
        # Stop any existing animation
        if hasattr(self, 'background_movie') and self.background_movie:
            self.background_movie.stop()

        if self.current_preset and self.current_preset.background_frames:
            # Check if it's a GIF
            first_frame = self.current_preset.background_frames[0]
            if first_frame.lower().endswith('.gif'):
                # Handle animated GIF
                self.background_movie = QMovie(first_frame)
                self.background_label.setMovie(self.background_movie)
                self.background_movie.start()
            elif len(self.current_preset.background_frames) > 1:
                # Handle multi-frame animation
                self.setup_multi_frame_animation()
            else:
                # Single static image
                pixmap = QPixmap(first_frame)
                self.background_label.setPixmap(pixmap)
        else:
            # No background - clear it
            self.background_label.clear()

    def setup_multi_frame_animation(self):
        """Set up multi-frame background animation."""
        if not self.current_preset or not self.current_preset.background_frames:
            return

        self.animation_frames = self.current_preset.background_frames
        self.current_frame_index = 0

        # Set initial frame
        pixmap = QPixmap(self.animation_frames[0])
        self.background_label.setPixmap(pixmap)

        # Set up timer for animation if more than one frame
        if len(self.animation_frames) > 1:
            self.animation_timer = QTimer(self)
            self.animation_timer.timeout.connect(self.next_animation_frame)
            self.animation_timer.start(200)  # 200ms per frame

    def next_animation_frame(self):
        """Advance to next animation frame."""
        if not hasattr(self, 'animation_frames') or not self.animation_frames:
            return

        self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)
        pixmap = QPixmap(self.animation_frames[self.current_frame_index])
        self.background_label.setPixmap(pixmap)

    def send_message(self):
        """Send a message to the AI with player context."""
        message = self.input_field.toPlainText().strip()
        if not message or not self.current_preset:
            QMessageBox.warning(self, "No Character Selected", "Please select a character preset first.")
            return

        # Get current player
        current_player = self.player_combo.currentText()
        if not self.current_player_data:
            self.current_player_data = self.player_manager.load_player(current_player)
        if self.current_player_data:
            ensure_player_state(self.current_player_data)

        # Add user message to chat with player context
        self.add_chat_bubble(f"[{current_player}] {message}", is_user=True)

        # Clear input
        self.input_field.clear()

        # Get AI response with enhanced context
        try:
            # Include player context in the query
            enhanced_message = f"Player {current_player} says: {message}"

            context = self.memory_manager.get_context(enhanced_message)
            response = self.ai_model.generate_response(
                enhanced_message,
                context,
                self.current_preset,
                extra_context=self.build_roleplay_context()
            )

            # Add AI response to chat
            self.add_chat_bubble(response, is_user=False, avatar_path=self.current_preset.avatar_path)

            if self.character_speech_enabled:
                qwen_voice = self.tts_manager.build_character_qwen_voice_config(self.current_preset)
                self.tts_manager.speak(response, qwen_voice, self.current_preset)
            elif self.tts_toggle.isChecked():
                self.tts_manager.speak(response, self.current_preset.voice_config, self.current_preset)

            # Update memory with player context
            self.memory_manager.add_interaction(enhanced_message, response)

            # Log session with player information
            self.session_logger.log_interaction(message, response, player=current_player)
            self.update_gold_display()

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.add_chat_bubble(error_msg, is_user=False)
            QMessageBox.warning(self, "Chat Error", error_msg)

    def add_chat_bubble(self, message: str, is_user: bool = False, avatar_path: Optional[str] = None, is_system: bool = False):
        """Add a chat bubble to the chat area."""
        bubble = ChatBubble(message, is_user, avatar_path)

        if is_system:
            bubble.setStyleSheet("""
                ChatBubble {
                    background-color: #3e3e3e;
                    border: 1px dashed #777;
                    border-radius: 5px;
                    margin: 5px;
                    padding: 3px;
                }
                QLabel { color: #f0c674; font-style: italic; }
            """)

        self.chat_layout.addWidget(bubble)

        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()))

    def toggle_voice_input(self):
        """Toggle voice input mode."""
        if self.stt_manager.is_listening:
            self.stt_manager.stop_listening()
            self.stt_toggle.setChecked(False)
            self.stt_toggle.setText("🔇 STT: OFF")
            self.voice_button.setText("🎤")
        else:
            started = self.stt_manager.start_listening(self.handle_voice_input)
            if not started:
                self.stt_toggle.setChecked(False)
                self.stt_toggle.setText("🔇 STT: OFF")
                self.voice_button.setText("🎤")
                QMessageBox.warning(
                    self,
                    "STT Unavailable",
                    "Speech-to-text could not start. Check your microphone and local STT dependencies."
                )
                return
            self.stt_toggle.setChecked(True)
            self.stt_toggle.setText("🎤 STT: ON")
            self.voice_button.setText("⏹️")

    def handle_voice_input(self, text: str):
        """Handle voice input from the background STT thread."""
        self.voice_input_received.emit(text)

    def apply_voice_input(self, text: str):
        """Apply voice input on the UI thread."""
        # Check if this is a battle result log (system message)
        if "You defeated" in text and "Gold!" in text:
            self.add_chat_bubble(text, is_user=False, is_system=True)

            # Trigger TTS for the immersive combat narrative if enabled
            if self.tts_toggle.isChecked() or self.character_speech_enabled:
                # Use the narrator/character voice for the battle summary
                voice_config = None
                if self.current_preset:
                    if self.character_speech_enabled:
                        voice_config = self.tts_manager.build_character_qwen_voice_config(self.current_preset)
                    else:
                        voice_config = self.current_preset.voice_config

                if voice_config:
                    self.tts_manager.speak(text, voice_config, self.current_preset)
            return

        self.input_field.setPlainText(text)
        self.voice_button.setText("🎤")
        self.stt_toggle.setChecked(False)
        self.stt_toggle.setText("🔇 STT: OFF")
        self.stt_manager.stop_listening()

    def setup_hotkeys(self):
        """Set up keyboard shortcuts."""
        # Ctrl+Enter to send message
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        send_shortcut.activated.connect(self.send_message)

        # F5 to toggle voice input
        voice_shortcut = QShortcut(QKeySequence("F5"), self)
        voice_shortcut.activated.connect(self.toggle_voice_input)

        # Ctrl+N for new character
        new_char_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_char_shortcut.activated.connect(self.show_character_creation)

        # Ctrl+R for reload preset
        reload_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        reload_shortcut.activated.connect(self.reload_preset)

    def show_character_creation(self):
        """Show simplified character creation dialog."""
        dialog = SimpleCharacterDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Character is already created by the dialog
            self.load_presets()  # Refresh preset list



    def show_options(self):
        """Show the options dialog."""
        dialog = OptionsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload config
            self.config = self.load_config()
            self.character_speech_enabled = self.config.get('tts', {}).get('character_speech_enabled', False)
            self.character_speech_toggle.setChecked(self.character_speech_enabled)
            self.update_character_speech_button()
            # Apply theme changes
            self.apply_theme()
            # Could add more dynamic updates here

    def build_roleplay_context(self) -> dict:
        """Build extra system context for roleplay, economy, and inventory."""
        extra_context = {}
        if self.current_player_data:
            ensure_player_state(self.current_player_data)
            extra_context["persona"] = {
                "name": self.current_player_data.name,
                "backstory": self.current_player_data.notes,
                "summary": self.current_player_data.persona_summary(),
                "stats": {
                    "title": self.current_player_data.title,
                    "pronouns": self.current_player_data.pronouns,
                    "demeanor": self.current_player_data.demeanor,
                    "motivation": self.current_player_data.motivation,
                    "traits": ', '.join(self.current_player_data.traits),
                    "specialties": ', '.join(self.current_player_data.specialties),
                    "companions": self.current_player_data.companions,
                    "gold": self.current_player_data.gold,
                    "carry_weight": f"{inventory_weight(self.current_player_data)}/{inventory_capacity(self.current_player_data)}",
                    "inventory": summarize_inventory(self.current_player_data.inventory),
                    "equipment": summarize_equipment(self.current_player_data.equipment),
                    "arena_rank": self.current_player_data.arena_record.get('rank', 'Unranked'),
                    "quest_log": '; '.join(quest['title'] for quest in self.current_player_data.quest_log),
                }
            }

        if self.current_preset:
            economy = self.current_preset.config.get("economy", {})
            stock = economy.get("shop_inventory", [])
            if stock:
                stock_summary = ", ".join(
                    f"{item['name']} ({item.get('price', 0)}g, qty {item.get('quantity', 1)})"
                    for item in stock
                )
            else:
                stock_summary = "no shop stock listed"
            extra_context["economy"] = {
                "npc_name": self.current_preset.character_name,
                "npc_gold": economy.get("gold", 0),
                "pricing_style": economy.get("pricing_style", "standard"),
                "shop_stock": stock_summary,
            }

        return extra_context

    def save_config(self):
        """Persist the active configuration to disk."""
        config_path = Path(__file__).parent.parent.parent / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About LoreForge",
            "LoreForge v1.0.0\n"
            "Immersive RPG AI Chat Client\n\n"
            "Features:\n"
            "• Local AI models with Ollama\n"
            "• Text-to-Speech with Piper and offline Qwen3-TTS\n"
            "• Speech-to-Text input\n"
            "• Persistent character memory\n"
            "• Customizable presets\n\n"
            "Cross-platform: Linux, Windows, macOS"
        )

    def reload_preset(self):
        """Reload the current preset."""
        if self.current_preset:
            preset_name = self.current_preset.name
            # Clear cache and reload
            if preset_name in self.preset_manager._presets_cache:
                del self.preset_manager._presets_cache[preset_name]
            self.on_preset_changed(preset_name)
            self.add_chat_bubble(f"Reloaded preset: {preset_name}", is_user=False)

    def update_memory_periodically(self):
        """Periodically update and maintain memory."""
        try:
            if self.current_preset and self.memory_manager:
                # Force memory consolidation and cleanup
                self.memory_manager.consolidate_memory(self.current_preset.name)
                self.log_memory_update(f"Periodic memory update for {self.current_preset.name}")
        except Exception as e:
            # Silent failure for periodic updates
            print(f"Memory update failed: {e}")

    def log_memory_update(self, message: str):
        """Log memory maintenance activities."""
        try:
            self.session_logger.start_session(f"memory_{self.current_preset.name if self.current_preset else 'unknown'}")
            # Log as system message
            self.session_logger.log_interaction(f"[SYSTEM] {message}", "[MEMORY UPDATED]", "System")
        except:
            pass  # Silent failure
