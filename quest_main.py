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
                        if not game.training_started:
                            game.begin_training()
                            paused = False
                        else:
                            paused = not paused
                    elif event.key == pygame.K_r:
                        game.return_to_setup(); paused = True; step_budget = 0.0
                    elif event.key == pygame.K_m:
                        game.toggle_access_mode()
                    elif event.key == pygame.K_LEFTBRACKET:
                        simulation_speed = max(1.0, simulation_speed - 1.0)
                    elif event.key == pygame.K_RIGHTBRACKET:
                        simulation_speed = min(60.0, simulation_speed + 1.0)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = ui.action_at(event.pos)
                    canvas_pos = ui.canvas_position(event.pos)
                    if action == "pause":
                        if not game.training_started:
                            game.begin_training()
                            paused = False
                        else:
                            paused = not paused
                    elif action == "reset":
                        game.return_to_setup(); paused = True; step_budget = 0.0
                    elif action == "role":
                        game.toggle_access_mode()
                    elif action == "toggle_enemies":
                        game.toggle_enemies()
                    elif action == "collect_coins":
                        game.collect_coins()
                    elif action == "revive_coins":
                        game.revive_coins()
                    elif action in {"speed_down", "speed_up"}:
                        if action == "speed_down": simulation_speed = max(1.0, simulation_speed - 1.0)
                        else: simulation_speed = min(60.0, simulation_speed + 1.0)
                    elif action and game.access_mode == "configurer" and not game.training_started:
                        if action == "enemy_slower": game.config["enemy_speed"] = min(30, game.config["enemy_speed"] + 1)
                        elif action == "enemy_faster": game.config["enemy_speed"] = max(1, game.config["enemy_speed"] - 1)
                        elif action == "hero_vision_down": game.config["agent_vision_range"] = max(1, game.config["agent_vision_range"] - 1)
                        elif action == "hero_vision_up": game.config["agent_vision_range"] = min(10, game.config["agent_vision_range"] + 1)
                        elif action == "monster_vision_down": game.config["monster_vision_range"] = max(1, game.config["monster_vision_range"] - 1)
                        elif action == "monster_vision_up": game.config["monster_vision_range"] = min(10, game.config["monster_vision_range"] + 1)
                        elif action == "castle_reward_down": game.config["gem_reward"] = max(0, game.config["gem_reward"] - 5)
                        elif action == "castle_reward_up": game.config["gem_reward"] += 5
                        elif action == "coin_reward_down": game.config["coin_reward"] = max(0, game.config["coin_reward"] - 1)
                        elif action == "coin_reward_up": game.config["coin_reward"] += 1
                        elif action == "coin_respawn_down": game.config["coin_respawn_steps"] = max(1, game.config["coin_respawn_steps"] - 1)
                        elif action == "coin_respawn_up": game.config["coin_respawn_steps"] += 1
                        elif action == "hazard_penalty_down": game.config["hazard_penalty"] -= 1
                        elif action == "hazard_penalty_up": game.config["hazard_penalty"] = min(0, game.config["hazard_penalty"] + 1)
                        elif action == "enemy_penalty_down": game.config["enemy_penalty"] -= 5
                        elif action == "enemy_penalty_up": game.config["enemy_penalty"] = min(0, game.config["enemy_penalty"] + 5)
                    elif action is None and canvas_pos is not None and canvas_pos[0] < ui.arena_width and canvas_pos[1] < ui.arena_height:
                        game.place_or_remove_coin((canvas_pos[0] // ui.cell, canvas_pos[1] // ui.cell))

            if not paused:
                step_budget += elapsed * simulation_speed
                if game.episode >= game.TRAINING_EPISODES and game.mode == "training":
                    game.mode = "demo"
                    game.reset_episode()
                    paused = True
                    step_budget = 0.0
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
