"""
Enhanced character creation dialog with image/voice selection.
"""

import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QFileDialog, QMessageBox, QGroupBox, QProgressBar,
    QTabWidget, QCheckBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

from src.presets.preset import Preset, VoiceConfig


class CharacterCreationDialog(QDialog):
    """Enhanced dialog for creating new characters with full asset management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Character")
        self.setModal(True)
        self.resize(700, 600)

        # Asset paths
        self.avatar_path: Optional[str] = None
        self.background_path: Optional[str] = None
        self.voice_file_path: Optional[str] = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Tab widget for organization
        tab_widget = QTabWidget()

        # Basic Info Tab
        tab_widget.addTab(self.create_basic_tab(), "Basic Info")

        # Assets Tab
        tab_widget.addTab(self.create_assets_tab(), "Assets")

        # Voice Tab
        tab_widget.addTab(self.create_voice_tab(), "Voice")

        # Advanced Tab
        tab_widget.addTab(self.create_advanced_tab(), "Advanced")

        layout.addWidget(tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Character")
        self.create_button.clicked.connect(self.create_character)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def create_basic_tab(self) -> QWidget:
        """Create basic character information tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Character details
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Character folder name (no spaces)")
        layout.addRow("Folder Name:", self.name_edit)

        self.character_name_edit = QLineEdit()
        self.character_name_edit.setPlaceholderText("Display name in chat")
        layout.addRow("Character Name:", self.character_name_edit)

        self.job_edit = QLineEdit()
        self.job_edit.setPlaceholderText("e.g., Ancient Scholar, Tavern Keeper")
        layout.addRow("Job/Title:", self.job_edit)

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., Eldoria Forest, Waterdeep Tavern")
        layout.addRow("Location:", self.location_edit)

        # Lore description
        layout.addRow(QLabel("Short Lore/Background:"))
        self.lore_edit = QTextEdit()
        self.lore_edit.setPlaceholderText("Brief description of character's background and personality...")
        self.lore_edit.setMaximumHeight(80)
        layout.addRow(self.lore_edit)

        # Full profile
        layout.addRow(QLabel("Detailed Profile:"))
        self.profile_edit = QTextEdit()
        self.profile_edit.setPlaceholderText(
            "Detailed character personality, backstory, appearance, and behavior guidelines. "
            "This will guide the AI's responses. Include speech patterns, motivations, etc."
        )
        layout.addRow(self.profile_edit)

        return widget

    def create_assets_tab(self) -> QWidget:
        """Create assets selection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Avatar selection
        avatar_group = QGroupBox("Avatar Image")
        avatar_layout = QVBoxLayout(avatar_group)

        avatar_select_layout = QHBoxLayout()
        self.avatar_path_edit = QLineEdit()
        self.avatar_path_edit.setReadOnly(True)
        self.avatar_path_edit.setPlaceholderText("No avatar selected")
        avatar_select_layout.addWidget(self.avatar_path_edit)

        self.avatar_button = QPushButton("Browse...")
        self.avatar_button.clicked.connect(self.select_avatar)
        avatar_select_layout.addWidget(self.avatar_button)

        avatar_layout.addLayout(avatar_select_layout)

        # Avatar preview
        self.avatar_preview = QLabel()
        self.avatar_preview.setFixedSize(100, 100)
        self.avatar_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        self.avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(self.avatar_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(avatar_group)

        # Background selection
        background_group = QGroupBox("Background Image")
        background_layout = QVBoxLayout(background_group)

        background_select_layout = QHBoxLayout()
        self.background_path_edit = QLineEdit()
        self.background_path_edit.setReadOnly(True)
        self.background_path_edit.setPlaceholderText("No background selected")
        background_select_layout.addWidget(self.background_path_edit)

        self.background_button = QPushButton("Browse...")
        self.background_button.clicked.connect(self.select_background)
        background_select_layout.addWidget(self.background_button)

        background_layout.addLayout(background_select_layout)

        # Background preview
        self.background_preview = QLabel()
        self.background_preview.setFixedSize(200, 120)
        self.background_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        self.background_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        background_layout.addWidget(self.background_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # Animation checkbox
        self.animated_bg_check = QCheckBox("Animated background (GIF or multi-frame)")
        background_layout.addWidget(self.animated_bg_check)

        layout.addWidget(background_group)
        layout.addStretch()

        return widget

    def create_voice_tab(self) -> QWidget:
        """Create voice configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Voice engine selection
        engine_group = QGroupBox("Voice Engine")
        engine_layout = QFormLayout(engine_group)

        self.voice_engine_combo = QComboBox()
        self.voice_engine_combo.addItems(["local", "cloud"])
        self.voice_engine_combo.currentTextChanged.connect(self.on_voice_engine_changed)
        engine_layout.addRow("Default Engine:", self.voice_engine_combo)

        layout.addWidget(engine_group)

        # Local voice configuration
        self.local_voice_group = QGroupBox("Local Voice (Piper/TTS)")
        self.local_voice_layout = QFormLayout(self.local_voice_group)

        local_voice_layout = QHBoxLayout()
        self.local_voice_path_edit = QLineEdit()
        self.local_voice_path_edit.setReadOnly(True)
        self.local_voice_path_edit.setPlaceholderText("No voice model selected")
        local_voice_layout.addWidget(self.local_voice_path_edit)

        self.local_voice_button = QPushButton("Browse...")
        self.local_voice_button.clicked.connect(self.select_local_voice)
        local_voice_layout.addWidget(self.local_voice_button)

        self.local_voice_layout.addRow("Voice Model:", local_voice_layout)

        layout.addWidget(self.local_voice_group)

        # Cloud voice configuration
        self.cloud_voice_group = QGroupBox("Cloud Voice (ElevenLabs/OpenAI)")
        self.cloud_voice_layout = QFormLayout(self.cloud_voice_group)

        self.cloud_provider_combo = QComboBox()
        self.cloud_provider_combo.addItems(["elevenlabs", "openai"])
        self.cloud_voice_layout.addRow("Provider:", self.cloud_provider_combo)

        self.voice_id_edit = QLineEdit()
        self.voice_id_edit.setPlaceholderText("Voice ID or name")
        self.cloud_voice_layout.addRow("Voice ID:", self.voice_id_edit)

        layout.addWidget(self.cloud_voice_group)

        # Initialize visibility
        self.on_voice_engine_changed("local")

        layout.addStretch()
        return widget

    def create_advanced_tab(self) -> QWidget:
        """Create advanced options tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # AI behavior settings
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setValue(0.8)
        self.temperature_spin.setSingleStep(0.1)
        layout.addRow("AI Temperature:", self.temperature_spin)

        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(50, 500)
        self.max_length_spin.setValue(150)
        layout.addRow("Max Response Length:", self.max_length_spin)

        self.personality_weight_spin = QDoubleSpinBox()
        self.personality_weight_spin.setRange(0.0, 1.0)
        self.personality_weight_spin.setValue(0.8)
        self.personality_weight_spin.setSingleStep(0.1)
        layout.addRow("Personality Strength:", self.personality_weight_spin)

        # Memory settings
        self.memory_keywords_edit = QLineEdit()
        self.memory_keywords_edit.setText("magic,elves,history")
        layout.addRow("Memory Keywords:", self.memory_keywords_edit)

        # Animation settings
        self.avatar_animation_check = QCheckBox("Avatar animation")
        layout.addRow(self.avatar_animation_check)

        return widget

    def on_voice_engine_changed(self, engine: str):
        """Handle voice engine selection change."""
        is_local = engine == "local"
        self.local_voice_group.setVisible(is_local)
        self.cloud_voice_group.setVisible(not is_local)

    def select_avatar(self):
        """Select avatar image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Avatar Image", "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.avatar_path = file_path
            self.avatar_path_edit.setText(file_path)

            # Show preview
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
            self.avatar_preview.setPixmap(scaled_pixmap)

    def select_background(self):
        """Select background image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Image", "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.background_path = file_path
            self.background_path_edit.setText(file_path)

            # Show preview
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(200, 120, Qt.AspectRatioMode.KeepAspectRatio)
            self.background_preview.setPixmap(scaled_pixmap)

    def select_local_voice(self):
        """Select local voice model file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Voice Model", "",
            "Voice Model Files (*.onnx *.pth);;Audio Samples (*.wav)"
        )
        if file_path:
            self.voice_file_path = file_path
            self.local_voice_path_edit.setText(file_path)

    def create_character(self):
        """Create the character with all assets."""
        # Validate inputs
        folder_name = self.name_edit.text().strip()
        if not folder_name:
            QMessageBox.warning(self, "Error", "Folder name is required!")
            return

        character_name = self.character_name_edit.text().strip()
        if not character_name:
            QMessageBox.warning(self, "Error", "Character name is required!")
            return

        profile_text = self.profile_edit.toPlainText().strip()
        if not profile_text:
            QMessageBox.warning(self, "Error", "Character profile is required!")
            return

        try:
            # Create character using the preset manager
            from presets.preset_manager import PresetManager
            preset_manager = PresetManager()

            # Create the character data
            character_data = {
                'folder_name': folder_name,
                'character_name': character_name,
                'job_title': self.job_edit.text().strip(),
                'location': self.location_edit.text().strip(),
                'short_lore': self.lore_edit.toPlainText().strip(),
                'profile_text': profile_text,
                'avatar_path': self.avatar_path,
                'background_path': self.background_path,
                'voice_engine': self.voice_engine_combo.currentText(),
                'voice_file_path': self.voice_file_path if self.voice_engine_combo.currentText() == 'local' else None,
                'cloud_provider': self.cloud_provider_combo.currentText() if self.voice_engine_combo.currentText() == 'cloud' else None,
                'voice_id': self.voice_id_edit.text().strip() if self.voice_engine_combo.currentText() == 'cloud' else None,
                'temperature': self.temperature_spin.value(),
                'max_length': self.max_length_spin.value(),
                'personality_weight': self.personality_weight_spin.value(),
                'memory_keywords': self.memory_keywords_edit.text().strip(),
                'avatar_animation': self.avatar_animation_check.isChecked(),
                'animated_background': self.animated_bg_check.isChecked()
            }

            # Create the character
            preset_manager.create_character(character_data)

            QMessageBox.information(self, "Success",
                                  f"Character '{character_name}' created successfully!\n"
                                  f"Folder: Presets/{folder_name}")

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create character: {e}")

    def get_character_data(self):
        """Get the created character data (for compatibility)."""
        return self.name_edit.text().strip(), self.profile_edit.toPlainText().strip()