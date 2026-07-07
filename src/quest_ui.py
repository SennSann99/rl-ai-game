"""Refined presentation UI for the castle quest."""

from __future__ import annotations

import math
import pygame

from .ui import GameUI, PANEL_WIDTH


class QuestUI(GameUI):
    def __init__(self, config: dict):
        super().__init__(config)
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
        legend = [(theme["agent"], "AI勇者"), (theme["reward"], "お城"),
                  (theme["hazard"], "危険な道"), (theme["enemy"], "モンスター"), ((112, 126, 159), "壁")]
        x = 24
        for color, label in legend:
            pygame.draw.circle(self.screen, color, (x + 6, y + 7), 6)
            self.screen.blit(self.small.render(label, True, theme["text"]), (x + 17, y))
            x += 124
        game = self.current_game
        card_y, gap = y + 45, 12
        card_width = (self.arena_width - 48 - gap * 2) // 3
        visible_enemies = sum(game.agent_can_see(enemy.position) for enemy in game.enemies)
        visible_hazards = sum(game.agent_can_see(hazard.position) for hazard in game.hazards)
        remaining = game._goal_distances.get(game.agent_position, game.start_distance)
        cards = [
            ("現在の旅", [f"城まで残り {remaining} マス", f"現在 {game.steps} 歩目", game.last_outcome]),
            ("勇者に見えているもの", [f"モンスター {visible_enemies} 体", f"危険な道 {visible_hazards} 個", "青い範囲が勇者の視野"]),
            ("報酬ルール", [f"城に到着  +{game.config['gem_reward']:.0f}", f"危険な道  {game.config['hazard_penalty']:.0f}", f"捕まる  {game.config['enemy_penalty']:.0f}"]),
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
        status = "準備中" if paused else ("冒険を学習中" if game.mode == "training" else "学んだ道で冒険中")
        self.screen.blit(self.font.render(f"●  {status}", True, theme["agent"]), (left, 55))
        self._button("pause", "冒険を始める" if paused else "一時停止", left, 88, 126, theme, primary=True)
        self._button("reset", "学習をリセット", left + 136, 88, 145, theme)
        self._button("mode", "おためし" if game.mode == "training" else "学習", left + 291, 88, 95, theme)

        y = 139
        self.screen.blit(self.small.render(game.last_outcome, True, theme["text"]), (left, y))
        y += 27
        self.screen.blit(self.small.render("お城までの進み具合", True, theme["text"]), (left, y))
        progress_rect = pygame.Rect(left, y + 23, width, 14)
        pygame.draw.rect(self.screen, (205, 199, 186), progress_rect, border_radius=7)
        filled = progress_rect.copy()
        filled.width = max(4, int(progress_rect.width * game.journey_progress()))
        pygame.draw.rect(self.screen, theme["reward"], filled, border_radius=7)
        y += 54

        cards = [("エピソード", str(game.episode)), ("今回の歩数", str(game.steps)),
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
        y = self._parameter("speed_down", "speed_up", "勇者の速さ", f"毎秒 {speed:g} 歩", left, y, width, theme)
        y = self._parameter("enemy_slower", "enemy_faster", "モンスターの速さ",
                            f"{game.config['enemy_speed']} 歩ごと", left, y, width, theme)
        sight = f"視野　勇者 {game.config['agent_vision_range']}マス　／　モンスター {game.config['monster_vision_range']}マス"
        self.screen.blit(self.small.render(sight, True, theme["text"]), (left, y - 4))
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
