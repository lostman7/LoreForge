from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox, QFrame, QProgressBar, QGraphicsColorizeEffect
)
from PyQt6.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QPoint, QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
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

        # Audio setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setSource(QUrl.fromLocalFile(str(ASSET_DIR / "BattleBM.mp3")))
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.media_player.play()

        # Combat stats initialization
        stats = self.player.reputation.get("_stats", {})
        self.player_hp = stats.get("hp", 100)
        self.player_max_hp = stats.get("max_hp", 100)
        self.player_speed = stats.get("speed", 10)

        # Monster stats
        self.monster_speed = 5 + self.monster_level * 2
        self.monster_attack = 5 + self.monster_level * 3

        self.is_player_turn = self.player_speed >= self.monster_speed

        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        # Battle Background Widget
        self.battle_frame = QFrame()
        self.battle_frame.setFixedSize(580, 300)

        bg_path = ASSET_DIR / "BattleBG.png"
        if bg_path.exists():
            bg_pixmap = QPixmap(str(bg_path)).scaled(580, 300, Qt.AspectRatioMode.IgnoreAspectRatio)
            palette = QPalette()
            palette.setBrush(QPalette.ColorRole.Window, QBrush(bg_pixmap))
            self.battle_frame.setAutoFillBackground(True)
            self.battle_frame.setPalette(palette)

        # Monster Sprite Position (Centered on dirt patch)
        self.monster_label = QLabel(self.battle_frame)
        monster_path = ASSET_DIR / self.monster_asset
        if monster_path.exists():
            pixmap = QPixmap(str(monster_path)).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio)
            self.monster_label.setPixmap(pixmap)
            # Rough positioning for the 'dirt patch' center in BattleBG.png
            self.monster_label.setGeometry(230, 130, 120, 120)

        self.main_layout.addWidget(self.battle_frame)

        # Monster Stats
        self.stats_label = QLabel(f"{self.monster_name} (Level {self.monster_level}) - HP: {self.monster_hp}/{self.max_hp}")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.main_layout.addWidget(self.stats_label)

        # Player HUD with HP bars
        hud_layout = QHBoxLayout()

        self.player_hp_bar = QProgressBar()
        self.player_hp_bar.setMaximum(self.player_max_hp)
        self.player_hp_bar.setValue(self.player_hp)
        self.player_hp_bar.setFormat(f"Player HP: %v/%m")
        self.player_hp_bar.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")

        self.monster_hp_bar = QProgressBar()
        self.monster_hp_bar.setMaximum(self.max_hp)
        self.monster_hp_bar.setValue(self.monster_hp)
        self.monster_hp_bar.setFormat(f"Monster HP: %v/%m")
        self.monster_hp_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")

        hud_layout.addWidget(self.player_hp_bar)
        hud_layout.addWidget(self.monster_hp_bar)
        self.main_layout.addLayout(hud_layout)

        # Controls
        btn_layout = QHBoxLayout()
        self.attack_btn = QPushButton("⚔️ Attack")
        self.attack_btn.clicked.connect(self.attack_monster)
        btn_layout.addWidget(self.attack_btn)

        self.items_btn = QPushButton("🎒 Items")
        self.items_btn.clicked.connect(self.use_item)
        btn_layout.addWidget(self.items_btn)

        self.flee_btn = QPushButton("🏃 Run Away")
        self.flee_btn.clicked.connect(self.run_away)
        btn_layout.addWidget(self.flee_btn)

        self.main_layout.addLayout(btn_layout)

    def show_damage_feedback(self, target_widget, amount, is_monster=True):
        """Visual hit feedback: Floating numbers and color flash."""
        # Floating Number
        label = QLabel(f"-{amount}", self.battle_frame if is_monster else self)
        label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 20px; background: transparent;")

        if is_monster:
            start_pos = self.monster_label.pos() + QPoint(40, -20)
        else:
            start_pos = self.player_hp_bar.pos() + QPoint(100, -30)

        label.move(start_pos)
        label.show()

        # Animation
        anim = QPropertyAnimation(label, b"pos")
        anim.setDuration(800)
        anim.setStartValue(start_pos)
        anim.setEndValue(start_pos + QPoint(0, -60))
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Fade/Delete
        QTimer.singleShot(800, label.deleteLater)
        anim.start()
        self._active_anims = getattr(self, '_active_anims', [])
        self._active_anims.append(anim)

        # Color Flash
        effect = QGraphicsColorizeEffect()
        effect.setColor(QColor(255, 0, 0))
        target_widget.setGraphicsEffect(effect)

        flash_timer = QTimer(self)
        flash_timer.setSingleShot(True)
        flash_timer.timeout.connect(lambda: target_widget.setGraphicsEffect(None))
        flash_timer.start(150)

    def attack_monster(self):
        if not self.is_player_turn: return

        # Player Attack
        damage = random.randint(10, 20) + (self.player_speed // 2)
        self.monster_hp = max(0, self.monster_hp - damage)

        self.show_damage_feedback(self.monster_label, damage, is_monster=True)
        self.update_status(f"You struck the {self.monster_name} for {damage} damage!")
        self.refresh_stats_display()

        if self.monster_hp <= 0:
            QTimer.singleShot(800, self.victory)
        else:
            self.is_player_turn = False
            QTimer.singleShot(1200, self.monster_turn)

    def monster_turn(self):
        # Evasion check: player speed reduces monster hit chance
        evasion_chance = min(40, self.player_speed - self.monster_speed + 10)
        if random.randint(1, 100) <= evasion_chance:
            self.update_status(f"The {self.monster_name} lunged, but you dodged!")
        else:
            damage = max(1, self.monster_attack - random.randint(0, 5))
            self.player_hp = max(0, self.player_hp - damage)

            self.show_damage_feedback(self.player_hp_bar, damage, is_monster=False)
            self.update_status(f"The {self.monster_name} hit you for {damage} damage!")

        self.refresh_stats_display()

        if self.player_hp <= 0:
            QTimer.singleShot(800, self.defeat)
        else:
            self.is_player_turn = True
            self.update_status("Your turn!")

    def run_away(self):
        penalty = min(self.player.gold, 25 + self.monster_level * 5)
        self.player.remove_gold(penalty)
        QMessageBox.information(self, "Escaped", f"You fled the battle but dropped {penalty}g in the chaos!")
        self.battle_result_narrative = f"You retreated from the {self.monster_name}, losing {penalty} gold during your flight."
        self.reject()

    def update_status(self, text):
        self.stats_label.setText(text)

    def refresh_stats_display(self):
        self.player_hp_bar.setValue(self.player_hp)
        self.monster_hp_bar.setValue(self.monster_hp)
        self.attack_btn.setEnabled(self.is_player_turn)
        self.items_btn.setEnabled(self.is_player_turn)
        self.flee_btn.setEnabled(self.is_player_turn)

    def use_item(self):
        QMessageBox.information(self, "Items", "You have no usable combat items!")

    def victory(self):
        self.media_player.stop()
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

    def defeat(self):
        self.media_player.stop()
        QMessageBox.warning(self, "Defeat", f"You were overwhelmed by the {self.monster_name}!")
        self.reject()

    def closeEvent(self, event):
        self.media_player.stop()
        super().closeEvent(event)

    def get_result_summary(self) -> str:
        if not self.battle_result_narrative:
            self.battle_result_narrative = get_battle_narrative(self.monster_name, victory=False)
        return (
            f"{self.battle_result_narrative}\n\n"
            f"Battle outcome for Level {self.monster_level} {self.monster_name}: {self.gold_reward} Gold and {self.xp_reward} XP."
        )
