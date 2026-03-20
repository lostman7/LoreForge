"""Economy, inventory, and equipment helpers for LoreForge."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

EQUIPMENT_SLOTS = {
    "head": "Head",
    "under_torso": "Underclothes (Torso)",
    "over_torso": "Overclothes / Armor",
    "under_legs": "Underclothes (Legs)",
    "over_legs": "Leg Armor",
    "feet": "Feet",
    "back": "Back",
    "main_hand": "Weapon Hand",
    "off_hand": "Shield Hand",
    "ring": "Ring",
}


def make_item(
    name: str,
    category: str,
    price: int,
    *,
    quantity: int = 1,
    weight: int = 1,
    stackable: bool = False,
    slot: str | None = None,
    description: str = "",
    capacity_bonus: int = 0,
    rarity: str = "common",
) -> Dict[str, Any]:
    """Create a normalized item dictionary."""
    return {
        "name": name,
        "category": category,
        "price": int(price),
        "quantity": int(quantity),
        "weight": int(weight),
        "stackable": bool(stackable),
        "slot": slot,
        "description": description,
        "capacity_bonus": int(capacity_bonus),
        "rarity": rarity,
    }


def default_player_inventory() -> List[Dict[str, Any]]:
    """Get the default unequipped player inventory."""
    return [
        make_item("Traveler's Rations", "consumable", 8, quantity=2, weight=1, stackable=True,
                  description="Simple travel food for the road."),
        make_item("Waterskin", "utility", 5, weight=1, description="A worn but dependable waterskin."),
        make_item("Bandage Roll", "consumable", 6, quantity=2, weight=1, stackable=True,
                  description="Clean cloth for basic field treatment."),
    ]


def default_player_equipment() -> Dict[str, Dict[str, Any] | None]:
    """Get the default equipped gear for a new player."""
    return {
        "head": None,
        "under_torso": make_item("Linen Tunic", "clothing", 10, weight=1, slot="under_torso",
                                  description="A simple starter tunic."),
        "over_torso": None,
        "under_legs": make_item("Traveler's Trousers", "clothing", 10, weight=1, slot="under_legs",
                                 description="Comfortable trousers for long walks."),
        "over_legs": None,
        "feet": make_item("Worn Shoes", "clothing", 8, weight=1, slot="feet",
                           description="Simple shoes with a lot of miles left in them."),
        "back": make_item("Traveler's Backpack", "container", 35, weight=2, slot="back",
                           description="A basic backpack with room for road supplies.", capacity_bonus=12),
        "main_hand": make_item("Rusty Shortsword", "weapon", 25, weight=2, slot="main_hand",
                                description="A plain but serviceable starter blade."),
        "off_hand": None,
        "ring": None,
    }


def normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize an item dictionary and fill missing defaults."""
    normalized = make_item(
        item.get("name", "Unknown Item"),
        item.get("category", "misc"),
        item.get("price", 0),
        quantity=item.get("quantity", 1),
        weight=item.get("weight", 1),
        stackable=item.get("stackable", False),
        slot=item.get("slot"),
        description=item.get("description", ""),
        capacity_bonus=item.get("capacity_bonus", 0),
        rarity=item.get("rarity", "common"),
    )
    return normalized


