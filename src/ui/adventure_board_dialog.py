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
        """Initialize the single-hero Character Sheet dashboard."""
        layout = QVBoxLayout(self.persona_tab)

        # Profile Header
        header_group = QGroupBox("Hero Profile")
        header_layout = QHBoxLayout(header_group)

        self.avatar_label = QLabel("👤")
        self.avatar_label.setFixedSize(64, 64)
        self.avatar_label.setStyleSheet("font-size: 48px; background: #333; border: 1px solid #555; border-radius: 4px;")
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.avatar_label)

        name_layout = QVBoxLayout()
        self.player_name_label = QLabel(self.player.name)
        self.player_name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f0c674;")
        name_layout.addWidget(self.player_name_label)

        self.profession_label = QLabel(f"{self.player.race} {self.player.profession}")
        self.profession_label.setStyleSheet("color: #aaa; italic;")
        name_layout.addWidget(self.profession_label)
        header_layout.addLayout(name_layout)
        header_layout.addStretch()

        layout.addWidget(header_group)

        # Progression Stats
        stats_group = QGroupBox("Attributes & Wealth")
        stats_layout = QGridLayout(stats_group)

        self.level_label = QLabel("Level: 1")
        self.speed_label = QLabel("Speed: 10")
        self.gold_label = QLabel("Gold: 0g")

        self.xp_bar = QProgressBar()
        self.xp_bar.setFormat("XP: %v / %m")
        self.xp_bar.setFixedHeight(15)

        stats_layout.addWidget(self.level_label, 0, 0)
        stats_layout.addWidget(self.speed_label, 0, 1)
        stats_layout.addWidget(self.gold_label, 1, 0)
        stats_layout.addWidget(self.xp_bar, 2, 0, 1, 2)

        layout.addWidget(stats_group)

        # Equipment Dropdowns
        equip_group = QGroupBox("Equipped Gear")
        equip_layout = QFormLayout(equip_group)

        self.head_dropdown = QComboBox()
        self.chest_dropdown = QComboBox()
        self.weapon_dropdown = QComboBox()
        self.accessory_dropdown = QComboBox()

        # Connect slots
        self.head_dropdown.currentIndexChanged.connect(lambda: self.update_equipment("head", self.head_dropdown))
        self.chest_dropdown.currentIndexChanged.connect(lambda: self.update_equipment("over_torso", self.chest_dropdown))
        self.weapon_dropdown.currentIndexChanged.connect(lambda: self.update_equipment("main_hand", self.weapon_dropdown))
        self.accessory_dropdown.currentIndexChanged.connect(lambda: self.update_equipment("ring", self.accessory_dropdown))

        equip_layout.addRow("Head:", self.head_dropdown)
        equip_layout.addRow("Chest:", self.chest_dropdown)
        equip_layout.addRow("Weapon:", self.weapon_dropdown)
        equip_layout.addRow("Accessory:", self.accessory_dropdown)

        layout.addWidget(equip_group)

        # Master Inventory List
        self.inventory_list = QListWidget()
        layout.addWidget(QLabel("Hero Inventory:"))
        layout.addWidget(self.inventory_list)


    def update_equipment(self, slot, dropdown):
        """Handle equipment change from dropdown and apply stat buffs."""
        from src.game.economy import equip_item, unequip_item
        item_name = dropdown.currentText()

        # Remove old item buffs before equipping new one
        # This implementation assumes buffs are calculated dynamically during combat
        # or stored as a 'base_stats' vs 'current_stats'

        if item_name == "None" or item_name == "Unequipped":
            unequip_item(self.player, slot)
        else:
            equip_item(self.player, item_name, slot)

        self.parent().player_manager.save_player(self.player)
        self.refresh_inventory_display()
        self.refresh_stats_display()

    def refresh_stats_display(self):
        """Update progression and attribute readouts."""
        stats = self.player.reputation.get("_stats", {})
        self.level_label.setText(f"Level: {stats.get('level', 1)}")

        # Calculate derived speed with gear buffs
        base_speed = stats.get("speed", 10)
        bonus_speed = 0
        for item in self.player.equipment.values():
            if item:
                bonus_speed += item.get("speed_bonus", 0)

        self.speed_label.setText(f"Speed: {base_speed + bonus_speed}")
        self.gold_label.setText(f"Gold: {self.player.gold}g")

        xp = stats.get('xp', 0)
        next_level_xp = stats.get('level', 1) * 100
        self.xp_bar.setMaximum(next_level_xp)
        self.xp_bar.setValue(xp)

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
        self.player_name_label.setText(self.player.name)
        self.profession_label.setText(f"{self.player.race} {self.player.profession}")
        self.refresh_stats_display()
        self.refresh_equipment_dropdowns()
        self.refresh_inventory_display()

    def refresh_equipment_dropdowns(self):
        """Populate equipment dropdowns from inventory with dynamic filtering."""
        combos = {
            "head": self.head_dropdown,
            "over_torso": self.chest_dropdown,
            "main_hand": self.weapon_dropdown,
            "ring": self.accessory_dropdown
        }

        for slot, combo in combos.items():
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Unequipped")

            # Filter inventory by matching slot or category
            for item in self.player.inventory:
                if item.get("slot") == slot or (slot == "ring" and item.get("category") == "accessory"):
                    combo.addItem(item["name"])

            # Set current equipped
            current = self.player.equipment.get(slot)
            if current:
                combo.setCurrentText(current["name"])
            else:
                combo.setCurrentIndex(0)

            combo.blockSignals(False)

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
