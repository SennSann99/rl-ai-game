"""Refined presentation UI for the castle quest."""

from __future__ import annotations

import math
import pygame

from .ui import GameUI, PANEL_WIDTH


class QuestUI(GameUI):
    def __init__(self, config: dict):
        super().__init__(config)
        self.height = max(self.height, 1250)
        self.screen = pygame.display.set_mode((self.arena_width + PANEL_WIDTH, self.height))
        pygame.display.set_caption("AI勇者のキャッスルクエスト — 安全な道を学ぼう")

    def draw(self, game, paused: bool, speed: float) -> None:
        self.current_game = game
        super().draw(game, paused, speed)

    def _draw_grid(self, theme: dict) -> None:
        for y in range(self.config["grid_height"]):
            for x in range(self.config["grid_width"]):
                color = (244, 241, 233) if (x + y) % 2 == 0 else (237, 233, 223)
                pygame.draw.rect(self.screen, color, self._cell_rect((x, y)))
        for x in range(0, self.arena_width + 1, self.cell):
            pygame.draw.line(self.screen, theme["grid"], (x, 0), (x, self.arena_height), 1)
        for y in range(0, self.arena_height + 1, self.cell):
            pygame.draw.line(self.screen, theme["grid"], (0, y), (self.arena_width, y), 1)

    def _draw_decorations(self) -> None:
        for x, y, radius in [(42, 682, 3), (605, 733, 4), (84, 765, 2), (648, 642, 3)]:
            pygame.draw.circle(self.screen, (214, 165, 65), (x, y), radius)

    def _draw_agent(self, position, color) -> None:
        """Draw a compact knight instead of the robot used by other versions."""
        cx, cy = self._center(position)
        pygame.draw.ellipse(self.screen, (174, 166, 151), (cx - 18, cy - 17, 39, 43))
        pygame.draw.polygon(self.screen, (154, 55, 55),
                            [(cx - 13, cy + 2), (cx + 9, cy + 2), (cx + 15, cy + 24), (cx - 20, cy + 24)])
        pygame.draw.ellipse(self.screen, color, (cx - 15, cy - 13, 30, 35))
        # Silver helmet, face opening, and red plume.
        pygame.draw.circle(self.screen, (221, 226, 226), (cx, cy - 8), 13)
        pygame.draw.polygon(self.screen, (190, 199, 202),
                            [(cx - 13, cy - 9), (cx + 13, cy - 9), (cx + 8, cy - 2), (cx - 8, cy - 2)])
        pygame.draw.circle(self.screen, (45, 49, 53), (cx - 5, cy - 6), 2)
        pygame.draw.circle(self.screen, (45, 49, 53), (cx + 5, cy - 6), 2)
        pygame.draw.line(self.screen, (154, 55, 55), (cx, cy - 21), (cx + 5, cy - 30), 4)
        pygame.draw.line(self.screen, (191, 69, 69), (cx + 4, cy - 29), (cx + 11, cy - 24), 4)
        # Gold shield and visible sword.
        pygame.draw.polygon(self.screen, (214, 165, 65),
                            [(cx + 7, cy + 1), (cx + 20, cy + 5), (cx + 17, cy + 20), (cx + 8, cy + 15)])
        pygame.draw.line(self.screen, (247, 239, 211), (cx + 12, cy + 5), (cx + 14, cy + 15), 2)
        pygame.draw.line(self.screen, (205, 210, 211), (cx - 12, cy + 1), (cx - 22, cy + 18), 3)
        pygame.draw.line(self.screen, (214, 165, 65), (cx - 17, cy + 9), (cx - 10, cy + 14), 2)

    def _draw_arena_legend(self, theme: dict) -> None:
        if self.height <= self.arena_height:
            return
        y = self.arena_height + 22
        self.screen.blit(self.font.render("勇者は危険な道を学び、お城を目指します", True, theme["text"]), (24, y))
        y += 36
        legend = [(theme["agent"], "AI勇者"), (theme["reward"], "お城・コイン"),
                  (theme["hazard"], "危険な道"), (theme["enemy"], "モンスター"), ((112, 126, 159), "壁")]
        x = 24
        for color, label in legend:
            pygame.draw.circle(self.screen, color, (x + 6, y + 7), 6)
            self.screen.blit(self.small.render(label, True, theme["text"]), (x + 17, y))
            x += 124
        game = self.current_game
        card_y, gap = y + 45, 12
        card_width = (self.arena_width - 48 - gap * 2) // 3
        visible_enemies = len(game.enemies)
        visible_hazards = sum(game.agent_can_see(hazard.position) for hazard in game.hazards)
        remaining = game._goal_distances.get(game.agent_position, game.start_distance)
        destination = f"城まで残り {remaining} マス" if game.goal_is_known() else "目的地はまだ未発見"
        cards = [
            ("現在の旅", [destination, f"現在 {game.steps} 歩目", game.last_outcome]),
            ("勇者が把握しているもの", [f"モンスター全{visible_enemies}体の位置", f"危険な道 {visible_hazards} 個", "敵の位置は視野外でも把握"]),
            ("報酬ルール", [f"お城  +{game.config['gem_reward']:.0f}　コイン +{game.config['coin_reward']:.0f}", f"危険な道  {game.config['hazard_penalty']:.0f}", f"捕まる  {game.config['enemy_penalty']:.0f}"]),
        ]
        for index, (title, lines) in enumerate(cards):
            rect = pygame.Rect(24 + index * (card_width + gap), card_y, card_width, 132)
            pygame.draw.rect(self.screen, (231, 227, 217), rect.move(0, 3), border_radius=10)
            pygame.draw.rect(self.screen, (250, 248, 242), rect, border_radius=10)
            pygame.draw.rect(self.screen, theme["reward"], (rect.x, rect.y, 4, rect.height), border_radius=2)
            self.screen.blit(self.font.render(title, True, theme["text"]), (rect.x + 13, rect.y + 12))
            for row, line in enumerate(lines):
                clipped = line if len(line) <= 18 else line[:17] + "…"
                self.screen.blit(self.small.render(clipped, True, theme["text"]),
                                 (rect.x + 13, rect.y + 45 + row * 23))

    def _draw_panel(self, game, paused: bool, speed: float, theme: dict) -> None:
        x = self.arena_width
        pygame.draw.rect(self.screen, theme["panel"], (x, 0, PANEL_WIDTH, self.height))
        self.buttons.clear()
        left, width = x + 22, PANEL_WIDTH - 44

        self.screen.blit(self.title.render("AI勇者のキャッスルクエスト", True, theme["text"]), (left, 18))
        if not game.training_started:
            status = "コイン配置・設定中"
        elif game.mode == "training" and game.episode < game.TRAINING_EPISODES:
            status = f"{game.TRAINING_EPISODES}回の冒険を学習中"
        else:
            status = "学習済み勇者を再生中"
        self.screen.blit(self.font.render(f"●  {status}", True, theme["agent"]), (left, 55))
        role = "設定者モード" if game.access_mode == "configurer" else "体験者モード"
        self._button("role", role, left, 88, 115, theme)
        start_label = "学習を開始" if not game.training_started else ("再生を開始" if paused else "一時停止")
        self._button("pause", start_label, left + 125, 88, 130, theme, primary=True)
        self._button("reset", "設定をやり直す", left + 265, 88, 121, theme)
        if game.access_mode == "configurer" and not game.training_started:
            self._button("collect_coins", "コイン回収", left, 128, 184, theme)
            self._button("revive_coins", "コイン復活", left + 202, 128, 184, theme)

        y = 178
        setup_note = ("盤面クリックでコインを配置・削除（最大7枚）" if not game.training_started
                      else f"コイン位置は固定　／　1回 {game.fixed_step_limit} 歩")
        self.screen.blit(self.small.render(setup_note, True, theme["text"]), (left, y))
        y += 25
        coin_state = "復活中" if game.coins_enabled else "回収済み"
        self.screen.blit(self.small.render(f"コイン {len(game.coin_positions)} / {game.MAX_COINS} 枚（{coin_state}）　{game.last_outcome}", True, theme["text"]), (left, y))
        y += 27
        if game.goal_is_known():
            self.screen.blit(self.small.render("お城までの進み具合", True, theme["text"]), (left, y))
            progress_rect = pygame.Rect(left, y + 23, width, 14)
            pygame.draw.rect(self.screen, (205, 199, 186), progress_rect, border_radius=7)
            filled = progress_rect.copy()
            filled.width = max(4, int(progress_rect.width * game.journey_progress()))
            pygame.draw.rect(self.screen, theme["reward"], filled, border_radius=7)
        else:
            self.screen.blit(self.small.render("目的地を探索中：城の位置はまだ見えていません", True, theme["text"]), (left, y + 8))
        y += 54

        cards = [("エピソード", f"{game.episode} / {game.TRAINING_EPISODES}"), ("今回の歩数", f"{game.steps} / {game.fixed_step_limit}"),
                 ("お城に到着", f"{game.successes}回"), ("モンスター敗北", f"{game.defeats}回"),
                 ("最高記録", f"{game.best_steps}歩" if game.best_steps else "--"),
                 ("探索率", f"{game.agent.epsilon:.3f}")]
        for index, (label, value) in enumerate(cards):
            col, row = index % 3, index // 3
            rect = pygame.Rect(left + col * 130, y + row * 58, 120, 48)
            pygame.draw.rect(self.screen, (243, 240, 232), rect, border_radius=8)
            self.screen.blit(self.small.render(label, True, (105, 103, 98)), (rect.x + 9, rect.y + 6))
            self.screen.blit(self.font.render(value, True, theme["text"]), (rect.x + 9, rect.y + 23))
        y += 128

        self.screen.blit(self.font.render("冒険の設定", True, theme["text"]), (left, y))
        y += 33
        y = self._parameter("speed_down", "speed_up", "再生・学習の速さ", f"毎秒 {speed:g} 歩", left, y, width, theme)
        if game.access_mode == "configurer" and not game.training_started:
            y = self._parameter("enemy_slower", "enemy_faster", "モンスターの速さ",
                                f"{game.config['enemy_speed']} 歩ごと", left, y, width, theme)
            y = self._parameter("hero_vision_down", "hero_vision_up", "勇者の視野",
                                f"{game.config['agent_vision_range']} マス", left, y, width, theme)
            y = self._parameter("monster_vision_down", "monster_vision_up", "モンスターの視野",
                                f"{game.config['monster_vision_range']} マス", left, y, width, theme)
            y = self._parameter("coin_respawn_down", "coin_respawn_up", "コイン復活まで",
                                f"{game.config['coin_respawn_steps']} 歩", left, y, width, theme)
            self.screen.blit(self.font.render("報酬ルール", True, theme["text"]), (left, y))
            y += 33
            y = self._parameter("castle_reward_down", "castle_reward_up", "城の報酬",
                                f"{game.config['gem_reward']:.0f}", left, y, width, theme)
            y = self._parameter("coin_reward_down", "coin_reward_up", "コインの報酬",
                                f"{game.config['coin_reward']:.0f}", left, y, width, theme)
            y = self._parameter("hazard_penalty_down", "hazard_penalty_up", "危険マスの報酬",
                                f"{game.config['hazard_penalty']:.0f}", left, y, width, theme)
            y = self._parameter("enemy_penalty_down", "enemy_penalty_up", "捕獲時の報酬",
                                f"{game.config['enemy_penalty']:.0f}", left, y, width, theme)
        else:
            message = ("体験者モード：パラメータは固定です" if game.access_mode == "player"
                       else "学習開始後はパラメータを固定します")
            self.screen.blit(self.small.render(message, True, theme["text"]), (left, y))
            y += 24
            self.screen.blit(self.small.render(f"勇者の視野 {game.config['agent_vision_range']}マス　モンスター {game.config['monster_vision_range']}マス", True, theme["text"]), (left, y))
            y += 24

        self.screen.blit(self.font.render("学習の記録", True, theme["text"]), (left, y))
        y += 29
        self._draw_learning_plot(game.score_history, pygame.Rect(left, y, width, 105), theme)
        y += 121
        self.screen.blit(self.font.render("このAIが学ぶこと", True, theme["text"]), (left, y))
        y += 29
        explanation = "勇者は毎回同じ場所から出発し、危険な道とモンスターを避けながら、お城までの安全な道を少しずつ覚えます。"
        y = self._wrapped_text(explanation, left, y, width, theme["text"])
        self._wrapped_text("Space 開始・停止　R リセット　M モード　Esc 終了", left, y + 5, width, theme["text"])
