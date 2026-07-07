# AI Treasure Dash

A lightweight event demo where a blue AI agent learns to collect gold gems and avoid red hazards and purple enemies. It uses tabular Q-learning: good outcomes increase the value of the action that led to them, while penalties reduce it. No GPU, network service, or machine-learning framework is required.

## Install and run

Requires Python 3.10 or newer. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The game opens paused; click **START** when the audience is ready. The agent initially explores randomly (high epsilon), then increasingly chooses actions that earned higher rewards. After `training_episodes`, the game switches to demo mode and pauses so the presenter stays in control.

## Controls

| Key | Action |
| --- | --- |
| `G` | Add a gem |
| `H` | Add a hazard |
| `C` | Toggle enemies between random movement and chasing |
| `M` | Switch between training and demo mode |
| `R` | Clear the Q-table and restart training |
| `Space` | Pause/resume |
| `[` / `]` | Decrease/increase simulation speed |
| `Esc` | Quit |

## Configure the environment

Edit `config.json` before starting the game. It controls the grid and cell size; fixed object positions; rewards and penalties; update speeds; moving or blocking hazards; enemy behavior; episode/training length; Q-learning values; and colors. Invalid or missing values produce a warning and use safe defaults.

Useful presentation changes:

- Set `reward_positions` and `hazard_positions` to grid coordinates such as `[2, 1]`. These placements remain fixed across episodes, and collected gems return to their configured cells.
- Set `hazards_moving` to `true` for a harder environment.
- Set `hazard_blocks_agent` to `true` to turn red cells into walls instead of traversable penalty zones.
- Set `enemy_behavior` to `"chase"` for pursuing enemies.
- Change `agent_speed` to set the initial number of learning steps per second. It can also be adjusted live with the panel controls.
- Lower `episode_length` or `training_episodes` for a shorter demo.

`enemy_speed` is the number of agent steps between enemy/hazard moves, so a smaller value makes them move faster.

The on-screen panel also provides clickable controls for start/pause, reset, training/demo mode, simulation speed, gem and hazard counts, enemy speed, and enemy behavior.

The learning-progress chart shows raw episode scores in gray and a five-episode moving average in gold. A rising gold line indicates that the policy is improving.

## Reinforcement learning in plain language

The AI is not given a route. It sees its position and the direction and distance to the nearest gem, hazard, and enemy. It tries actions, receives points or penalties, and stores which actions worked in a Q-table. Epsilon is the chance that it explores a random action; that chance falls as training progresses. Demo mode sets exploration aside and shows the best policy learned so far.

## Limitations

The Q-table is kept in memory and is not saved between runs. Because objects can move and respawn, scores naturally vary, and a changed configuration should be followed by resetting training. This prototype favors visible, fast learning over sophisticated planning.

## Advanced limited-vision version

Run `python advanced_main.py` to start the separate advanced version configured by `config_advanced.json`. Both the AI and monsters see up to three grid cells away, walls block movement and line of sight, and alerted monsters use shortest-path search to pursue the AI's last known position. Blue and purple shading visualizes each side's field of view; an outlined monster with `!` has detected the AI.

## Castle quest version

Run `python quest_main.py` for a separate fixed-start journey configured by `config_quest.json`. The AI hero must cross a maze of dangerous road cells and sight-based monsters to reach one castle. Reaching the castle or being caught ends the episode. The final castle reward is supplemented by a small configurable `progress_reward` so the sparse-reward task can learn during a live demonstration.

The quest dashboard uses the lower-left area to show the remaining route distance, currently visible threats, and reward rules.
