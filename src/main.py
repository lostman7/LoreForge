#!/usr/bin/env python3
"""
LoreForge - Immersive RPG/AI Chat Client
Main entry point for the application.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow
from src.ui.character_select_dialog import CharacterSelectDialog


def main():
    """Main application entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("LoreForge")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LoreForge")

    # Load config
    config = load_config()

    # Show character selection dialog first
    char_select = CharacterSelectDialog(config)
    if char_select.exec() == QDialog.DialogCode.Accepted:
        selected_character = char_select.get_selected_character()
        selected_player = char_select.get_selected_player()
        if selected_character and selected_player:
            # Create and show main window with selected character and player
            window = MainWindow(selected_character, selected_player)
            window.show()

            # Start event loop
            sys.exit(app.exec())
        else:
            QMessageBox.warning(None, "Selection Required",
                              "Please select both a player and a character.")
    else:
        # User cancelled character selection
        sys.exit(0)


def load_config():
    """Load application configuration."""
    config_path = Path(__file__).parent.parent / 'config.json'
    if config_path.exists():
        import json
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    main()