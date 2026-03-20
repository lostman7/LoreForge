from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
import random
import math
from pathlib import Path
from src.game.content import (
    get_monster_pool,
    calculate_monster_level,
    ASSET_DIR,
    get_battle_narrative
)
from src.game.economy import make_item

class BattleDialog(QDialog):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setWindowTitle("Monster Encounter")
        self.resize(600, 450)
        self.setModal(True)

        # Load random monster
        monster_template = random.choice(get_monster_pool())

        # Calculate scaling
        # Assuming player has a 'level' attribute in reputation or similar,
        # but the prompt says Player Level 1 = Monster Level 1 etc.
        # Let's check player.reputation for a level or default to 1
        player_level = self.player.reputation.get("_stats", {}).get("level", 1)
        self.monster_level = calculate_monster_level(player_level)

        self.monster_name = monster_template["name"]
        self.monster_hp = monster_template["base_hp"] + (self.monster_level - 1) * 10
        self.max_hp = self.monster_hp
        self.xp_reward = monster_template["base_xp"] + (self.monster_level - 1) * 5
        self.gold_min, self.gold_max = monster_template["base_gold"]
        self.gold_reward = random.randint(self.gold_min, self.gold_max) + (self.monster_level - 1) * 3

        self.monster_asset = monster_template["asset"]
        self.battle_result_narrative = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Battle Background
        bg_path = ASSET_DIR / "BattleBG.png"
        self.bg_label = QLabel()
        if bg_path.exists():
            pixmap = QPixmap(str(bg_path)).scaled(580, 250, Qt.AspectRatioMode.KeepAspectRatio)
            self.bg_label.setPixmap(pixmap)
        self.bg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.bg_label)

        # Monster Display
        monster_path = ASSET_DIR / self.monster_asset
        self.monster_label = QLabel()
        if monster_path.exists():
            pixmap = QPixmap(str(monster_path)).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
            self.monster_label.setPixmap(pixmap)
        self.monster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.monster_label)

        # Monster Stats
        self.stats_label = QLabel(f"{self.monster_name} (Level {self.monster_level}) - HP: {self.monster_hp}/{self.max_hp}")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.stats_label)

        # Controls
        btn_layout = QHBoxLayout()
        self.attack_btn = QPushButton("⚔️ Attack")
        self.attack_btn.clicked.connect(self.attack_monster)
        btn_layout.addWidget(self.attack_btn)

        self.flee_btn = QPushButton("🏃 Flee")
        self.flee_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.flee_btn)

        layout.addLayout(btn_layout)

    def attack_monster(self):
        # Simple attack logic
        damage = random.randint(5, 15)
        self.monster_hp -= damage
        if self.monster_hp < 0:
            self.monster_hp = 0

        self.stats_label.setText(f"{self.monster_name} (Level {self.monster_level}) - HP: {self.monster_hp}/{self.max_hp}")

        if self.monster_hp <= 0:
            self.victory()

    def victory(self):
        # Resolve battle
        self.player.add_gold(self.gold_reward)
        # Assuming XP goes into reputation stats for now
        stats = self.player.reputation.get("_stats", {})
        current_xp = stats.get("xp", 0)
        stats["xp"] = current_xp + self.xp_reward
        self.player.reputation["_stats"] = stats

        self.battle_result_narrative = get_battle_narrative(self.monster_name, victory=True)

        msg = f"Victory! You defeated a Level {self.monster_level} {self.monster_name}!\n\n"
        msg += f"{self.battle_result_narrative}\n\n"
        msg += f"Rewards: {self.gold_reward} Gold and {self.xp_reward} XP."

        QMessageBox.information(self, "Battle Result", msg)
        self.accept()

    def get_result_summary(self) -> str:
        if not self.battle_result_narrative:
            self.battle_result_narrative = get_battle_narrative(self.monster_name, victory=False)
        return (
            f"{self.battle_result_narrative}\n\n"
            f"You defeated a Level {self.monster_level} {self.monster_name} and found {self.gold_reward} Gold!"
        )
