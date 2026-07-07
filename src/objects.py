"""Simple game object data types."""

from dataclasses import dataclass

Position = tuple[int, int]


@dataclass
class Gem:
    position: Position
    home_position: Position | None = None


@dataclass
class Hazard:
    position: Position


@dataclass
class Enemy:
    position: Position
    last_seen: Position | None = None
    alerted: bool = False
