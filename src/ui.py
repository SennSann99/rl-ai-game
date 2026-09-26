"""Pygame drawing helpers and clickable presenter controls."""

from __future__ import annotations

import math
from pathlib import Path
import pygame


PANEL_WIDTH = 430
MIN_HEIGHT = 820


class GameUI:
    def __init__(self, config: dict):
        self.config = config
        self.cell = config["cell_size"]
        self.arena_width = config["grid_width"] * self.cell
        self.arena_height = config["grid_height"] * self.cell
        self.height = max(self.arena_height, MIN_HEIGHT)
        self.screen = pygame.display.set_mode((self.arena_width + PANEL_WIDTH, self.height))
        pygame.display.set_caption("AIトレジャーダッシュ — AIの学習を見てみよう！")
        bundled_candidates = [
            Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
            Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
            Path("/Library/Fonts/NotoSansCJK-Regular.ttc"),
        ]
        font_path = next((str(path) for path in bundled_candidates if path.exists()), None)
        if font_path is None:
            font_path = pygame.font.match_font(["Noto Sans CJK JP", "Yu Gothic", "Arial"])
        self.font = pygame.font.Font(font_path, 18)
        self.small = pygame.font.Font(font_path, 14)
        self.title = pygame.font.Font(font_path, 25)
        self.button_font = pygame.font.Font(font_path, 15)
        self.buttons: dict[str, pygame.Rect] = {}

    def draw(self, game, paused: bool, speed: float) -> None:
        theme = self.config["theme"]
        self.screen.fill((245, 247, 255))
        self._draw_decorations()
        self._draw_grid(theme)
        if hasattr(game, "visible_cells"):
            self._draw_vision(game, theme)
        for wall in getattr(game, "walls", set()):
            self._draw_wall(wall, theme)
        for hazard in game.hazards:
            rect = self._cell_rect(hazard.position).inflate(-10, -10)
            shadow = rect.move(3, 4)
            pygame.draw.rect(self.screen, (218, 196, 210), shadow, border_radius=14)
            pygame.draw.rect(self.screen, theme["hazard"], rect, border_radius=14)
            cx, cy = rect.center
            pygame.draw.polygon(self.screen, (255, 245, 247),
                                [(cx, cy - 17), (cx + 18, cy + 15), (cx - 18, cy + 15)])
            pygame.draw.line(self.screen, theme["hazard"], (cx, cy - 8), (cx, cy + 5), 4)
            pygame.draw.circle(self.screen, theme["hazard"], (cx, cy + 10), 2)
        for gem in game.gems:
            if getattr(game, "is_quest", False):
                self._draw_castle(gem.position, theme)
                continue
            cx, cy = self._center(gem.position)
            points = [(cx, cy - 20), (cx + 16, cy), (cx, cy + 20), (cx - 16, cy)]
            pygame.draw.polygon(self.screen, (219, 197, 136), [(x + 3, y + 4) for x, y in points])
            pygame.draw.polygon(self.screen, theme["reward"], points)
            pygame.draw.polygon(self.screen, (255, 245, 190), points, 3)
            pygame.draw.circle(self.screen, (255, 255, 238), (cx - 5, cy - 7), 4)
        for coin in getattr(game, "coins", []):
            self._draw_coin(coin.position, theme)
        for enemy in game.enemies:
            cx, cy = self._center(enemy.position)
            pygame.draw.circle(self.screen, (206, 193, 225), (cx + 3, cy + 4), self.cell // 3)
            pygame.draw.circle(self.screen, theme["enemy"], (cx, cy), self.cell // 3)
            pygame.draw.circle(self.screen, (255, 255, 255), (cx - 10, cy - 6), 5)
            pygame.draw.circle(self.screen, (255, 255, 255), (cx + 10, cy - 6), 5)
            pygame.draw.circle(self.screen, (73, 62, 105), (cx - 10, cy - 6), 2)
            pygame.draw.circle(self.screen, (73, 62, 105), (cx + 10, cy - 6), 2)
            pygame.draw.arc(self.screen, (255, 245, 255), (cx - 8, cy + 1, 16, 11), math.pi, math.tau, 2)
            if getattr(enemy, "alerted", False):
                pygame.draw.circle(self.screen, theme["hazard"], (cx, cy), self.cell // 2 - 3, 3)
                self.screen.blit(self.button_font.render("!", True, theme["hazard"]), (cx + 20, cy - 29))
        self._draw_agent(game.agent_position, theme["agent"])
        if hasattr(game, "discovered_cells") and getattr(game, "access_mode", "player") == "player":
            self._draw_fog_of_war(game)
        self._draw_arena_legend(theme)
        self._draw_panel(game, paused, speed, theme)
        pygame.display.flip()

    def action_at(self, position: tuple[int, int]) -> str | None:
        """Return the action for a clicked control, if any."""
        for action, rect in self.buttons.items():
            if rect.collidepoint(position):
                return action
        return None

    def _draw_grid(self, theme: dict) -> None:
        for y in range(self.config["grid_height"]):
            for x in range(self.config["grid_width"]):
                color = (248, 250, 255) if (x + y) % 2 == 0 else (240, 244, 254)
                pygame.draw.rect(self.screen, color, self._cell_rect((x, y)))
        for x in range(0, self.arena_width + 1, self.cell):
            pygame.draw.line(self.screen, theme["grid"], (x, 0), (x, self.arena_height))
        for y in range(0, self.arena_height + 1, self.cell):
            pygame.draw.line(self.screen, theme["grid"], (0, y), (self.arena_width, y))

    def _draw_fog_of_war(self, game) -> None:
        """Hide all objects and terrain outside the hero's remembered field of view."""
        for y in range(game.height):
            for x in range(game.width):
                if (x, y) not in game.discovered_cells:
                    rect = self._cell_rect((x, y))
                    pygame.draw.rect(self.screen, (52, 59, 71), rect)
                    pygame.draw.rect(self.screen, (72, 81, 96), rect, 1)

    def _draw_vision(self, game, theme: dict) -> None:
        overlay = pygame.Surface((self.arena_width, self.arena_height), pygame.SRCALPHA)
        for position in game.visible_cells(game.agent_position):
            pygame.draw.rect(overlay, (*theme["agent"], 22), self._cell_rect(position))
        for enemy in game.enemies:
            for position in game.visible_cells(enemy.position):
                pygame.draw.rect(overlay, (*theme["enemy"], 14), self._cell_rect(position))
        self.screen.blit(overlay, (0, 0))

    def _draw_wall(self, position, theme: dict) -> None:
        rect = self._cell_rect(position).inflate(-7, -7)
        pygame.draw.rect(self.screen, (174, 185, 211), rect.move(3, 4), border_radius=9)
        pygame.draw.rect(self.screen, (112, 126, 159), rect, border_radius=9)
        brick = (150, 164, 194)
        pygame.draw.line(self.screen, brick, (rect.left, rect.centery), (rect.right, rect.centery), 2)
        pygame.draw.line(self.screen, brick, (rect.centerx, rect.top), (rect.centerx, rect.centery), 2)
        pygame.draw.line(self.screen, brick, (rect.left + rect.width // 3, rect.centery),
                         (rect.left + rect.width // 3, rect.bottom), 2)

    def _draw_arena_legend(self, theme: dict) -> None:
        if self.height <= self.arena_height:
            return
        y = self.arena_height + 22
        self.screen.blit(self.font.render("ごほうびと失敗から、AIが学んでいくよ！", True, theme["text"]), (22, y))
        y += 34
        legend = [(theme["reward"], "+ 宝石"), (theme["hazard"], "- 危険マス"),
                  (theme["enemy"], "- モンスター"), (theme["agent"], "AIロボット")]
        x = 22
        for color, label in legend:
            pygame.draw.circle(self.screen, color, (x + 7, y + 8), 7)
            self.screen.blit(self.small.render(label, True, theme["text"]), (x + 20, y))
            x += 145

    def _draw_decorations(self) -> None:
        """Small pastel dots make the unused lower arena feel intentional."""
        dots = [((36, 675), 5, (255, 200, 77)), ((610, 620), 7, (181, 126, 255)),
                ((590, 755), 4, (77, 183, 255)), ((75, 760), 6, (255, 153, 180))]
        for position, radius, color in dots:
            pygame.draw.circle(self.screen, color, position, radius)

    def _draw_agent(self, position, color) -> None:
        cx, cy = self._center(position)
        pygame.draw.circle(self.screen, (190, 211, 231), (cx + 3, cy + 4), self.cell // 3)
        pygame.draw.circle(self.screen, color, (cx, cy), self.cell // 3)
        pygame.draw.rect(self.screen, (225, 248, 255), (cx - 17, cy - 15, 34, 26), border_radius=9)
        pygame.draw.circle(self.screen, (220, 245, 255), (cx - 10, cy - 7), 5)
        pygame.draw.circle(self.screen, (220, 245, 255), (cx + 10, cy - 7), 5)
        pygame.draw.arc(self.screen, (57, 88, 120), (cx - 10, cy - 2, 20, 14), 0, math.pi, 2)
        pygame.draw.line(self.screen, (57, 88, 120), (cx, cy - 16), (cx, cy - 23), 2)
        pygame.draw.circle(self.screen, (255, 113, 128), (cx, cy - 25), 3)

    def _draw_castle(self, position, theme: dict) -> None:
        cx, cy = self._center(position)
        stone, roof, light = (91, 101, 122), theme["reward"], (247, 239, 211)
        pygame.draw.rect(self.screen, (170, 161, 145), (cx - 21, cy - 14, 46, 38), border_radius=5)
        pygame.draw.rect(self.screen, stone, (cx - 23, cy - 18, 46, 38), border_radius=4)
        pygame.draw.rect(self.screen, stone, (cx - 18, cy - 26, 11, 15))
        pygame.draw.rect(self.screen, stone, (cx + 7, cy - 26, 11, 15))
        pygame.draw.polygon(self.screen, roof, [(cx - 20, cy - 25), (cx - 12, cy - 35), (cx - 4, cy - 25)])
        pygame.draw.polygon(self.screen, roof, [(cx + 5, cy - 25), (cx + 12, cy - 35), (cx + 20, cy - 25)])
        pygame.draw.rect(self.screen, light, (cx - 5, cy + 3, 10, 17), border_radius=5)
        pygame.draw.line(self.screen, stone, (cx, cy - 35), (cx, cy - 45), 2)
        pygame.draw.polygon(self.screen, theme["hazard"], [(cx, cy - 45), (cx + 12, cy - 41), (cx, cy - 37)])

    def _draw_coin(self, position, theme: dict) -> None:
        cx, cy = self._center(position)
        pygame.draw.circle(self.screen, (173, 133, 53), (cx + 2, cy + 3), 13)
        pygame.draw.circle(self.screen, theme["reward"], (cx, cy), 13)
        pygame.draw.circle(self.screen, (255, 240, 180), (cx - 3, cy - 4), 5)
        pygame.draw.circle(self.screen, (173, 133, 53), (cx, cy), 8, 2)
        self.screen.blit(self.small.render("C", True, (126, 91, 35)),
                         self.small.render("C", True, (126, 91, 35)).get_rect(center=(cx, cy)))

    def _draw_panel(self, game, paused: bool, speed: float, theme: dict) -> None:
        x = self.arena_width
        pygame.draw.rect(self.screen, theme["panel"], (x, 0, PANEL_WIDTH, self.height))
        self.buttons.clear()
        left, width = x + 22, PANEL_WIDTH - 44
        title = getattr(game, "display_title", "AIトレジャーダッシュ")
        self.screen.blit(self.title.render(title, True, theme["text"]), (left, 18))
        status = "一時停止中" if paused else ("学習中" if game.mode == "training" else "おためし中")
        self.screen.blit(self.font.render(f"●  {status}", True, theme["agent"]), (left, 55))

        self._button("pause", "スタート" if paused else "一時停止", left, 88, 116, theme, primary=True)
        self._button("reset", "学習をリセット", left + 126, 88, 145, theme)
        self._button("mode", "おためし" if game.mode == "training" else "学習", left + 281, 88, 105, theme)

        avg = sum(game.recent_scores) / len(game.recent_scores) if game.recent_scores else 0
        best = game.best_score if game.best_score != float("-inf") else 0
        stats = [f"エピソード  {game.episode}", f"スコア  {game.score:.1f}", f"直前の報酬  {game.last_reward:+.1f}",
                 f"探索率 ε  {game.agent.epsilon:.3f}", f"直近20回の平均  {avg:.1f}",
                 f"最高記録  {best:.1f}", f"学んだ状態  {len(game.agent.q_table)}"]
        for index, text in enumerate(stats):
            col, row = index % 2, index // 2
            color = theme["hazard"] if text.startswith("直前") and game.last_reward <= 0 else theme["text"]
            self.screen.blit(self.small.render(text, True, color), (left + col * 194, 137 + row * 25))

        y = 246
        self.screen.blit(self.font.render("リアルタイム設定", True, theme["text"]), (left, y))
        y += 36
        y = self._parameter("speed_down", "speed_up", "動く速さ", f"毎秒 {speed:g} 歩", left, y, width, theme)
        y = self._parameter("gem_down", "gem_up", "宝石の数", str(len(game.gems)), left, y, width, theme)
        y = self._parameter("hazard_down", "hazard_up", "危険マスの数", str(len(game.hazards)), left, y, width, theme)
        y = self._parameter("enemy_slower", "enemy_faster", "モンスターの速さ", f"{game.config['enemy_speed']} 歩ごと", left, y, width, theme)

        self.screen.blit(self.small.render("モンスターの動き", True, theme["text"]), (left, y + 8))
        if getattr(game, "locked_enemy_behavior", False):
            behavior = "視界で追跡（固定）"
        else:
            behavior = "追いかける" if game.enemy_behavior == "chase" else "ランダム"
        self._button("behavior", behavior, left + 224, y, 162, theme)
        y += 50

        self.screen.blit(self.font.render("AIの成長グラフ", True, theme["text"]), (left, y))
        y += 29
        self._draw_learning_plot(game.score_history, pygame.Rect(left, y, width, 105), theme)
        y += 118

        self.screen.blit(self.font.render("AIはどうやって学ぶの？", True, theme["text"]), (left, y))
        y += 31
        explanation = ("青いAIロボットはいろいろな動きを試し、宝石をもらえた行動と、"
                       "危険だった行動を覚えます。少しずつ経験を信じて動くようになります。")
        y = self._wrapped_text(explanation, left, y, width, theme["text"])
        y += 9
        keys = "キーボード：Space 開始・停止　R リセット　M モード　[ ] 速さ　Esc 終了"
        self._wrapped_text(keys, left, y, width, theme["text"])

    def _draw_learning_plot(self, scores: list[float], rect: pygame.Rect, theme: dict) -> None:
        """Plot episode scores and a five-episode moving average."""
        pygame.draw.rect(self.screen, theme["background"], rect, border_radius=5)
        pygame.draw.rect(self.screen, theme["grid"], rect, 1, border_radius=5)
        if len(scores) < 2:
            message = self.small.render("2エピソード終わるとグラフが表示されます", True, theme["text"])
            self.screen.blit(message, message.get_rect(center=rect.center))
            return
        low, high = min(scores), max(scores)
        if high == low:
            high += 1.0
        pad = 7

        def point(index: int, value: float) -> tuple[int, int]:
            x = rect.left + pad + int(index * (rect.width - 2 * pad) / (len(scores) - 1))
            y = rect.bottom - pad - int((value - low) * (rect.height - 2 * pad) / (high - low))
            return x, y

        raw = [point(i, value) for i, value in enumerate(scores)]
        pygame.draw.lines(self.screen, theme["grid"], False, raw, 1)
        averages = [sum(scores[max(0, i - 4):i + 1]) / min(5, i + 1) for i in range(len(scores))]
        trend = [point(i, value) for i, value in enumerate(averages)]
        pygame.draw.lines(self.screen, theme["reward"], False, trend, 3)
        label = self.small.render("黄色：5エピソードの平均", True, theme["reward"])
        self.screen.blit(label, (rect.left + 8, rect.top + 5))

    def _parameter(self, minus: str, plus: str, label: str, value: str, x: int, y: int,
                   width: int, theme: dict) -> int:
        self.screen.blit(self.small.render(label, True, theme["text"]), (x, y + 8))
        self._button(minus, "-", x + 224, y, 44, theme)
        value_surface = self.small.render(value, True, theme["text"])
        self.screen.blit(value_surface, (x + 275, y + 9))
        self._button(plus, "+", x + width - 44, y, 44, theme)
        return y + 48

    def _button(self, action: str, label: str, x: int, y: int, width: int,
                theme: dict, primary: bool = False) -> None:
        rect = pygame.Rect(x, y, width, 34)
        self.buttons[action] = rect
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill = theme["agent"] if primary else ((207, 216, 243) if hovered else theme["grid"])
        shadow = rect.move(0, 3)
        pygame.draw.rect(self.screen, (199, 205, 225), shadow, border_radius=9)
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        color = (255, 255, 255) if primary else theme["text"]
        surface = self.button_font.render(label, True, color)
        self.screen.blit(surface, surface.get_rect(center=rect.center))

    def _wrapped_text(self, text: str, x: int, y: int, width: int, color) -> int:
        line = ""
        has_spaces = " " in text
        tokens = text.split() if has_spaces else list(text)
        for token in tokens:
            candidate = f"{line} {token}".strip() if has_spaces else line + token
            if self.small.size(candidate)[0] > width and line:
                self.screen.blit(self.small.render(line, True, color), (x, y))
                y += 20
                line = token
            else:
                line = candidate
        if line:
            self.screen.blit(self.small.render(line, True, color), (x, y))
            y += 20
        return y

    def _cell_rect(self, position) -> pygame.Rect:
        return pygame.Rect(position[0] * self.cell, position[1] * self.cell, self.cell, self.cell)

    def _center(self, position) -> tuple[int, int]:
        return (position[0] * self.cell + self.cell // 2, position[1] * self.cell + self.cell // 2)
