"""Adventure board dialog for placeholder quests and arena hooks."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QListWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize

from src.game.content import load_arena_roster, load_quest_board, ASSET_DIR


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

        # Guild Wall (Scroll Button)
        self.scroll_layout = QHBoxLayout()
        self.scroll_layout.addStretch()

        self.scroll_btn = QPushButton()
        scroll_path = ASSET_DIR / "Scroll.png"
        if scroll_path.exists():
            pixmap = QPixmap(str(scroll_path))
            icon = QIcon(pixmap)
            self.scroll_btn.setIcon(icon)
            # Maintain aspect ratio while scaling
            self.scroll_btn.setIconSize(QSize(64, 64))
            self.scroll_btn.setFixedSize(70, 70)
            self.scroll_btn.setToolTip("Start a Monster Encounter!")
            self.scroll_btn.setStyleSheet("border: none; background: transparent;")
            self.scroll_btn.clicked.connect(self.start_monster_encounter)

        self.scroll_layout.addWidget(self.scroll_btn)

        # Merchant Button (Satchel)
        self.merchant_btn = QPushButton()
        # Fallback to text if satchel icon missing or just use an icon
        self.merchant_btn.setText("🛍️") # Use an emoji as a simple placeholder icon
        self.merchant_btn.setFixedSize(70, 70)
        self.merchant_btn.setStyleSheet("font-size: 32px; border: none; background: transparent;")
        self.merchant_btn.setToolTip("Visit the Guild Merchant!")
        self.merchant_btn.clicked.connect(self.visit_merchant)
        self.scroll_layout.addWidget(self.merchant_btn)

        layout.addLayout(self.scroll_layout)

    def visit_merchant(self):
        """Placeholder for a simple merchant interaction."""
        from src.ui.inventory_dialog import InventoryDialog
        from src.presets.preset import Preset, VoiceConfig

        # Create a dummy 'Guild Merchant' preset for the shop interface
        merchant_preset = Preset(
            name="Guild Merchant",
            profile_text="The Guild Merchant is a jolly soul who sells essential supplies to adventurers.",
            character_name="Guild Merchant",
            config={
                "economy": {
                    "gold": 5000,
                    "pricing_style": "standard guild rates",
                    "shop_inventory": [
                        {
                            "name": "Minor Healing Potion",
                            "category": "consumable",
                            "price": 40,
                            "quantity": 10,
                            "weight": 1,
                            "stackable": True,
                            "description": "A small red potion that restores 20 HP.",
                            "rarity": "common"
                        },
                        {
                            "name": "XP Insight Tome",
                            "category": "consumable",
                            "price": 150,
                            "quantity": 2,
                            "weight": 2,
                            "stackable": False,
                            "description": "A dusty book that grants a small boost to XP.",
                            "rarity": "uncommon"
                        },
                        {
                            "name": "Traveler's Bread",
                            "category": "consumable",
                            "price": 5,
                            "quantity": 20,
                            "weight": 1,
                            "stackable": True,
                            "description": "Hard bread that keeps well on the road.",
                            "rarity": "common"
                        }
                    ]
                }
            }
        )

        # Use InventoryDialog in shop mode
        dialog = InventoryDialog(self.player, merchant_preset, self.parent().player_manager, self)
        dialog.tabs.setCurrentIndex(3) # Switch to Shop tab
        dialog.exec()

        # Persist player state after shopping
        self.parent().player_manager.save_player(self.player)
        self.parent().update_gold_display()

    def start_monster_encounter(self):
        from src.ui.battle_dialog import BattleDialog
        battle = BattleDialog(self.player, self)
        if battle.exec() == QDialog.DialogCode.Accepted:
            # Emit battle outcome summary to parent for chat logging
            self.parent().voice_input_received.emit(battle.get_result_summary())

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
