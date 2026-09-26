"""Configuration loading with validation and safe defaults."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


DEFAULTS: dict[str, Any] = {
    "grid_width": 10,
    "grid_height": 8,
    "cell_size": 64,
    "number_of_rewards": 3,
    "number_of_hazards": 4,
    "number_of_enemies": 1,
    "vision_range": 3,
    "agent_vision_range": 3,
    "monster_vision_range": 3,
    "wall_positions": [],
    "enemy_positions": [],
    "coin_positions": [],
    "monster_regions": [],
    "start_position": None,
    "reward_positions": [[2, 1], [8, 0], [9, 5]],
    "hazard_positions": [[1, 0], [2, 4], [8, 5], [9, 4]],
    "gem_reward": 10.0,
    "coin_reward": 6.0,
    "coin_respawn_steps": 4,
    "hazard_penalty": -12.0,
    "enemy_penalty": -15.0,
    "step_penalty": -0.05,
    "progress_reward": 0.0,
    "agent_speed": 8,
    "enemy_speed": 3,
    "hazards_moving": False,
    "hazard_blocks_agent": False,
    "enemy_behavior": "random",
    "episode_length": 150,
    "training_episodes": 500,
    "learning_rate": 0.2,
    "discount_factor": 0.95,
    "epsilon_start": 1.0,
    "epsilon_min": 0.05,
    "epsilon_decay": 0.992,
    "fps": 60,
    "seed": 7,
    "theme": {
        "background": [22, 28, 40],
        "grid": [48, 58, 76],
        "agent": [65, 180, 255],
        "reward": [255, 215, 64],
        "hazard": [235, 70, 70],
        "enemy": [170, 80, 230],
        "text": [235, 240, 248],
        "panel": [30, 38, 54],
    },
}

_POSITIVE_INTS = {
    "coin_respawn_steps",
    "grid_width", "grid_height", "cell_size", "agent_speed", "enemy_speed",
    "episode_length", "training_episodes", "fps", "vision_range",
    "agent_vision_range", "monster_vision_range",
}
_NONNEGATIVE_INTS = {"number_of_rewards", "number_of_hazards", "number_of_enemies", "seed"}
_NUMBERS = {
    "gem_reward", "coin_reward", "hazard_penalty", "enemy_penalty", "step_penalty",
    "learning_rate", "discount_factor", "epsilon_start", "epsilon_min", "epsilon_decay",
    "progress_reward",
}


def load_config(path: str | Path) -> dict[str, Any]:
    """Load JSON config, replacing invalid or missing fields with defaults."""
    config = copy.deepcopy(DEFAULTS)
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("top level must be an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Config warning: {exc}; using defaults.")
        return config

    for key, value in raw.items():
        if key == "theme" and isinstance(value, dict):
            for color, rgb in value.items():
                if color in config["theme"] and _valid_color(rgb):
                    config["theme"][color] = rgb
                else:
                    print(f"Config warning: ignoring invalid theme.{color}")
        elif key in _POSITIVE_INTS and isinstance(value, int) and value > 0:
            config[key] = value
        elif key in _NONNEGATIVE_INTS and isinstance(value, int) and value >= 0:
            config[key] = value
        elif key in _NUMBERS and isinstance(value, (int, float)):
            config[key] = float(value)
        elif key in {"hazards_moving", "hazard_blocks_agent"} and isinstance(value, bool):
            config[key] = value
        elif key in {"reward_positions", "hazard_positions", "wall_positions", "enemy_positions", "coin_positions"} and isinstance(value, list):
            valid = []
            for position in value:
                if (isinstance(position, list) and len(position) == 2 and
                        all(isinstance(v, int) for v in position)):
                    valid.append(position)
                else:
                    print(f"Config warning: ignoring invalid position in '{key}'")
            config[key] = valid
        elif key == "monster_regions" and isinstance(value, list):
            regions = []
            for region in value:
                if (isinstance(region, list) and len(region) == 4 and all(isinstance(v, int) for v in region)
                        and region[2] > 0 and region[3] > 0):
                    regions.append(region)
                else:
                    print("Config warning: ignoring invalid monster region")
            config[key] = regions
        elif key == "start_position" and (value is None or
                (isinstance(value, list) and len(value) == 2 and all(isinstance(v, int) for v in value))):
            config[key] = value
        elif key == "enemy_behavior" and value in {"random", "chase"}:
            config[key] = value
        elif key not in DEFAULTS:
            print(f"Config warning: unknown setting '{key}' ignored")
        else:
            print(f"Config warning: invalid '{key}', using default")

    config["learning_rate"] = min(1.0, max(0.0, config["learning_rate"]))
    config["discount_factor"] = min(1.0, max(0.0, config["discount_factor"]))
    config["epsilon_start"] = min(1.0, max(0.0, config["epsilon_start"]))
    config["epsilon_min"] = min(config["epsilon_start"], max(0.0, config["epsilon_min"]))
    config["epsilon_decay"] = min(1.0, max(0.0, config["epsilon_decay"]))
    if config["start_position"] is not None:
        sx, sy = config["start_position"]
        if not (0 <= sx < config["grid_width"] and 0 <= sy < config["grid_height"]):
            print("Config warning: start_position is outside the grid; using grid center")
            config["start_position"] = None
    reserved_start = (tuple(config["start_position"]) if config["start_position"] is not None
                      else (config["grid_width"] // 2, config["grid_height"] // 2))
    occupied: set[tuple[int, int]] = set()
    for key in ("wall_positions", "reward_positions", "hazard_positions", "enemy_positions", "coin_positions"):
        checked = []
        for position in config[key]:
            point = (position[0], position[1])
            in_grid = 0 <= point[0] < config["grid_width"] and 0 <= point[1] < config["grid_height"]
            is_start = point == reserved_start
            if in_grid and not is_start and point not in occupied:
                checked.append(position)
                occupied.add(point)
            else:
                print(f"Config warning: ignoring unavailable {key} position {position}")
        config[key] = checked
    config["number_of_rewards"] = len(config["reward_positions"])
    config["number_of_hazards"] = len(config["hazard_positions"])
    if config["enemy_positions"]:
        config["number_of_enemies"] = len(config["enemy_positions"])
    if len(config["coin_positions"]) > 7:
        print("Config warning: only the first 7 coin positions are used")
        config["coin_positions"] = config["coin_positions"][:7]
    valid_regions = []
    for x, y, width, height in config["monster_regions"]:
        if x >= 0 and y >= 0 and x + width <= config["grid_width"] and y + height <= config["grid_height"]:
            valid_regions.append([x, y, width, height])
        else:
            print(f"Config warning: ignoring out-of-grid monster region {[x, y, width, height]}")
    config["monster_regions"] = valid_regions
    capacity = config["grid_width"] * config["grid_height"] - 1
    requested = config["number_of_rewards"] + config["number_of_hazards"] + config["number_of_enemies"]
    if requested > capacity:
        print("Config warning: too many objects for grid; reducing counts.")
        for key in ("number_of_enemies", "number_of_hazards", "number_of_rewards"):
            overflow = max(0, requested - capacity)
            removed = min(config[key], overflow)
            config[key] -= removed
            requested -= removed
    return config


def _valid_color(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(isinstance(v, int) and 0 <= v <= 255 for v in value)
