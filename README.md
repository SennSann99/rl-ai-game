# AI Treasure Dash

A lightweight event demo where a blue AI agent learns to collect gold gems and avoid red hazards and purple enemies. It uses tabular Q-learning: good outcomes increase the value of the action that led to them, while penalties reduce it. No GPU, network service, or machine-learning framework is required.

## Install and run

Requires Python 3.10 or newer. From this directory:

```bash
cd /Users/tomford/dev/rl-ai-game
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python quest_main.py
```

If `.venv` does not exist yet, create it after changing into the project directory:

```bash
python3 -m venv .venv
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

Run `python quest_main.py` for a separate fixed-start journey configured by `config_quest.json`. The AI hero starts from the same cell every episode and must reach one castle while avoiding walls, dangerous road cells, and sight-based monsters. Reaching the castle, being caught, or using all permitted steps ends the episode.

### Fixed learning rules

The quest fixes its training run to **100 episodes**. Every training and playback episode has a fixed **100-step** limit. This limit is enforced by the game even if `episode_length` or `training_episodes` are edited in the JSON file.

### Coins: fixed intermediate rewards

`config_quest.json` defines up to seven fixed `coin_positions`. Coins respawn at their configured locations at the start of every episode. During setup, **設定者モード** provides **コイン回収** to temporarily remove the configured set and **コイン復活** to restore it. Coin locations cannot be added, removed, or moved after learning starts.

Coins provide a small positive reward once per episode, while the castle remains the only final objective and provides the largest reward. Coins are intentionally excluded from the agent's observation state: the agent cannot see or directly target them, and must discover useful routes through its normal epsilon-greedy exploration and learned policy.

### Monster A / Monster B ranges

`monster_regions` defines a fixed `[x, y, width, height]` movement range for each monster in `enemy_positions`. Monster A uses the first region and Monster B the second. They may patrol and chase within their own range but never leave it.

### Two access modes

| Mode | Visibility and controls |
| --- | --- |
| 設定者モード | Full map is visible before and during training. Before learning starts, the user can collect/revive the fixed coins and adjust movement, vision, and reward rules. |
| 体験者モード | Only the hero's explored map is visible. Coins, map layout, and reward rules are fixed; the display speed remains adjustable. |

Use the top-left mode button before training starts to switch modes. `Space` or **学習を開始** begins the fixed 100-episode run. After learning begins, all coin and environment settings lock.

### Quest-specific settings

`config_quest.json` defines the fixed map, start, castle, hazards, coin positions, monster spawn cells and ranges, rewards, and initial view distances. The adjustable reward rules are `gem_reward`, `coin_reward`, `hazard_penalty`, and `enemy_penalty`.

The dashboard uses the lower-left area for the remaining route distance, visible threats, and reward rules.
