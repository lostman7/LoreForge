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
    QLineEdit,
    QComboBox,
    QFormLayout,
    QProgressBar,
    QGroupBox,
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

        self.tabs = QTabWidget()
        self.quest_list = QListWidget()
        self.arena_list = QListWidget()

        quests_tab = QWidget()
        quests_layout = QVBoxLayout(quests_tab)
        quests_layout.addWidget(self.quest_list)

        arena_tab = QWidget()
        arena_layout = QVBoxLayout(arena_tab)
        arena_layout.addWidget(self.arena_list)

        self.persona_tab = QWidget()
        self.init_persona_tab()

        self.tabs.addTab(quests_tab, "Quest Board")
        self.tabs.addTab(arena_tab, "Arena")
        self.tabs.addTab(self.persona_tab, "Character Sheet")
        layout.addWidget(self.tabs)

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

    def init_persona_tab(self):
        """Initialize the new Character Sheet dashboard."""
        layout = QVBoxLayout(self.persona_tab)

        # Profile Switcher
        profile_group = QGroupBox("Profile")
        profile_layout = QFormLayout(profile_group)

        self.hero_dropdown = QComboBox()
        self.hero_dropdown.currentTextChanged.connect(self.switch_hero)
        profile_layout.addRow("Active Hero:", self.hero_dropdown)

        self.player_name_edit = QLineEdit()
        self.player_name_edit.textChanged.connect(self.update_player_name)
        profile_layout.addRow("Player Name:", self.player_name_edit)

        layout.addWidget(profile_group)

        # Progression Stats
        stats_group = QGroupBox("Progression")
        stats_layout = QFormLayout(stats_group)

        self.level_label = QLabel("Level: 1")
        self.gold_label = QLabel("Gold: 0g")
        self.xp_bar = QProgressBar()
        self.xp_bar.setFormat("XP: %v / %m")

        stats_layout.addRow(self.level_label)
        stats_layout.addRow(self.gold_label)
        stats_layout.addRow(self.xp_bar)

        layout.addWidget(stats_group)

        # Equipment Dropdowns
        equip_group = QGroupBox("Equipment")
        equip_layout = QFormLayout(equip_group)

        self.weapon_dropdown = QComboBox()
        self.armor_dropdown = QComboBox()
        self.accessory_dropdown = QComboBox()

        # Connect slots
        self.weapon_dropdown.currentIndexChanged.connect(lambda: self.update_equipment("main_hand", self.weapon_dropdown))
        self.armor_dropdown.currentIndexChanged.connect(lambda: self.update_equipment("over_torso", self.armor_dropdown))
        self.accessory_dropdown.currentIndexChanged.connect(lambda: self.update_equipment("ring", self.accessory_dropdown))

        equip_layout.addRow("Weapon:", self.weapon_dropdown)
        equip_layout.addRow("Armor:", self.armor_dropdown)
        equip_layout.addRow("Accessory:", self.accessory_dropdown)

        layout.addWidget(equip_group)

        # Master Inventory List
        self.inventory_list = QListWidget()
        layout.addWidget(QLabel("Master Inventory:"))
        layout.addWidget(self.inventory_list)

        self.refresh_hero_list()

    def refresh_hero_list(self):
        """Reload the list of saved heroes."""
        from src.players.player_manager import PlayerManager
        pm = self.parent().player_manager
        self.hero_dropdown.blockSignals(True)
        self.hero_dropdown.clear()
        self.hero_dropdown.addItems(pm.get_player_names())
        self.hero_dropdown.setCurrentText(self.player.name)
        self.hero_dropdown.blockSignals(False)

    def switch_hero(self, hero_name):
        """Switch the active player profile."""
        if not hero_name: return
        pm = self.parent().player_manager
        new_player = pm.load_player(hero_name)
        if new_player:
            self.player = new_player
            self.load_content()
            # Notify parent window
            self.parent().on_player_changed(hero_name)

    def update_player_name(self, name):
        """Update the player's name and persist."""
        self.player.name = name
        self.parent().player_manager.save_player(self.player)

    def update_equipment(self, slot, dropdown):
        """Handle equipment change from dropdown."""
        from src.game.economy import equip_item, unequip_item
        item_name = dropdown.currentText()

        if item_name == "None":
            unequip_item(self.player, slot)
        else:
            equip_item(self.player, item_name, slot)

        self.parent().player_manager.save_player(self.player)
        self.refresh_inventory_display()

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

        # Update Character Sheet
        self.player_name_edit.setText(self.player.name)
        stats = self.player.reputation.get("_stats", {})
        self.level_label.setText(f"Level: {stats.get('level', 1)}")
        self.gold_label.setText(f"Gold: {self.player.gold}g")

        xp = stats.get('xp', 0)
        next_level_xp = stats.get('level', 1) * 100 # Simple logic
        self.xp_bar.setMaximum(next_level_xp)
        self.xp_bar.setValue(xp)

        self.refresh_equipment_dropdowns()
        self.refresh_inventory_display()

    def refresh_equipment_dropdowns(self):
        """Populate equipment dropdowns from inventory."""
        self.weapon_dropdown.blockSignals(True)
        self.armor_dropdown.blockSignals(True)
        self.accessory_dropdown.blockSignals(True)

        self.weapon_dropdown.clear()
        self.armor_dropdown.clear()
        self.accessory_dropdown.clear()

        self.weapon_dropdown.addItem("None")
        self.armor_dropdown.addItem("None")
        self.accessory_dropdown.addItem("None")

        for item in self.player.inventory:
            cat = item.get("category", "")
            if cat == "weapon":
                self.weapon_dropdown.addItem(item["name"])
            elif cat == "armor":
                self.armor_dropdown.addItem(item["name"])
            elif cat == "accessory" or cat == "ring":
                self.accessory_dropdown.addItem(item["name"])

        # Set current equipped
        eq = self.player.equipment
        if eq.get("main_hand"): self.weapon_dropdown.setCurrentText(eq["main_hand"]["name"])
        if eq.get("over_torso"): self.armor_dropdown.setCurrentText(eq["over_torso"]["name"])
        if eq.get("ring"): self.accessory_dropdown.setCurrentText(eq["ring"]["name"])

        self.weapon_dropdown.blockSignals(False)
        self.armor_dropdown.blockSignals(False)
        self.accessory_dropdown.blockSignals(False)

    def refresh_inventory_display(self):
        """Refresh the master inventory list."""
        self.inventory_list.clear()

        # Track what is equipped
        equipped_names = []
        for item in self.player.equipment.values():
            if item: equipped_names.append(item["name"])

        for item in self.player.inventory:
            status = " [In Use]" if item["name"] in equipped_names else ""
            self.inventory_list.addItem(
                f"{item['name']} (x{item['quantity']}){status}\n"
                f"{item.get('description', '')}"
            )
