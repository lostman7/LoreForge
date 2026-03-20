"""Adventure board dialog for placeholder quests and arena hooks."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QListWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.game.content import load_arena_roster, load_quest_board


class AdventureBoardDialog(QDialog):
    """Show placeholder guild quest and arena content tied to the current hero."""

    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setWindowTitle("Adventure Board")
        self.resize(700, 520)
        self.setModal(True)
        self.init_ui()
        self.load_content()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.header_label = QLabel()
        self.header_label.setWordWrap(True)
        self.header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.header_label)

        tabs = QTabWidget()
        self.quest_list = QListWidget()
        self.arena_list = QListWidget()
        self.hero_notes = QTextEdit()
        self.hero_notes.setReadOnly(True)

        quests_tab = QWidget()
        quests_layout = QVBoxLayout(quests_tab)
        quests_layout.addWidget(self.quest_list)

        arena_tab = QWidget()
        arena_layout = QVBoxLayout(arena_tab)
        arena_layout.addWidget(self.arena_list)

        hero_tab = QWidget()
        hero_layout = QVBoxLayout(hero_tab)
        hero_layout.addWidget(self.hero_notes)

        tabs.addTab(quests_tab, "Quest Board")
        tabs.addTab(arena_tab, "Arena")
        tabs.addTab(hero_tab, "Hero Hooks")
        layout.addWidget(tabs)

    def load_content(self):
        arena = self.player.arena_record
        self.header_label.setText(
            f"{self.player.display_name} is browsing fresh contracts. Arena rank: {arena.get('rank', 'Unranked')} "
            f"({arena.get('wins', 0)}W/{arena.get('losses', 0)}L)."
        )

        self.quest_list.clear()
        for quest in load_quest_board():
            self.quest_list.addItem(
                f"{quest['title']} — {quest['difficulty']} — {quest['reward']}\n"
                f"Location: {quest['location']} | Patron: {quest['patron']} | Status: {quest['status']}\n"
                f"{quest['summary']}"
            )

        self.arena_list.clear()
        for challenger in load_arena_roster():
            self.arena_list.addItem(
                f"{challenger['name']} — {challenger['rank']} purse {challenger['purse']}\n"
                f"Style: {challenger['style']} | Signature: {challenger['signature_move']}"
            )

        traits = ", ".join(self.player.traits) or "No traits recorded"
        specialties = ", ".join(self.player.specialties) or "No specialties recorded"
        quests = "\n".join(
            f"• {quest['title']} [{quest['status']}] — {quest['reward']}"
            for quest in self.player.quest_log
        ) or "No personal quests tracked yet."
        self.hero_notes.setPlainText(
            f"Hero Summary\n"
            f"Name: {self.player.display_name}\n"
            f"Pronouns: {self.player.pronouns}\n"
            f"Origin: {self.player.origin}\n"
            f"Profession: {self.player.profession}\n"
            f"Demeanor: {self.player.demeanor}\n"
            f"Motivation: {self.player.motivation}\n"
            f"Traits: {traits}\n"
            f"Specialties: {specialties}\n"
            f"Companions: {self.player.companions or 'None listed'}\n\n"
            f"Backstory\n{self.player.notes or 'No backstory recorded.'}\n\n"
            f"Personal Quest Hooks\n{quests}"
        )
