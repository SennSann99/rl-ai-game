"""Castle quest with fixed coins, fog-of-war, and bounded monsters."""

from __future__ import annotations

from collections import deque

from .advanced_game import AdvancedTreasureDash
from .objects import Enemy, Gem, Hazard, Position


class CastleQuest(AdvancedTreasureDash):
    display_title = "AI勇者のキャッスルクエスト"
    is_quest = True
    TRAINING_EPISODES = 100
    FIXED_STEP_LIMIT = 100
    MAX_COINS = 7

    def __init__(self, config: dict):
        self.successes = 0
        self.defeats = 0
        self.best_steps: int | None = None
        self.last_outcome = "設定者がコインと報酬を準備できます"
        self.coin_positions = [tuple(p) for p in config.get("coin_positions", [])][:self.MAX_COINS]
        self.coins: list[Gem] = []
        self.coins_enabled = True
        self.discovered_cells: set[Position] = set()
        self.training_started = False
        self.access_mode = "configurer"
        super().__init__(config)
        self.goal_position = tuple(config["reward_positions"][0])
        self._goal_distances = self._build_goal_distances()
        self.start_distance = self._goal_distances.get(self.start_position, 1)
        self.fixed_step_limit = self.FIXED_STEP_LIMIT
        self.config["episode_length"] = self.fixed_step_limit
        self.config["training_episodes"] = self.TRAINING_EPISODES
        self.reset_episode()

    @property
    def start_position(self) -> Position:
        configured = self.config.get("start_position")
        return tuple(configured) if configured is not None else (1, self.height - 2)

    @property
    def monster_regions(self) -> list[tuple[int, int, int, int]]:
        return [tuple(region) for region in self.config.get("monster_regions", [])]

    def reset_episode(self) -> None:
        self.walls = {tuple(p) for p in self.config["wall_positions"]}
        self.agent_position = self.start_position
        self.steps = 0
        self.score = 0.0
        self.last_reward = 0.0
        self.gems = [Gem(tuple(self.config["reward_positions"][0]), tuple(self.config["reward_positions"][0]))]
        self.coins = [Gem(position, position) for position in self.coin_positions] if self.coins_enabled else []
        self.hazards = [Hazard(tuple(p)) for p in self.config["hazard_positions"]]
        positions = self.config.get("enemy_positions", [])
        self.enemies = [Enemy(tuple(p)) for p in positions]
        self.discovered_cells.update(self.visible_cells(self.agent_position))

    def begin_training(self) -> None:
        if self.training_started:
            return
        self.training_started = True
        self.discovered_cells.clear()
        self.agent.reset()
        self.episode = 0
        self.best_score = float("-inf")
        self.recent_scores.clear(); self.score_history.clear()
        self.successes = self.defeats = 0
        self.best_steps = None
        self.last_outcome = "100回の学習を開始しました"
        self.mode = "training"
        self.reset_episode()

    def return_to_setup(self) -> None:
        self.training_started = False
        self.agent.reset(); self.episode = 0; self.best_score = float("-inf")
        self.recent_scores.clear(); self.score_history.clear()
        self.successes = self.defeats = 0; self.best_steps = None
        self.discovered_cells.clear(); self.mode = "training"
        self.last_outcome = "設定を初期化しました"
        self.reset_episode()

    def toggle_access_mode(self) -> None:
        if not self.training_started:
            self.access_mode = "player" if self.access_mode == "configurer" else "configurer"

    def collect_coins(self) -> bool:
        if self.training_started or self.access_mode != "configurer" or not self.coins_enabled:
            return False
        self.coins_enabled = False; self.coins.clear(); self.last_outcome = "コインを回収しました"
        return True

    def revive_coins(self) -> bool:
        if self.training_started or self.access_mode != "configurer" or self.coins_enabled:
            return False
        self.coins_enabled = True
        self.coins = [Gem(position, position) for position in self.coin_positions]
        self.last_outcome = "コインを復活させました"
        return True

    def place_or_remove_coin(self, position: Position) -> bool:
        """Configurer-only board editing before learning starts; maximum seven coins."""
        if self.training_started or self.access_mode != "configurer":
            return False
        if position in self.coin_positions:
            self.coin_positions.remove(position)
            self.coins = [Gem(point, point) for point in self.coin_positions] if self.coins_enabled else []
            self.last_outcome = "コインを削除しました"
            return True
        if len(self.coin_positions) >= self.MAX_COINS or not self._valid_coin_cell(position):
            return False
        self.coin_positions.append(position)
        if self.coins_enabled:
            self.coins.append(Gem(position, position))
        self.last_outcome = "コインを配置しました"
        return True

    def _valid_coin_cell(self, position: Position) -> bool:
        x, y = position
        occupied = (self.walls | {self.start_position, self.goal_position} |
                    {hazard.position for hazard in self.hazards} |
                    {enemy.position for enemy in self.enemies})
        return 0 <= x < self.width and 0 <= y < self.height and position not in occupied

    def state(self) -> tuple:
        hazards = [obj for obj in self.hazards if self.agent_can_see(obj.position)]
        enemies = [obj for obj in self.enemies if self.agent_can_see(obj.position)]
        blocked = tuple(self._clamp((self.agent_position[0] + dx, self.agent_position[1] + dy)) in self.walls
                        or self._clamp((self.agent_position[0] + dx, self.agent_position[1] + dy)) == self.agent_position
                        for dx, dy in self.agent.ACTIONS)
        dx, dy = self.goal_position[0] - self.agent_position[0], self.goal_position[1] - self.agent_position[1]
        goal = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0), min(self._goal_distances.get(self.agent_position, 20), 20))
        return (self.agent_position, blocked, goal, self._nearest_signature(hazards), self._nearest_signature(enemies))

    def tick(self) -> bool:
        old_state = self.state()
        old_distance = self._goal_distances.get(self.agent_position, self.start_distance)
        action = self.agent.choose_action(old_state, training=self.mode == "training")
        dx, dy = self.agent.ACTIONS[action]
        candidate = self._clamp((self.agent_position[0] + dx, self.agent_position[1] + dy))
        if candidate not in self.walls:
            self.agent_position = candidate
        self.steps += 1
        if self.steps % self.config["enemy_speed"] == 0:
            self._move_enemies()
        self.discovered_cells.update(self.visible_cells(self.agent_position))
        new_distance = self._goal_distances.get(self.agent_position, old_distance)
        reward = self.config["step_penalty"] + self.config["progress_reward"] * (old_distance - new_distance)
        for coin in [coin for coin in self.coins if coin.position == self.agent_position]:
            self.coins.remove(coin); reward += self.config["coin_reward"]
        if any(h.position == self.agent_position for h in self.hazards): reward += self.config["hazard_penalty"]
        reached = self.agent_position == self.goal_position
        caught = any(enemy.position == self.agent_position for enemy in self.enemies)
        if reached: reward += self.config["gem_reward"]
        if caught: reward += self.config["enemy_penalty"]
        self.last_reward = reward; self.score += reward
        done = reached or caught or self.steps >= self.fixed_step_limit
        if self.mode == "training": self.agent.learn(old_state, action, reward, self.state(), done)
        if done:
            if reached:
                self.successes += 1; self.best_steps = self.steps if self.best_steps is None else min(self.best_steps, self.steps); self.last_outcome = f"お城に到着！ {self.steps}歩"
            elif caught:
                self.defeats += 1; self.last_outcome = "モンスターにつかまりました"
            else: self.last_outcome = "100歩で時間切れです"
            self._finish_episode()
        return done

    def _move_enemies(self) -> None:
        for index, enemy in enumerate(self.enemies):
            region = self.monster_regions[index] if index < len(self.monster_regions) else (0, 0, self.width, self.height)
            if self.monster_can_see(enemy, self.agent_position):
                enemy.last_seen = self.agent_position; enemy.alerted = True
            if enemy.last_seen is not None:
                enemy.position = self._region_path_step(enemy.position, enemy.last_seen, region)
            else:
                enemy.position = self._region_random_neighbor(enemy.position, region)

    def _region_path_step(self, start: Position, target: Position, region: tuple[int, int, int, int]) -> Position:
        queue = deque([start]); parent: dict[Position, Position | None] = {start: None}
        while queue:
            current = queue.popleft()
            for dx, dy in self.agent.ACTIONS:
                nxt = self._clamp((current[0] + dx, current[1] + dy))
                if nxt not in parent and nxt not in self.walls and self._inside_region(nxt, region):
                    parent[nxt] = current; queue.append(nxt)
        current = min(parent, key=lambda p: abs(p[0] - target[0]) + abs(p[1] - target[1]))
        while parent[current] not in (None, start): current = parent[current]  # type: ignore[assignment]
        return current

    def _region_random_neighbor(self, position: Position, region: tuple[int, int, int, int]) -> Position:
        candidates = [self._clamp((position[0] + dx, position[1] + dy)) for dx, dy in self.agent.ACTIONS + ((0, 0),)]
        candidates = [p for p in candidates if p not in self.walls and self._inside_region(p, region)]
        return self.rng.choice(candidates) if candidates else position

    @staticmethod
    def _inside_region(position: Position, region: tuple[int, int, int, int]) -> bool:
        x, y, width, height = region
        return x <= position[0] < x + width and y <= position[1] < y + height

    def journey_progress(self) -> float:
        remaining = self._goal_distances.get(self.agent_position, self.start_distance)
        return max(0.0, min(1.0, 1.0 - remaining / max(1, self.start_distance)))

    def goal_is_known(self) -> bool:
        return self.goal_position in self.discovered_cells

    def _build_goal_distances(self) -> dict[Position, int]:
        distances = {self.goal_position: 0}; queue = deque([self.goal_position])
        while queue:
            current = queue.popleft()
            for dx, dy in self.agent.ACTIONS:
                nxt = self._clamp((current[0] + dx, current[1] + dy))
                if nxt not in self.walls and nxt not in distances:
                    distances[nxt] = distances[current] + 1; queue.append(nxt)
        return distances
