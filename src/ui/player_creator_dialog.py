"""Rich player persona creator dialog for LoreForge."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.players.player_manager import Player


class PlayerCreatorDialog(QDialog):
    """Dialog for creating or editing a player persona."""

    def __init__(self, player: Optional[Player] = None, parent=None):
        super().__init__(parent)
        self.player = player
        self.original_name = player.name if player else None
        self.setWindowTitle("Forge Hero Persona")
        self.setModal(True)
        self.resize(540, 720)
        self.setStyleSheet(
            """
            QDialog { background-color: #202020; color: white; }
            QGroupBox {
                border: 1px solid #5a4a1f;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #f0c86e; }
            QLabel { color: white; }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
                padding: 6px;
            }
            QPushButton {
                background-color: #6c5220;
                border: 1px solid #8c6f31;
                border-radius: 5px;
                padding: 8px 12px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #81622a; }
            QPushButton.secondary { background-color: #3d3d3d; border-color: #666; }
            """
        )
        self.init_ui()
        self.populate_from_player(player)

    def init_ui(self):
        layout = QVBoxLayout(self)

        intro = QLabel("Shape a full adventurer persona for guild contracts, arena hooks, and roleplay context.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        identity_group = QGroupBox("Identity")
        identity_form = QFormLayout(identity_group)
        self.name_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.pronouns_edit = QLineEdit()
        self.race_edit = QLineEdit()
        self.profession_edit = QLineEdit()
        self.origin_edit = QLineEdit()
        identity_form.addRow("Name", self.name_edit)
        identity_form.addRow("Title / Epithet", self.title_edit)
        identity_form.addRow("Pronouns", self.pronouns_edit)
        identity_form.addRow("Race / Lineage", self.race_edit)
        identity_form.addRow("Profession", self.profession_edit)
        identity_form.addRow("Origin", self.origin_edit)
        layout.addWidget(identity_group)

        roleplay_group = QGroupBox("Roleplay Hooks")
        roleplay_form = QFormLayout(roleplay_group)
        self.demeanor_combo = QComboBox()
        self.demeanor_combo.addItems([
            "Steady",
            "Bold",
            "Wry",
            "Scholarly",
            "Kind",
            "Brooding",
            "Mercurial",
        ])
        self.motivation_edit = QLineEdit()
        self.traits_edit = QLineEdit()
        self.specialties_edit = QLineEdit()
        self.companions_edit = QLineEdit()
        roleplay_form.addRow("Demeanor", self.demeanor_combo)
        roleplay_form.addRow("Motivation", self.motivation_edit)
        roleplay_form.addRow("Traits", self.traits_edit)
        roleplay_form.addRow("Specialties", self.specialties_edit)
        roleplay_form.addRow("Companions", self.companions_edit)
        layout.addWidget(roleplay_group)

        bio_group = QGroupBox("Backstory")
        bio_layout = QVBoxLayout(bio_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("What shaped this hero? What do they fear, owe, or seek?")
        bio_layout.addWidget(self.notes_edit)
        layout.addWidget(bio_group)

        hint = QLabel("Tip: separate traits and specialties with commas. Existing inventory, gold, quests, and arena progress are preserved when editing.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #c9c9c9; font-size: 11px;")
        layout.addWidget(hint)

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setProperty("class", "secondary")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save Hero")
        save.clicked.connect(self.validate_and_accept)
        button_row.addWidget(cancel)
        button_row.addWidget(save)
        layout.addLayout(button_row)

    def populate_from_player(self, player: Optional[Player]):
        """Pre-fill fields from an existing player if provided."""
        if not player:
            self.title_edit.setText("Wanderer")
            self.pronouns_edit.setText("they/them")
            self.race_edit.setText("Human")
            self.profession_edit.setText("Adventurer")
            self.origin_edit.setText("Unknown Roads")
            self.motivation_edit.setText("Seeking coin, lore, and a place to belong.")
            return

        self.name_edit.setText(player.name)
        self.title_edit.setText(player.title)
        self.pronouns_edit.setText(player.pronouns)
        self.race_edit.setText(player.race)
        self.profession_edit.setText(player.profession)
        self.origin_edit.setText(player.origin)
        self.motivation_edit.setText(player.motivation)
        self.demeanor_combo.setCurrentText(player.demeanor)
        self.traits_edit.setText(", ".join(player.traits))
        self.specialties_edit.setText(", ".join(player.specialties))
        self.companions_edit.setText(player.companions)
        self.notes_edit.setPlainText(player.notes)

    @staticmethod
    def _split_tags(value: str):
        return [part.strip() for part in value.split(",") if part.strip()]

    def validate_and_accept(self):
        """Basic validation before closing."""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Hero Persona", "A hero needs a name.")
            return
        if not self.race_edit.text().strip() or not self.profession_edit.text().strip():
            QMessageBox.warning(self, "Hero Persona", "Race/lineage and profession are required.")
            return
        self.accept()

    def get_player_payload(self) -> dict:
        """Return the normalized player payload."""
        existing = self.player.to_dict() if self.player else {}
        return {
            "name": self.name_edit.text().strip(),
            "race": self.race_edit.text().strip(),
            "profession": self.profession_edit.text().strip(),
            "title": self.title_edit.text().strip() or "Wanderer",
            "pronouns": self.pronouns_edit.text().strip() or "they/them",
            "origin": self.origin_edit.text().strip() or "Unknown Roads",
            "motivation": self.motivation_edit.text().strip() or "Seeking coin, lore, and a place to belong.",
            "demeanor": self.demeanor_combo.currentText(),
            "notes": self.notes_edit.toPlainText().strip(),
            "traits": self._split_tags(self.traits_edit.text()),
            "specialties": self._split_tags(self.specialties_edit.text()),
            "companions": self.companions_edit.text().strip(),
            "reputation": existing.get("reputation", {}),
            "gold": existing.get("gold", 150),
            "inventory": existing.get("inventory"),
            "equipment": existing.get("equipment"),
            "quest_log": existing.get("quest_log"),
            "arena_record": existing.get("arena_record"),
        }
