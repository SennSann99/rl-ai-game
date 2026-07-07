"""Readable tabular Q-learning agent."""

from __future__ import annotations

from collections import defaultdict
import random
from typing import Hashable

import numpy as np


class QLearningAgent:
    ACTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))

    def __init__(self, config: dict, rng: random.Random):
        self.alpha = config["learning_rate"]
        self.gamma = config["discount_factor"]
        self.epsilon_start = config["epsilon_start"]
        self.epsilon_min = config["epsilon_min"]
        self.epsilon_decay = config["epsilon_decay"]
        self.rng = rng
        self.q_table: defaultdict[Hashable, np.ndarray] = defaultdict(lambda: np.zeros(4, dtype=float))
        self.epsilon = self.epsilon_start

    def choose_action(self, state: Hashable, training: bool = True) -> int:
        if training and self.rng.random() < self.epsilon:
            return self.rng.randrange(4)
        values = self.q_table[state]
        best = np.flatnonzero(values == values.max())
        return int(self.rng.choice(best.tolist()))

    def learn(self, state: Hashable, action: int, reward: float, next_state: Hashable, done: bool) -> None:
        # Q-learning moves the old estimate toward reward + best future value.
        future = 0.0 if done else float(np.max(self.q_table[next_state]))
        target = reward + self.gamma * future
        self.q_table[state][action] += self.alpha * (target - self.q_table[state][action])

    def end_episode(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def reset(self) -> None:
        self.q_table.clear()
        self.epsilon = self.epsilon_start
