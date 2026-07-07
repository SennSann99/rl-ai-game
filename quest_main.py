"""Entry point for the fixed-start castle quest."""

from pathlib import Path
import sys

import pygame

from src.config import load_config
from src.quest_game import CastleQuest
from src.quest_ui import QuestUI


def main() -> int:
    config = load_config(Path(__file__).with_name("config_quest.json"))
    pygame.init()
    try:
        game = CastleQuest(config)
        ui = QuestUI(config)
        clock = pygame.time.Clock()
        running, paused = True, True
        simulation_speed = float(config["agent_speed"])
        step_budget = 0.0
        while running:
            elapsed = clock.tick(config["fps"]) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_r:
                        game.reset_training(); paused = True; step_budget = 0.0
                    elif event.key == pygame.K_m:
                        game.toggle_mode(); paused = True; step_budget = 0.0
                    elif event.key == pygame.K_LEFTBRACKET:
                        simulation_speed = max(1.0, simulation_speed - 1.0)
                    elif event.key == pygame.K_RIGHTBRACKET:
                        simulation_speed = min(60.0, simulation_speed + 1.0)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = ui.action_at(event.pos)
                    if action == "pause": paused = not paused
                    elif action == "reset": game.reset_training(); paused = True; step_budget = 0.0
                    elif action == "mode": game.toggle_mode(); paused = True; step_budget = 0.0
                    elif action == "speed_down": simulation_speed = max(1.0, simulation_speed - 1.0)
                    elif action == "speed_up": simulation_speed = min(60.0, simulation_speed + 1.0)
                    elif action == "enemy_slower": game.config["enemy_speed"] = min(30, game.config["enemy_speed"] + 1)
                    elif action == "enemy_faster": game.config["enemy_speed"] = max(1, game.config["enemy_speed"] - 1)

            if not paused:
                step_budget += elapsed * simulation_speed
                if game.episode >= config["training_episodes"] and game.mode == "training":
                    game.toggle_mode(); paused = True; step_budget = 0.0
                updates = min(int(step_budget), 10)
                step_budget -= updates
                for _ in range(updates):
                    game.tick()
            ui.draw(game, paused, simulation_speed)
        return 0
    finally:
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
