"""Castle quest: learn one safe route from a fixed start to a single goal."""

from __future__ import annotations

from collections import deque

from .advanced_game import AdvancedTreasureDash
from .objects import Enemy, Gem, Hazard, Position


class CastleQuest(AdvancedTreasureDash):
    display_title = "AI勇者のキャッスルクエスト"
    is_quest = True

    def __init__(self, config: dict):
        self.successes = 0
        self.defeats = 0
        self.best_steps: int | None = None
        self.last_outcome = "まだ冒険は始まっていません"
        super().__init__(config)
        self.goal_position = tuple(config["reward_positions"][0])
        self._goal_distances = self._build_goal_distances()
        self.start_distance = self._goal_distances.get(self.start_position, 1)

    @property
    def start_position(self) -> Position:
        configured = self.config.get("start_position")
        return tuple(configured) if configured is not None else (1, self.height - 2)

    def reset_episode(self) -> None:
        self.walls = {tuple(p) for p in self.config["wall_positions"]}
        self.agent_position = self.start_position
        self.steps = 0
        self.score = 0.0
        self.last_reward = 0.0
        self.gems = [Gem(tuple(self.config["reward_positions"][0]), tuple(self.config["reward_positions"][0]))]
        self.hazards = [Hazard(tuple(p)) for p in self.config["hazard_positions"]]
        configured_enemies = self.config.get("enemy_positions", [])
        self.enemies = [Enemy(tuple(p)) for p in configured_enemies]
        if not self.enemies:
            for _ in range(self.config["number_of_enemies"]):
                position = self._empty_position()
                if position is not None:
                    self.enemies.append(Enemy(position))

    def state(self) -> tuple:
        visible_hazards = [obj for obj in self.hazards if self.agent_can_see(obj.position)]
        visible_enemies = [obj for obj in self.enemies if self.agent_can_see(obj.position)]
        blocked = tuple(self._clamp((self.agent_position[0] + dx, self.agent_position[1] + dy)) in self.walls
                        or self._clamp((self.agent_position[0] + dx, self.agent_position[1] + dy)) == self.agent_position
                        for dx, dy in self.agent.ACTIONS)
        goal_dx = self.goal_position[0] - self.agent_position[0]
        goal_dy = self.goal_position[1] - self.agent_position[1]
        goal_hint = ((goal_dx > 0) - (goal_dx < 0), (goal_dy > 0) - (goal_dy < 0),
                     min(self._goal_distances.get(self.agent_position, 20), 20))
        return (self.agent_position, blocked, goal_hint, self._nearest_signature(visible_hazards),
                self._nearest_signature(visible_enemies))

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

        new_distance = self._goal_distances.get(self.agent_position, old_distance)
        reward = self.config["step_penalty"] + self.config["progress_reward"] * (old_distance - new_distance)
        if any(h.position == self.agent_position for h in self.hazards):
            reward += self.config["hazard_penalty"]
        reached_castle = self.agent_position == self.goal_position
        caught = any(e.position == self.agent_position for e in self.enemies)
        if reached_castle:
            reward += self.config["gem_reward"]
        if caught:
            reward += self.config["enemy_penalty"]

        self.last_reward = reward
        self.score += reward
        done = reached_castle or caught or self.steps >= self.config["episode_length"]
        if self.mode == "training":
            self.agent.learn(old_state, action, reward, self.state(), done)
        if done:
            if reached_castle:
                self.successes += 1
                self.best_steps = self.steps if self.best_steps is None else min(self.best_steps, self.steps)
                self.last_outcome = f"お城に到着！ {self.steps}歩"
            elif caught:
                self.defeats += 1
                self.last_outcome = "モンスターにつかまりました"
            else:
                self.last_outcome = "時間切れになりました"
            self._finish_episode()
        return done

    def journey_progress(self) -> float:
        remaining = self._goal_distances.get(self.agent_position, self.start_distance)
        return max(0.0, min(1.0, 1.0 - remaining / max(1, self.start_distance)))

    def reset_training(self) -> None:
        self.successes = 0
        self.defeats = 0
        self.best_steps = None
        self.last_outcome = "学習をリセットしました"
        super().reset_training()

    def _build_goal_distances(self) -> dict[Position, int]:
        distances = {self.goal_position: 0}
        queue = deque([self.goal_position])
        while queue:
            current = queue.popleft()
            for dx, dy in self.agent.ACTIONS:
                nxt = self._clamp((current[0] + dx, current[1] + dy))
                if nxt not in self.walls and nxt not in distances:
                    distances[nxt] = distances[current] + 1
                    queue.append(nxt)
        return distances
