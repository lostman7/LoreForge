"""
Character Selection Dialog - Pre-UI screen for LoreForge.
Allows users to select characters, access options, and create new characters.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QFrame, QInputDialog, QMenu, QMessageBox, QProgressBar, QPushButton,
    QTextEdit, QVBoxLayout, QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QPixmap

from src.presets.preset_manager import PresetManager
from src.players.player_manager import PlayerManager
from src.ui.options_dialog import OptionsDialog
from src.ui.player_creator_dialog import PlayerCreatorDialog
from src.ui.simple_character_dialog import SimpleCharacterDialog


class CharacterSelectDialog(QDialog):
    """Pre-UI dialog for character selection and options."""

    character_selected = pyqtSignal(str)  # Emits character name when selected

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.preset_manager = PresetManager()
        self.player_manager = PlayerManager()
        self.selected_character = None
        self.selected_player = None

        self.setWindowTitle("LoreForge - Character Select")
        self.setModal(True)
        self.resize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: white;
            }
            QPushButton {
                background-color: #444;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 8px 12px;
                color: white;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
            QListWidget {
                background-color: #333;
                border: 1px solid #666;
                border-radius: 3px;
                color: white;
                selection-background-color: #4a90e2;
            }
            QFrame {
                border: 1px solid #666;
                border-radius: 5px;
            }
        """)

        self.init_ui()
        self.load_players()
        self.load_characters()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("🎭 LoreForge - Character Select")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Player selection panel
        self.setup_player_panel(layout)

        # Top buttons
        button_layout = QHBoxLayout()

        self.options_button = QPushButton("⚙️ Options")
        self.options_button.clicked.connect(self.show_options)
        button_layout.addWidget(self.options_button)

        self.add_char_button = QPushButton("➕ Add Character")
        self.add_char_button.clicked.connect(self.show_character_creation)
        button_layout.addWidget(self.add_char_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Character list
        self.character_list = QListWidget()
        self.character_list.setMaximumHeight(300)
        self.character_list.itemClicked.connect(self.on_character_selected)
        self.character_list.itemDoubleClicked.connect(self.on_character_double_clicked)
        self.character_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.character_list.customContextMenuRequested.connect(self.show_character_context_menu)
        layout.addWidget(self.character_list)

        # Character info panel
        self.info_frame = QFrame()
        self.info_frame.setVisible(False)
        info_layout = QVBoxLayout(self.info_frame)

        self.char_name_label = QLabel()
        self.char_name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        info_layout.addWidget(self.char_name_label)

        self.char_job_label = QLabel()
        info_layout.addWidget(self.char_job_label)

        self.char_location_label = QLabel()
        info_layout.addWidget(self.char_location_label)

        self.char_description = QTextEdit()
        self.char_description.setMaximumHeight(80)
        self.char_description.setReadOnly(True)
        info_layout.addWidget(self.char_description)

        layout.addWidget(self.info_frame)

        # Bottom buttons
        bottom_layout = QHBoxLayout()

        self.select_button = QPushButton("🎮 Enter World")
        self.select_button.clicked.connect(self.select_character)
        self.select_button.setEnabled(False)
        bottom_layout.addWidget(self.select_button)

        self.cancel_button = QPushButton("❌ Exit")
        self.cancel_button.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_button)

        layout.addLayout(bottom_layout)

    def load_characters(self):
        """Load available characters into the list."""
        self.character_list.clear()
        preset_names = self.preset_manager.get_preset_names()

        for name in preset_names:
            item = QListWidgetItem(f"🎭 {name}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.character_list.addItem(item)

        if not preset_names:
            empty_item = QListWidgetItem("No characters found. Click 'Add Character' to create one!")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.character_list.addItem(empty_item)

    def setup_player_panel(self, parent_layout):
        """Set up the player selection panel."""
        player_group = QFrame()
        player_group.setStyleSheet("""
            QFrame {
                border: 1px solid #666;
                border-radius: 5px;
                background-color: #333;
                margin: 5px;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
        """)

        player_layout = QVBoxLayout(player_group)

        # Player panel header
        player_header = QHBoxLayout()
        player_label = QLabel("👥 Select Player")
        player_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        player_header.addWidget(player_label)

        self.add_player_button = QPushButton("➕ Forge Hero")
        self.add_player_button.clicked.connect(self.show_player_creation)
        self.add_player_button.setStyleSheet("font-size: 11px; padding: 3px 8px;")
        player_header.addWidget(self.add_player_button)

        player_header.addStretch()
        player_layout.addLayout(player_header)

        # Player selection
        self.player_combo = QComboBox()
        self.player_combo.setStyleSheet("""
            QComboBox {
                background-color: #444;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 5px;
                color: white;
                font-size: 12px;
            }
        """)
        player_layout.addWidget(self.player_combo)

        self.player_summary = QLabel('Forge or select a hero persona to continue.')
        self.player_summary.setWordWrap(True)
        self.player_summary.setStyleSheet('color: #d7d7d7; font-size: 11px; margin-top: 6px;')
        player_layout.addWidget(self.player_summary)

        parent_layout.addWidget(player_group)

    def load_players(self):
        """Load available players into the combo box."""
        self.player_combo.blockSignals(True)
        self.player_combo.clear()
        player_names = self.player_manager.get_player_names()

        if player_names:
            self.player_combo.addItems(player_names)
            self.player_combo.setCurrentIndex(0)
            self.selected_player = player_names[0]
        else:
            self.player_summary.setText('No hero personas found yet. Create one to enter the world.')
            self.selected_player = None

        self.player_combo.blockSignals(False)
        try:
            self.player_combo.currentTextChanged.disconnect(self.on_player_selected)
        except TypeError:
            pass
        self.player_combo.currentTextChanged.connect(self.on_player_selected)
        self.update_player_summary(self.selected_player)

    def on_player_selected(self, player_name: str):
        """Handle player selection."""
        if player_name:
            self.selected_player = player_name
        else:
            self.selected_player = None
        self.update_player_summary(self.selected_player)

    def show_player_creation(self):
        """Show the richer hero persona creation dialog."""
        dialog = PlayerCreatorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            payload = dialog.get_player_payload()
            if self.original_name_conflicts(dialog.original_name, payload['name']):
                QMessageBox.warning(self, 'Hero Persona', f"A hero named '{payload['name']}' already exists.")
                return
            player = self.player_manager.upsert_player(payload, previous_name=dialog.original_name)
            if player:
                self.load_players()
                self.player_combo.setCurrentText(player.name)
                self.selected_player = player.name
                self.update_player_summary(player.name)
                QMessageBox.information(self, 'Success', f"Hero persona '{player.name}' saved successfully!")
            else:
                QMessageBox.warning(self, 'Error', 'Failed to save hero persona.')


    def original_name_conflicts(self, original_name: Optional[str], new_name: str) -> bool:
        """Check if a rename would collide with an existing player file."""
        existing = self.player_manager.load_player(new_name)
        return existing is not None and new_name != original_name

    def update_player_summary(self, player_name: Optional[str]):
        """Refresh the selected player summary card."""
        if not player_name:
            self.player_summary.setText('No hero persona selected.')
            return

        player = self.player_manager.load_player(player_name)
        if not player:
            self.player_summary.setText('Unable to load the selected hero persona.')
            return

        traits = ', '.join(player.traits[:3]) or 'no traits listed'
        self.player_summary.setText(
            f"{player.display_name}\n"
            f"{player.race} {player.profession} from {player.origin}.\n"
            f"Demeanor: {player.demeanor} | Motivation: {player.motivation}\n"
            f"Traits: {traits}"
        )

    def on_character_selected(self, item):
        """Handle character selection."""
        if item:
            char_name = item.data(Qt.ItemDataRole.UserRole)
            if char_name:
                self.selected_character = char_name
                self.select_button.setEnabled(True)
                self.show_character_info(char_name)

    def show_character_info(self, char_name: str):
        """Show information about the selected character."""
        preset = self.preset_manager.load_preset(char_name)
        if preset:
            self.info_frame.setVisible(True)

            self.char_name_label.setText(f"Name: {preset.config.get('character_name', char_name)}")
            self.char_job_label.setText(f"Role: {preset.config.get('job_title', 'Unknown')}")
            self.char_location_label.setText(f"Location: {preset.config.get('location', 'Unknown')}")

            # Show first 200 characters of profile
            profile_preview = preset.profile_text[:200]
            if len(preset.profile_text) > 200:
                profile_preview += "..."
            self.char_description.setPlainText(profile_preview)
        else:
            self.info_frame.setVisible(False)

    def on_character_double_clicked(self, item):
        """Handle double-click on character."""
        self.on_character_selected(item)
        if self.selected_character:
            self.select_character()

    def show_character_context_menu(self, position):
        """Show context menu for character items."""
        item = self.character_list.itemAt(position)
        if not item:
            return

        char_name = item.data(Qt.ItemDataRole.UserRole)
        if not char_name:
            return

        menu = QMenu(self)

        # Rename action
        rename_action = QAction("✏️ Rename", self)
        rename_action.triggered.connect(lambda: self.rename_character(char_name))
        menu.addAction(rename_action)

        # Delete action
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(lambda: self.delete_character(char_name))
        menu.addAction(delete_action)

        menu.exec(self.character_list.mapToGlobal(position))

    def select_character(self):
        """Select the current character and close dialog."""
        if self.selected_character:
            # Show loading animation
            self.show_loading_animation()

            # Emit signal and accept
            self.character_selected.emit(self.selected_character)
            self.accept()

    def show_loading_animation(self):
        """Show loading animation while character loads."""
        loading_dialog = LoadingDialog(self.selected_character, self)
        loading_dialog.exec()

    def show_options(self):
        """Show options dialog."""
        options_dialog = OptionsDialog(self.config, self)
        options_dialog.exec()

    def show_character_creation(self):
        """Show character creation dialog."""
        creation_dialog = SimpleCharacterDialog(self)
        if creation_dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh character list
            self.load_characters()

    def rename_character(self, old_name: str):
        """Rename a character."""
        new_name, ok = QInputDialog.getText(self, "Rename Character",
                                          f"Enter new name for '{old_name}':")
        if ok and new_name.strip() and new_name.strip() != old_name:
            try:
                self.preset_manager.rename_preset(old_name, new_name.strip())
                self.load_characters()
                QMessageBox.information(self, "Success", f"Character renamed to '{new_name.strip()}'")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename character: {e}")

    def delete_character(self, char_name: str):
        """Delete a character."""
        reply = QMessageBox.question(self, "Delete Character",
                                   f"Are you sure you want to delete '{char_name}'?\n"
                                   "This will permanently remove all associated files.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.preset_manager.delete_preset(char_name)
                self.load_characters()
                if self.selected_character == char_name:
                    self.selected_character = None
                    self.select_button.setEnabled(False)
                    self.info_frame.setVisible(False)
                QMessageBox.information(self, "Success", f"Character '{char_name}' deleted")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete character: {e}")

    def get_selected_character(self) -> Optional[str]:
        """Get the currently selected character name."""
        return self.selected_character

    def get_selected_player(self) -> Optional[str]:
        """Get the currently selected player name."""
        return self.selected_player


class LoadingDialog(QDialog):
    """Loading animation dialog shown when entering a character world."""

    def __init__(self, character_name: str, parent=None):
        super().__init__(parent)
        self.character_name = character_name

        self.setWindowTitle("Entering the World...")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QProgressBar {
                border: 1px solid #666;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
            }
        """)

        self.init_ui()
        self.start_loading()

    def init_ui(self):
        """Initialize loading UI."""
        layout = QVBoxLayout(self)

        # Character name
        char_label = QLabel(f"Loading {self.character_name}...")
        char_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        char_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(char_label)

        # Door image (try to load actual image, fallback to emoji)
        door_label = QLabel()
        door_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Try to load the door image
        door_image_path = Path(__file__).parent.parent.parent / 'Images' / 'loadingdoor.jpg'
        if door_image_path.exists():
            pixmap = QPixmap(str(door_image_path))
            if not pixmap.isNull():
                # Scale to fit (max 150px height)
                scaled_pixmap = pixmap.scaledToHeight(150, Qt.TransformationMode.SmoothTransformation)
                door_label.setPixmap(scaled_pixmap)
            else:
                door_label.setText("🚪")
                door_label.setStyleSheet("font-size: 48px;")
        else:
            door_label.setText("🚪")
            door_label.setStyleSheet("font-size: 48px;")

        layout.addWidget(door_label)

        # Loading text
        self.loading_label = QLabel("Initializing world...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    def start_loading(self):
        """Start the loading animation."""
        self.progress_bar.setValue(0)
        self.loading_steps = [
            "Loading character assets...",
            "Initializing voice system...",
            "Preparing memory...",
            "Setting up AI context...",
            "Entering the world..."
        ]
        self.current_step = 0

        # Play door opening sound if available
        self.play_door_sound()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(600)  # ~3 seconds total

    def play_door_sound(self):
        """Play the door opening sound effect."""
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl

            sound_path = Path(__file__).parent.parent.parent / 'Sounds' / 'door.mp3'
            if sound_path.exists():
                self.sound_effect = QSoundEffect()
                self.sound_effect.setSource(QUrl.fromLocalFile(str(sound_path)))
                self.sound_effect.setVolume(0.5)  # 50% volume
                self.sound_effect.play()
        except ImportError:
            # PyQt6 multimedia not available, skip sound
            pass
        except Exception as e:
            # Sound playback failed, continue silently
            pass

    def update_progress(self):
        """Update loading progress."""
        self.current_step += 1
        progress = min(self.current_step * 20, 100)

        if self.current_step <= len(self.loading_steps):
            self.loading_label.setText(self.loading_steps[self.current_step - 1])

        self.progress_bar.setValue(progress)

        if progress >= 100:
            self.timer.stop()
            QTimer.singleShot(500, self.accept)  # Close after short delay
