"""
Options dialog for configuring LoreForge settings.
"""

import json
from pathlib import Path
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPushButton, QFormLayout, QGroupBox, QMessageBox,
    QFileDialog, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class OptionsDialog(QDialog):
    """Options dialog for application settings."""

    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.config_file = Path(__file__).parent.parent.parent / 'config.json'

        self.setWindowTitle("LoreForge Options")
        self.setModal(True)
        self.resize(600, 500)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Tab widget
        self.tab_widget = QTabWidget()

        # AI Tab
        self.tab_widget.addTab(self.create_ai_tab(), "AI")

        # Audio Tab
        self.tab_widget.addTab(self.create_audio_tab(), "Audio")

        # API Keys Tab
        self.tab_widget.addTab(self.create_api_tab(), "API Keys")

        # Memory Tab
        self.tab_widget.addTab(self.create_memory_tab(), "Memory")

        # UI Tab
        self.tab_widget.addTab(self.create_ui_tab(), "Interface")

        layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def create_ai_tab(self) -> QWidget:
        """Create AI settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # AI Backend
        self.ai_backend_combo = QComboBox()
        self.ai_backend_combo.addItems(["ollama", "lmstudio", "openai", "grok", "huggingface", "openrouter"])
        self.ai_backend_combo.currentTextChanged.connect(self.on_ai_backend_changed)
        layout.addRow("AI Backend:", self.ai_backend_combo)

        # Model selection (dynamic based on backend)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        layout.addRow("Model:", self.model_combo)

        # Test connection button
        self.test_ai_button = QPushButton("Test Connection")
        self.test_ai_button.clicked.connect(self.test_ai_connection)
        layout.addRow("", self.test_ai_button)

        # Model
        self.ai_model_edit = QLineEdit()
        layout.addRow("Model:", self.ai_model_edit)

        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        layout.addRow("Temperature:", self.temperature_spin)

        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 32768)
        self.max_tokens_spin.setValue(2048)
        layout.addRow("Max Tokens:", self.max_tokens_spin)

        # GPU Acceleration
        self.gpu_combo = QComboBox()
        self.gpu_combo.addItems(["auto", "cuda", "rocm", "mps", "cpu"])
        layout.addRow("GPU Acceleration:", self.gpu_combo)

        return widget

    def create_audio_tab(self) -> QWidget:
        """Create audio settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # TTS Engine
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems(["piper", "qwen3", "elevenlabs", "openai", "system"])
        layout.addRow("TTS Engine:", self.tts_engine_combo)

        # STT Engine
        self.stt_engine_combo = QComboBox()
        self.stt_engine_combo.addItems(["google", "openai", "whisper", "huggingface", "system"])
        layout.addRow("STT Engine:", self.stt_engine_combo)

        # Language
        self.language_edit = QLineEdit()
        self.language_edit.setText("en-US")
        layout.addRow("Language:", self.language_edit)

        # Fallback options
        self.tts_fallback_check = QCheckBox("Fallback to system TTS")
        layout.addRow(self.tts_fallback_check)

        return widget

    def create_api_tab(self) -> QWidget:
        """Create API keys tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # API Keys group
        api_group = QGroupBox("API Keys")
        api_layout = QFormLayout(api_group)

        self.api_keys = {}

        apis = [
            ('elevenlabs', 'ElevenLabs API Key'),
            ('openai', 'OpenAI API Key'),
            ('huggingface', 'HuggingFace API Key'),
            ('grok', 'Grok API Key'),
            ('lmstudio', 'LM Studio API Key'),
            ('openrouter', 'OpenRouter API Key')
        ]

        for key, label in apis:
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            api_layout.addRow(label + ":", edit)
            self.api_keys[key] = edit

        layout.addWidget(api_group)

        # Warning label
        warning = QLabel("⚠️ API keys are stored locally in config.json. Keep this file secure!")
        warning.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(warning)

        layout.addStretch()
        return widget

    def create_memory_tab(self) -> QWidget:
        """Create memory settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Max floating memory
        self.max_memory_spin = QSpinBox()
        self.max_memory_spin.setRange(10, 1000)
        self.max_memory_spin.setSuffix(" MB")
        layout.addRow("Max Floating Memory:", self.max_memory_spin)

        # Vector DB path
        self.vector_db_edit = QLineEdit()
        layout.addRow("Vector DB Path:", self.vector_db_edit)

        # Auto cleanup
        self.auto_cleanup_check = QCheckBox("Auto cleanup old memories")
        layout.addRow(self.auto_cleanup_check)

        return widget

    def create_ui_tab(self) -> QWidget:
        """Create UI settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        layout.addRow("Theme:", self.theme_combo)

        # Accent color
        self.accent_edit = QLineEdit()
        layout.addRow("Accent Color:", self.accent_edit)

        # Window size
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(400, 1920)
        self.width_spin.setValue(800)
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(300, 1080)
        self.height_spin.setValue(600)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.height_spin)

        layout.addRow("Window Size:", size_layout)

        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        layout.addRow("Font Size:", self.font_size_spin)

        # UI options
        self.timestamps_check = QCheckBox("Show timestamps")
        layout.addRow(self.timestamps_check)

        self.autoscroll_check = QCheckBox("Auto scroll to bottom")
        layout.addRow(self.autoscroll_check)

        return widget

    def load_settings(self):
        """Load current settings into UI."""
        # AI settings
        ai_config = self.config.get('ai', {})
        backend = ai_config.get('backend', 'ollama')
        self.ai_backend_combo.setCurrentText(backend)
        self.on_ai_backend_changed(backend)  # Populate model list
        self.model_combo.setCurrentText(ai_config.get('model', 'llama3.2:3b'))
        self.temperature_spin.setValue(ai_config.get('temperature', 0.8))
        self.max_tokens_spin.setValue(ai_config.get('max_tokens', 2048))
        self.gpu_combo.setCurrentText(ai_config.get('gpu_acceleration', 'auto'))

        # Audio settings
        tts_config = self.config.get('tts', {})
        stt_config = self.config.get('stt', {})
        self.tts_engine_combo.setCurrentText(tts_config.get('engine', 'piper'))
        self.stt_engine_combo.setCurrentText(stt_config.get('engine', 'google'))
        self.language_edit.setText(stt_config.get('language', 'en-US'))
        self.tts_fallback_check.setChecked(tts_config.get('fallback_to_system', True))

        # API keys
        apis_config = self.config.get('apis', {})
        for key, edit in self.api_keys.items():
            edit.setText(apis_config.get(key, ''))

        # Memory settings
        memory_config = self.config.get('memory', {})
        self.max_memory_spin.setValue(memory_config.get('max_floating_mb', 50))
        self.vector_db_edit.setText(memory_config.get('vector_db_path', './memory_db'))
        self.auto_cleanup_check.setChecked(memory_config.get('auto_cleanup', True))

        # UI settings
        app_config = self.config.get('app', {})
        ui_config = self.config.get('ui', {})
        self.theme_combo.setCurrentText(app_config.get('theme', 'dark'))
        self.accent_edit.setText(app_config.get('accent_color', '#ff4444'))
        self.width_spin.setValue(ui_config.get('window_width', 800))
        self.height_spin.setValue(ui_config.get('window_height', 600))
        self.font_size_spin.setValue(ui_config.get('font_size', 10))
        self.timestamps_check.setChecked(ui_config.get('show_timestamps', True))
        self.autoscroll_check.setChecked(ui_config.get('auto_scroll', True))

    def save_settings(self):
        """Save settings to config file."""
        try:
            # Update config from UI
            self.config['ai'] = {
                'backend': self.ai_backend_combo.currentText(),
                'model': self.model_combo.currentText(),
                'temperature': self.temperature_spin.value(),
                'max_tokens': self.max_tokens_spin.value(),
                'gpu_acceleration': self.gpu_combo.currentText()
            }

            self.config['tts'] = {
                **self.config.get('tts', {}),
                'engine': self.tts_engine_combo.currentText(),
                'fallback_to_system': self.tts_fallback_check.isChecked()
            }

            self.config['stt'] = {
                **self.config.get('stt', {}),
                'engine': self.stt_engine_combo.currentText(),
                'language': self.language_edit.text()
            }

            # API keys
            for key, edit in self.api_keys.items():
                self.config['apis'][key] = edit.text()

            self.config['memory'] = {
                'max_floating_mb': self.max_memory_spin.value(),
                'vector_db_path': self.vector_db_edit.text(),
                'auto_cleanup': self.auto_cleanup_check.isChecked()
            }

            self.config['app'] = {
                'name': self.config['app'].get('name', 'LoreForge'),
                'version': self.config['app'].get('version', '1.0.0'),
                'theme': self.theme_combo.currentText(),
                'accent_color': self.accent_edit.text(),
                'first_run': False
            }

            self.config['ui'] = {
                'window_width': self.width_spin.value(),
                'window_height': self.height_spin.value(),
                'font_size': self.font_size_spin.value(),
                'show_timestamps': self.timestamps_check.isChecked(),
                'auto_scroll': self.autoscroll_check.isChecked()
            }

            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)

            QMessageBox.information(self, "Settings Saved",
                                  "Settings have been saved successfully!\n"
                                  "Restart the application for some changes to take effect.")

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def on_ai_backend_changed(self, backend: str):
        """Handle AI backend selection change."""
        self.model_combo.clear()

        # Populate model suggestions based on backend
        model_suggestions = {
            "ollama": ["llama3.2:3b", "llama3.1:8b", "mistral:7b", "codellama:7b"],
            "lmstudio": ["local-model", "custom-model"],
            "openai": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            "grok": ["grok-1", "grok-beta"],
            "huggingface": ["microsoft/DialoGPT-medium", "facebook/blenderbot-400M-distill"],
            "openrouter": ["anthropic/claude-3", "openai/gpt-4", "meta/llama-2-70b"]
        }

        if backend in model_suggestions:
            self.model_combo.addItems(model_suggestions[backend])

    def test_ai_connection(self):
        """Test the AI connection with current settings."""
        backend = self.ai_backend_combo.currentText()
        model = self.model_combo.currentText()
        api_key = ""

        # Get API key if needed
        if backend in ['openai', 'grok', 'huggingface', 'openrouter']:
            key_name = f"{backend}_api_key"
            api_key = getattr(self, f"{backend}_key_edit", QLineEdit()).text()

        try:
            # Basic connection test (simplified)
            if backend == "ollama":
                import subprocess
                result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    QMessageBox.information(self, "Test Successful", "Ollama connection OK!")
                else:
                    QMessageBox.warning(self, "Test Failed", "Cannot connect to Ollama. Is it running?")
            else:
                QMessageBox.information(self, "Test", f"Would test {backend} connection with API key validation.")

        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Connection test failed: {e}")