def normalize_inventory(items: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    """Normalize an inventory list."""
    return [normalize_item(item) for item in (items or [])]


def normalize_equipment(equipment: Dict[str, Dict[str, Any] | None] | None) -> Dict[str, Dict[str, Any] | None]:
    """Normalize equipment slots and values."""
    normalized = {slot: None for slot in EQUIPMENT_SLOTS}
    for slot, item in (equipment or {}).items():
        if slot in normalized and item:
            normalized[slot] = normalize_item(item)
    return normalized


def ensure_player_state(player) -> None:
    """Ensure a player object has economy, inventory, and equipment defaults."""
    if getattr(player, "gold", None) is None:
        player.gold = 150
    if getattr(player, "inventory", None) is None:
        player.inventory = default_player_inventory()
    else:
        player.inventory = normalize_inventory(player.inventory)

    if getattr(player, "equipment", None) is None:
        player.equipment = default_player_equipment()
    else:
        player.equipment = normalize_equipment(player.equipment)


def inventory_capacity(player) -> int:
    """Calculate player carrying capacity."""
    ensure_player_state(player)
    base_capacity = 8
    back_item = player.equipment.get("back")
    if back_item:
        base_capacity += back_item.get("capacity_bonus", 0)
    return base_capacity


def inventory_weight(player) -> int:
    """Calculate the weight of carried inventory."""
    ensure_player_state(player)
    return sum(item.get("weight", 1) * item.get("quantity", 1) for item in player.inventory)


def can_add_item(player, item: Dict[str, Any]) -> Tuple[bool, str]:
    """Check whether an item can be added to the player's inventory."""
    ensure_player_state(player)
    projected = inventory_weight(player) + (item.get("weight", 1) * item.get("quantity", 1))
    capacity = inventory_capacity(player)
    if projected > capacity:
        return False, f"That would exceed carrying capacity ({projected}/{capacity})."
    return True, ""


def add_item_to_inventory(player, item: Dict[str, Any]) -> Tuple[bool, str]:
    """Add an item to player inventory."""
    ensure_player_state(player)
    item = normalize_item(item)
    can_add, message = can_add_item(player, item)
    if not can_add:
        return False, message

    if item.get("stackable"):
        for existing in player.inventory:
            if existing["name"] == item["name"]:
                existing["quantity"] += item["quantity"]
                return True, ""

    player.inventory.append(item)
    return True, ""


def remove_item_from_inventory(player, item_name: str, quantity: int = 1) -> Tuple[bool, str]:
    """Remove an item from inventory."""
    ensure_player_state(player)
    for index, item in enumerate(player.inventory):
        if item["name"] == item_name:
            if item["quantity"] < quantity:
                return False, "Not enough quantity available."
            item["quantity"] -= quantity
            if item["quantity"] <= 0:
                del player.inventory[index]
            return True, ""
    return False, f"{item_name} is not in inventory."


def equip_item(player, item_name: str, slot: str) -> Tuple[bool, str]:
    """Equip an inventory item into a slot."""
    ensure_player_state(player)
    if slot not in EQUIPMENT_SLOTS:
        return False, f"Unknown equipment slot: {slot}"

    for index, item in enumerate(player.inventory):
        if item["name"] == item_name:
            item_slot = item.get("slot")
            if item_slot != slot:
                return False, f"{item_name} fits in {item_slot or 'no slot'}, not {slot}."

            to_equip = deepcopy(item)
            to_equip["quantity"] = 1
            old_item = player.equipment.get(slot)
            player.equipment[slot] = to_equip

            if item["quantity"] > 1:
                player.inventory[index]["quantity"] -= 1
            else:
                del player.inventory[index]

            if old_item:
                add_item_to_inventory(player, old_item)
            return True, ""

    return False, f"{item_name} is not available to equip."


def unequip_item(player, slot: str) -> Tuple[bool, str]:
    """Move an equipped item back into inventory."""
    ensure_player_state(player)
    item = player.equipment.get(slot)
    if not item:
        return False, "Nothing is equipped in that slot."

    can_add, message = can_add_item(player, item)
    if not can_add:
        return False, message

    player.equipment[slot] = None
    add_item_to_inventory(player, item)
    return True, ""


def summarize_inventory(items: List[Dict[str, Any]]) -> str:
    """Build a compact summary string."""
    if not items:
        return "nothing"
    return ", ".join(
        f"{item['name']} x{item['quantity']}" if item.get("quantity", 1) > 1 else item["name"]
        for item in items
    )


def summarize_equipment(equipment: Dict[str, Dict[str, Any] | None]) -> str:
    """Build a compact equipment summary."""
    parts = []
    for slot, label in EQUIPMENT_SLOTS.items():
        item = equipment.get(slot)
        parts.append(f"{label}: {item['name'] if item else 'empty'}")
    return "; ".join(parts)
