"""Advanced environment with limited sight, walls, and persistent hunters."""

from __future__ import annotations

from collections import deque

from .game import TreasureDash, _sign
from .objects import Enemy, Gem, Hazard, Position


class AdvancedTreasureDash(TreasureDash):
    display_title = "かくれんぼAIダッシュ"
    locked_enemy_behavior = True

    def __init__(self, config: dict):
        self.walls: set[Position] = {tuple(p) for p in config["wall_positions"]}
        super().__init__(config)
        self.enemy_behavior = "vision_chase"

    def reset_episode(self) -> None:
        self.walls = {tuple(p) for p in self.config["wall_positions"]}
        self.agent_position = (self.width // 2, self.height // 2)
        self.steps = 0
        self.score = 0.0
        self.last_reward = 0.0
        self.gems = [Gem(tuple(p), tuple(p)) for p in self.config["reward_positions"]]
        self.hazards = [Hazard(tuple(p)) for p in self.config["hazard_positions"]]
        self.enemies = []
        for _ in range(self.config["number_of_enemies"]):
            position = self._empty_position()
            if position is not None:
                self.enemies.append(Enemy(position))

    def state(self) -> tuple:
        visible_gems = [obj for obj in self.gems if self.agent_can_see(obj.position)]
        visible_hazards = [obj for obj in self.hazards if self.agent_can_see(obj.position)]
        visible_enemies = [obj for obj in self.enemies if self.agent_can_see(obj.position)]
        blocked = tuple(self._clamp((self.agent_position[0] + dx, self.agent_position[1] + dy)) in self.walls
                        or self._clamp((self.agent_position[0] + dx, self.agent_position[1] + dy)) == self.agent_position
                        for dx, dy in self.agent.ACTIONS)
        return (self.agent_position, blocked, self._nearest_signature(visible_gems),
                self._nearest_signature(visible_hazards), self._nearest_signature(visible_enemies))

    def tick(self) -> bool:
        old_state = self.state()
        action = self.agent.choose_action(old_state, training=self.mode == "training")
        dx, dy = self.agent.ACTIONS[action]
        old_position = self.agent_position
        candidate = self._clamp((old_position[0] + dx, old_position[1] + dy))
        if candidate in self.walls or (self.config["hazard_blocks_agent"] and candidate in {h.position for h in self.hazards}):
            candidate = old_position
        self.agent_position = candidate
        self.steps += 1

        if self.steps % self.config["enemy_speed"] == 0:
            self._move_enemies()

        reward = self.config["step_penalty"]
        collected = [gem for gem in self.gems if gem.position == self.agent_position]
        for gem in collected:
            reward += self.config["gem_reward"]
            self.gems.remove(gem)
            if gem.home_position is not None:
                self.gems.append(Gem(gem.home_position, gem.home_position))
            else:
                self.add_gem()
        if any(h.position == self.agent_position for h in self.hazards):
            reward += self.config["hazard_penalty"]
        caught = any(e.position == self.agent_position for e in self.enemies)
        if caught:
            reward += self.config["enemy_penalty"]

        self.last_reward = reward
        self.score += reward
        done = caught or self.steps >= self.config["episode_length"]
        if self.mode == "training":
            self.agent.learn(old_state, action, reward, self.state(), done)
        if done:
            self._finish_episode()
        return done

    def _move_enemies(self) -> None:
        for enemy in self.enemies:
            if self.monster_can_see(enemy, self.agent_position):
                enemy.last_seen = self.agent_position
                enemy.alerted = True
            if enemy.last_seen is not None:
                enemy.position = self._next_path_step(enemy.position, enemy.last_seen)
                if enemy.position == enemy.last_seen and not self.monster_can_see(enemy, self.agent_position):
                    enemy.last_seen = None
                    enemy.alerted = False
            else:
                enemy.position = self._random_open_neighbor(enemy.position)

    def _next_path_step(self, start: Position, goal: Position) -> Position:
        """Breadth-first search makes hunters take the shortest route around walls."""
        queue = deque([start])
        parent: dict[Position, Position | None] = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for dx, dy in self.agent.ACTIONS:
                nxt = self._clamp((current[0] + dx, current[1] + dy))
                if nxt not in parent and nxt not in self.walls:
                    parent[nxt] = current
                    queue.append(nxt)
        if goal not in parent:
            return start
        current = goal
        while parent[current] not in (None, start):
            current = parent[current]  # type: ignore[assignment]
        return current

    def _random_open_neighbor(self, position: Position) -> Position:
        candidates = []
        for dx, dy in self.agent.ACTIONS + ((0, 0),):
            candidate = self._clamp((position[0] + dx, position[1] + dy))
            if candidate not in self.walls:
                candidates.append(candidate)
        return self.rng.choice(candidates)

    def can_see(self, source: Position, target: Position, vision_range: int | None = None) -> bool:
        sight = self.config["vision_range"] if vision_range is None else vision_range
        if abs(source[0] - target[0]) + abs(source[1] - target[1]) > sight:
            return False
        return all(point not in self.walls for point in self._line_points(source, target))

    def agent_can_see(self, target: Position) -> bool:
        return self.can_see(self.agent_position, target, self.config["agent_vision_range"])

    def monster_can_see(self, enemy: Enemy, target: Position) -> bool:
        return self.can_see(enemy.position, target, self.config["monster_vision_range"])

    def visible_cells(self, source: Position) -> set[Position]:
        sight = (self.config["agent_vision_range"] if source == self.agent_position
                 else self.config["monster_vision_range"])
        return {(x, y) for y in range(self.height) for x in range(self.width)
                if self.can_see(source, (x, y), sight)}

    def _line_points(self, start: Position, end: Position) -> list[Position]:
        """Return intermediate grid cells on a Bresenham line, excluding endpoints."""
        x0, y0 = start
        x1, y1 = end
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        error, points = dx + dy, []
        while (x0, y0) != (x1, y1):
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy
            if (x0, y0) != (x1, y1):
                points.append((x0, y0))
        return points

    def _occupied(self) -> set[Position]:
        return super()._occupied() | self.walls

    def toggle_enemy_behavior(self) -> None:
        # Hunters are intentionally locked to sight-based pursuit in this version.
        return
