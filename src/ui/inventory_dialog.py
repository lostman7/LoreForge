"""Inventory, equipment, and trading dialog for LoreForge."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.game.economy import (
    EQUIPMENT_SLOTS,
    add_item_to_inventory,
    ensure_player_state,
    equip_item,
    inventory_capacity,
    inventory_weight,
    remove_item_from_inventory,
    summarize_equipment,
    summarize_inventory,
    unequip_item,
)


class InventoryDialog(QDialog):
    """Dialog for player inventory, equipment, and NPC trade."""

    def __init__(self, player, preset, player_manager, parent=None):
        super().__init__(parent)
        self.player = player
        self.preset = preset
        self.player_manager = player_manager
        ensure_player_state(self.player)

        self.setWindowTitle("Hall of Heroes")
        self.resize(720, 560)
        self.setModal(True)

        self.init_ui()
        self.refresh_ui()

    def init_ui(self):
        """Build dialog UI."""
        layout = QVBoxLayout(self)

        self.header_label = QLabel()
        self.header_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(self.header_label)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_overview_tab(), "Overview")
        self.tabs.addTab(self.build_inventory_tab(), "Inventory")
        self.tabs.addTab(self.build_equipment_tab(), "Equipment")
        self.tabs.addTab(self.build_shop_tab(), "Shop")
        layout.addWidget(self.tabs)

        buttons = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        buttons.addStretch()
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    def build_overview_tab(self) -> QWidget:
        """Build overview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.overview_text = QTextEdit()
        self.overview_text.setReadOnly(True)
        layout.addWidget(self.overview_text)
        return widget

    def build_inventory_tab(self) -> QWidget:
        """Build inventory tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.inventory_list = QListWidget()
        layout.addWidget(self.inventory_list)

        action_row = QHBoxLayout()
        self.equip_slot_combo = QComboBox()
        self.equip_slot_combo.addItems([f"{label} ({slot})" for slot, label in EQUIPMENT_SLOTS.items()])
        action_row.addWidget(self.equip_slot_combo)

        equip_button = QPushButton("Equip Selected")
        equip_button.clicked.connect(self.equip_selected_item)
        action_row.addWidget(equip_button)

        layout.addLayout(action_row)
        return widget

    def build_equipment_tab(self) -> QWidget:
        """Build equipment tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.equipment_list = QListWidget()
        layout.addWidget(self.equipment_list)

        row = QHBoxLayout()
        self.unequip_slot_combo = QComboBox()
        self.unequip_slot_combo.addItems([f"{label} ({slot})" for slot, label in EQUIPMENT_SLOTS.items()])
        row.addWidget(self.unequip_slot_combo)

        unequip_button = QPushButton("Unequip Slot")
        unequip_button.clicked.connect(self.unequip_selected_slot)
        row.addWidget(unequip_button)
        layout.addLayout(row)
        return widget

    def build_shop_tab(self) -> QWidget:
        """Build shop tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        left_group = QGroupBox("NPC Stock")
        left_layout = QVBoxLayout(left_group)
        self.shop_list = QListWidget()
        left_layout.addWidget(self.shop_list)
        buy_button = QPushButton("Buy Selected")
        buy_button.clicked.connect(self.buy_selected_item)
        left_layout.addWidget(buy_button)

        right_group = QGroupBox("Sell From Inventory")
        right_layout = QVBoxLayout(right_group)
        self.sell_list = QListWidget()
        right_layout.addWidget(self.sell_list)
        sell_button = QPushButton("Sell Selected")
        sell_button.clicked.connect(self.sell_selected_item)
        right_layout.addWidget(sell_button)

        layout.addWidget(left_group)
        layout.addWidget(right_group)
        return widget

    def refresh_ui(self):
        """Refresh all UI text and lists."""
        npc_name = self.preset.character_name if self.preset else "NPC"
        self.header_label.setText(
            f"{self.player.name} — Gold: {self.player.gold}g | "
            f"{npc_name} Gold: {self.npc_gold}g"
        )

        overview = [
            f"Player Gold: {self.player.gold}g",
            f"NPC Gold: {self.npc_gold}g",
            f"Carry Weight: {inventory_weight(self.player)}/{inventory_capacity(self.player)}",
            "",
            f"Inventory: {summarize_inventory(self.player.inventory)}",
            "",
            f"Equipment: {summarize_equipment(self.player.equipment)}",
            "",
            f"{npc_name} Stock:",
        ]
        for item in self.shop_inventory:
            overview.append(f"- {item['name']} ({item['price']}g, qty {item['quantity']})")
        self.overview_text.setPlainText("\n".join(overview))

        self.inventory_list.clear()
        for item in self.player.inventory:
            self.inventory_list.addItem(self.format_item(item))

        self.equipment_list.clear()
        for slot, label in EQUIPMENT_SLOTS.items():
            item = self.player.equipment.get(slot)
            item_name = item["name"] if item else "empty"
            self.equipment_list.addItem(f"{label}: {item_name}")

        self.shop_list.clear()
        for item in self.shop_inventory:
            list_item = QListWidgetItem(self.format_item(item))
            list_item.setData(256, item["name"])
            self.shop_list.addItem(list_item)

        self.sell_list.clear()
        for item in self.player.inventory:
            sell_price = max(1, item["price"] // 2)
            list_item = QListWidgetItem(f"{self.format_item(item)} | sells for {sell_price}g")
            list_item.setData(256, item["name"])
            self.sell_list.addItem(list_item)

    @property
    def economy_config(self):
        """Get the mutable NPC economy config."""
        if not self.preset:
            return {"gold": 0, "shop_inventory": []}
        return self.preset.config.setdefault("economy", {"gold": 100, "shop_inventory": []})

    @property
    def npc_gold(self) -> int:
        return int(self.economy_config.get("gold", 0))

    @npc_gold.setter
    def npc_gold(self, value: int):
        self.economy_config["gold"] = max(0, int(value))

    @property
    def shop_inventory(self):
        return self.economy_config.setdefault("shop_inventory", [])

    def format_item(self, item) -> str:
        """Format an item for display."""
        quantity = item.get("quantity", 1)
        slot = item.get("slot")
        slot_text = f" | {slot}" if slot else ""
        return (
            f"{item['name']} — {item['price']}g"
            f" | qty {quantity}"
            f" | wt {item.get('weight', 1)}"
            f"{slot_text}"
        )

    def equip_selected_item(self):
        """Equip the selected inventory item."""
        item = self.inventory_list.currentItem()
        if not item:
            QMessageBox.information(self, "Equip Item", "Select an inventory item first.")
            return

        item_name = item.text().split(" — ", 1)[0]
        slot = self.equip_slot_combo.currentText().rsplit("(", 1)[-1].rstrip(")")
        success, message = equip_item(self.player, item_name, slot)
        if not success:
            QMessageBox.warning(self, "Equip Item", message)
            return

        self.save_state()
        self.refresh_ui()

    def unequip_selected_slot(self):
        """Unequip the selected slot."""
        slot = self.unequip_slot_combo.currentText().rsplit("(", 1)[-1].rstrip(")")
        success, message = unequip_item(self.player, slot)
        if not success:
            QMessageBox.warning(self, "Unequip Item", message)
            return

        self.save_state()
        self.refresh_ui()

    def buy_selected_item(self):
        """Buy an item from the current NPC."""
        current_item = self.shop_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Buy Item", "Select an item from the shop first.")
            return

        item_name = current_item.data(256)
        for index, item in enumerate(self.shop_inventory):
            if item["name"] == item_name:
                if self.player.gold < item["price"]:
                    QMessageBox.warning(self, "Buy Item", "You do not have enough gold.")
                    return
                success, message = add_item_to_inventory(self.player, deepcopy({**item, "quantity": 1}))
                if not success:
                    QMessageBox.warning(self, "Buy Item", message)
                    return

                self.player.gold -= item["price"]
                self.npc_gold += item["price"]
                item["quantity"] -= 1
                if item["quantity"] <= 0:
                    del self.shop_inventory[index]
                self.save_state()
                self.refresh_ui()
                return

    def sell_selected_item(self):
        """Sell an inventory item to the current NPC."""
        current_item = self.sell_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Sell Item", "Select an inventory item first.")
            return

        item_name = current_item.data(256)
        item_data = next((item for item in self.player.inventory if item["name"] == item_name), None)
        if not item_data:
            QMessageBox.warning(self, "Sell Item", "That item is no longer in inventory.")
            return

        sell_price = max(1, item_data["price"] // 2)
        if self.npc_gold < sell_price:
            QMessageBox.warning(self, "Sell Item", "The NPC does not have enough gold to buy that.")
            return

        success, message = remove_item_from_inventory(self.player, item_name, 1)
        if not success:
            QMessageBox.warning(self, "Sell Item", message)
            return

        self.player.gold += sell_price
        self.npc_gold -= sell_price
        sold_item = deepcopy(item_data)
        sold_item["quantity"] = 1
        existing = next((item for item in self.shop_inventory if item["name"] == sold_item["name"]), None)
        if existing and existing.get("stackable"):
            existing["quantity"] += 1
        else:
            self.shop_inventory.append(sold_item)

        self.save_state()
        self.refresh_ui()

    def save_state(self):
        """Persist player and NPC trading state."""
        ensure_player_state(self.player)
        self.player_manager.save_player(self.player)

        if self.preset and self.preset.folder_path:
            config_path = Path(self.preset.folder_path) / "config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.preset.config, f, indent=2)
