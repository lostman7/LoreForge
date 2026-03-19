"""
Simplified Character Creation Dialog - Auto-Linking Preset Generator
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QGroupBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer


class SimpleCharacterDialog(QDialog):
    """Simplified character creation dialog with auto-linking."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Character Preset")
        self.setModal(True)
        self.resize(500, 400)

        # Asset directories
        self.project_root = Path(__file__).parent.parent.parent
        self.images_dir = self.project_root / 'Images'
        self.voices_dir = self.project_root / 'Voices'
        self.memory_dir = self.project_root / 'Memory'

        # Asset detection results
        self.detected_assets = {}
        self.validation_messages = []

        self.init_ui()
        self.setup_auto_detection()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Character info section
        info_group = QGroupBox("Character Information")
        info_layout = QFormLayout(info_group)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_name_changed)
        self.name_edit.setPlaceholderText("e.g., Thompson, Elara, Marcus")
        info_layout.addRow("Character Name:", self.name_edit)

        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("e.g., Blacksmith, Scholar, Guard (optional)")
        info_layout.addRow("Role/Job:", self.role_edit)

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., City of Vance, Eldoria Forest (optional)")
        info_layout.addRow("Location:", self.location_edit)

        layout.addWidget(info_group)

        # Voice mode section
        voice_group = QGroupBox("Voice Configuration")
        voice_layout = QFormLayout(voice_group)

        self.voice_mode_combo = QComboBox()
        self.voice_mode_combo.addItems(["local", "cloud"])
        voice_layout.addRow("Voice Source:", self.voice_mode_combo)

        layout.addWidget(voice_group)

        # Description section
        desc_group = QGroupBox("AI Context (Optional)")
        desc_layout = QVBoxLayout(desc_group)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Brief description for AI context (e.g., 'You are the blacksmith of Vance. Gruff but loyal.')"
        )
        self.description_edit.setMaximumHeight(60)
        desc_layout.addWidget(self.description_edit)

        layout.addWidget(desc_group)

        # Asset detection status
        self.status_group = QGroupBox("Asset Detection")
        self.status_layout = QVBoxLayout(self.status_group)

        self.status_label = QLabel("Enter character name to auto-detect assets...")
        self.status_layout.addWidget(self.status_label)

        self.asset_status_widget = QWidget()
        self.asset_status_layout = QVBoxLayout(self.asset_status_widget)
        self.status_layout.addWidget(self.asset_status_widget)

        layout.addWidget(self.status_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Preset")
        self.create_button.clicked.connect(self.create_preset)
        self.create_button.setEnabled(False)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def setup_auto_detection(self):
        """Set up auto-detection timer."""
        self.detection_timer = QTimer(self)
        self.detection_timer.setSingleShot(True)
        self.detection_timer.timeout.connect(self.detect_assets)

    def on_name_changed(self, name: str):
        """Handle character name changes."""
        self.create_button.setEnabled(bool(name.strip()))
        if name.strip():
            self.detection_timer.start(500)  # 500ms delay
            self.status_label.setText(f"🔍 Detecting assets for '{name}'...")
        else:
            self.status_label.setText("Enter character name to auto-detect assets...")

    def detect_assets(self):
        """Detect available assets based on character name."""
        name = self.name_edit.text().strip()
        if not name:
            return

        self.detected_assets = {}
        self.validation_messages = []

        # Clear previous status
        self.clear_asset_status()

        # Detect avatar
        avatar_path = self.images_dir / f"{name}.png"
        if avatar_path.exists():
            self.detected_assets['avatar'] = str(avatar_path)
            self.add_asset_status("✅ Avatar", f"Found {name}.png")
        else:
            self.validation_messages.append(f"⚠️ Missing avatar: Images/{name}.png (will use default)")

        # Detect background
        background_path = self.images_dir / f"{name}_wallpaper.png"
        if background_path.exists():
            self.detected_assets['background'] = str(background_path)
            self.add_asset_status("✅ Background", f"Found {name}_wallpaper.png")
        else:
            # Check for GIF
            gif_path = self.images_dir / f"{name}_wallpaper.gif"
            if gif_path.exists():
                self.detected_assets['background'] = str(gif_path)
                self.add_asset_status("✅ Background", f"Found {name}_wallpaper.gif (animated)")
            else:
                self.validation_messages.append(f"⚠️ Missing background: Images/{name}_wallpaper.png (will use default)")

        # Detect voice directory
        voice_dir = self.voices_dir / name
        if voice_dir.exists():
            self.detected_assets['voice_dir'] = str(voice_dir)
            self.add_asset_status("✅ Voice", f"Found Voices/{name}/ directory")

            # Check for voice files
            voice_files = list(voice_dir.glob("*.wav")) + list(voice_dir.glob("*.onnx")) + list(voice_dir.glob("*.pth"))
            if voice_files:
                self.add_asset_status("   └─ Files", f"{len(voice_files)} voice file(s) found")
            else:
                self.validation_messages.append(f"⚠️ No voice files in Voices/{name}/")
        else:
            self.validation_messages.append(f"⚠️ Missing voice directory: Voices/{name}/ (will create empty)")

        # Detect memory file
        memory_path = self.memory_dir / f"{name}.json"
        if memory_path.exists():
            self.detected_assets['memory'] = str(memory_path)
            self.add_asset_status("✅ Memory", f"Found {name}.json")
        else:
            self.validation_messages.append(f"ℹ️ No memory file: Memory/{name}.json (will create new)")

        # Show validation messages
        if self.validation_messages:
            self.add_asset_status("", "")  # Spacer
            for msg in self.validation_messages:
                self.add_asset_status("   " + msg.split(" ")[0], " ".join(msg.split(" ")[1:]))

        self.status_label.setText(f"🎯 Asset detection complete for '{name}'")

    def clear_asset_status(self):
        """Clear asset status display."""
        # Remove all widgets from asset status layout
        while self.asset_status_layout.count():
            child = self.asset_status_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add_asset_status(self, icon: str, message: str):
        """Add asset status line."""
        layout = QHBoxLayout()

        icon_label = QLabel(icon)
        icon_label.setFixedWidth(30)

        message_label = QLabel(message)
        message_label.setWordWrap(True)

        layout.addWidget(icon_label)
        layout.addWidget(message_label, 1)
        layout.addStretch()

        self.asset_status_layout.addLayout(layout)

    def create_preset(self):
        """Create the character preset."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Character name is required!")
            return

        try:
            # Create preset using the simplified logic
            from presets.preset_manager import PresetManager
            preset_manager = PresetManager()

            # Prepare character data
            character_data = {
                'name': name,
                'role': self.role_edit.text().strip(),
                'location': self.location_edit.text().strip(),
                'description': self.description_edit.toPlainText().strip(),
                'voice_mode': self.voice_mode_combo.currentText(),
                'detected_assets': self.detected_assets
            }

            # Create the preset
            success = preset_manager.create_simple_preset(character_data)

            if success:
                QMessageBox.information(self, "Success",
                                      f"Character preset '{name}' created successfully!\n\n"
                                      f"Assets linked: {len(self.detected_assets)} found\n"
                                      f"Missing assets will use defaults.")

                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to create character preset!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create preset: {e}")