"""Grid environment and reinforcement-learning loop state."""

from __future__ import annotations

import random

from .agent import QLearningAgent
from .objects import Enemy, Gem, Hazard, Position


class TreasureDash:
    def __init__(self, config: dict):
        self.config = config
        self.rng = random.Random(config["seed"])
        self.agent = QLearningAgent(config, self.rng)
        self.mode = "training"
        self.enemy_behavior = config["enemy_behavior"]
        self.episode = 0
        self.best_score = float("-inf")
        self.recent_scores: list[float] = []
        self.score_history: list[float] = []
        self.gems: list[Gem] = []
        self.hazards: list[Hazard] = []
        self.enemies: list[Enemy] = []
        self.reset_episode()

    @property
    def width(self) -> int:
        return self.config["grid_width"]

    @property
    def height(self) -> int:
        return self.config["grid_height"]

    def reset_episode(self) -> None:
        self.agent_position = (self.width // 2, self.height // 2)
        self.steps = 0
        self.score = 0.0
        self.last_reward = 0.0
        self.gems, self.hazards, self.enemies = [], [], []
        for position in self.config["reward_positions"]:
            point = tuple(position)
            self.gems.append(Gem(point, point))
        for position in self.config["hazard_positions"]:
            self.hazards.append(Hazard(tuple(position)))
        for _ in range(self.config["number_of_enemies"]):
            position = self._empty_position()
            if position is not None:
                self.enemies.append(Enemy(position))

    def state(self) -> tuple:
        """Compact observations: position plus direction/distance to nearest objects."""
        return (self.agent_position, self._nearest_signature(self.gems),
                self._nearest_signature(self.hazards), self._nearest_signature(self.enemies))

    def tick(self) -> bool:
        """Run one action and one Q-learning update. Returns True at episode end."""
        old_state = self.state()
        action = self.agent.choose_action(old_state, training=self.mode == "training")
        dx, dy = self.agent.ACTIONS[action]
        old_position = self.agent_position
        candidate = self._clamp((old_position[0] + dx, old_position[1] + dy))
        if self.config["hazard_blocks_agent"] and candidate in {h.position for h in self.hazards}:
            candidate = old_position
        self.agent_position = candidate

        self.steps += 1
        if self.config["hazards_moving"] and self.steps % self.config["enemy_speed"] == 0:
            self._move_hazards()
        if self.steps % self.config["enemy_speed"] == 0:
            self._move_enemies()

        reward = self.config["step_penalty"]
        collected = [g for g in self.gems if g.position == self.agent_position]
        if collected:
            reward += self.config["gem_reward"] * len(collected)
            for gem in collected:
                self.gems.remove(gem)
                # Fixed gems return to their configured home cell when collected.
                if gem.home_position is not None:
                    self.gems.append(Gem(gem.home_position, gem.home_position))
                else:
                    self.add_gem()
        if any(h.position == self.agent_position for h in self.hazards):
            reward += self.config["hazard_penalty"]
        if any(e.position == self.agent_position for e in self.enemies):
            reward += self.config["enemy_penalty"]

        self.last_reward = reward
        self.score += reward
        done = self.steps >= self.config["episode_length"]
        if self.mode == "training":
            self.agent.learn(old_state, action, reward, self.state(), done)
        if done:
            self._finish_episode()
        return done

    def _finish_episode(self) -> None:
        self.episode += 1
        self.best_score = max(self.best_score, self.score)
        self.recent_scores = (self.recent_scores + [self.score])[-20:]
        self.score_history = (self.score_history + [self.score])[-100:]
        if self.mode == "training":
            self.agent.end_episode()
        self.reset_episode()

    def add_gem(self) -> None:
        position = self._empty_position()
        if position is not None:
            self.gems.append(Gem(position))

    def remove_gem(self) -> None:
        if self.gems:
            self.gems.pop()

    def add_hazard(self) -> None:
        position = self._empty_position()
        if position is not None:
            self.hazards.append(Hazard(position))

    def remove_hazard(self) -> None:
        if self.hazards:
            self.hazards.pop()

    def toggle_mode(self) -> None:
        self.mode = "demo" if self.mode == "training" else "training"
        self.reset_episode()

    def toggle_enemy_behavior(self) -> None:
        self.enemy_behavior = "chase" if self.enemy_behavior == "random" else "random"

    def reset_training(self) -> None:
        self.agent.reset()
        self.episode = 0
        self.best_score = float("-inf")
        self.recent_scores.clear()
        self.score_history.clear()
        self.mode = "training"
        self.reset_episode()

    def _nearest_signature(self, objects: list) -> tuple[int, int, int]:
        if not objects:
            return (0, 0, 0)
        ax, ay = self.agent_position
        target = min(objects, key=lambda obj: abs(obj.position[0] - ax) + abs(obj.position[1] - ay)).position
        dx, dy = target[0] - ax, target[1] - ay
        return (_sign(dx), _sign(dy), min(abs(dx) + abs(dy), 4))

    def _move_hazards(self) -> None:
        for hazard in self.hazards:
            hazard.position = self._random_neighbor(hazard.position)

    def _move_enemies(self) -> None:
        for enemy in self.enemies:
            if self.enemy_behavior == "chase":
                enemy.position = self._chase_neighbor(enemy.position)
            else:
                enemy.position = self._random_neighbor(enemy.position)

    def _chase_neighbor(self, position: Position) -> Position:
        candidates = [self._clamp((position[0] + dx, position[1] + dy)) for dx, dy in self.agent.ACTIONS]
        self.rng.shuffle(candidates)
        return min(candidates, key=lambda p: abs(p[0] - self.agent_position[0]) + abs(p[1] - self.agent_position[1]))

    def _random_neighbor(self, position: Position) -> Position:
        dx, dy = self.rng.choice(self.agent.ACTIONS + ((0, 0),))
        return self._clamp((position[0] + dx, position[1] + dy))

    def _clamp(self, position: Position) -> Position:
        return (max(0, min(self.width - 1, position[0])), max(0, min(self.height - 1, position[1])))

    def _occupied(self) -> set[Position]:
        return ({self.agent_position} | {g.position for g in self.gems} |
                {h.position for h in self.hazards} | {e.position for e in self.enemies})

    def _empty_position(self) -> Position | None:
        available = [(x, y) for y in range(self.height) for x in range(self.width)
                     if (x, y) not in self._occupied()]
        return self.rng.choice(available) if available else None


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)
