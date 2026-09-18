# NBA Roulette

NBA Roulette is a Yahtzee-inspired NBA strategy game built around historical
player-team-season statistics, accolades, games played, and jersey numbers.

## Current status

The 2023–24, 2024–25, and 2025–26 datasets are complete:

- 1,346 eligible player-team records across the three seasons and all 30 NBA teams;
- eligibility of at least 15 games and 10.0 minutes per game for that team;
- team-specific statistics for traded players;
- final jersey number for each team stint;
- All-NBA, All-Defensive, champion, MVP, DPOY, and ROTY fields;
- 121 historical jersey records verified against official NBA last-game box scores.

## Repository structure

```text
data/
├── game/          # Lightweight JSON consumed by the game
└── processed/     # Auditable CSV and validation summaries
nba_roulette/      # Core roulette, scoring, and game-state engine
docs/              # Data architecture and methodology
scripts/           # Reproducible collection and verification scripts
tests/              # Deterministic engine and probability tests
```

See [`docs/DATA_README.md`](docs/DATA_README.md) for the schema, source notes,
eligibility rules, jersey-number policy, and rebuild instructions.

See [`docs/DISTRIBUTION_REPORT.md`](docs/DISTRIBUTION_REPORT.md) for the
roulette-weighted three-season scoring, Joker, and accolade distributions.

See [`docs/ENGINE.md`](docs/ENGINE.md) for roulette resolution, lock semantics,
scoring defaults, and engine verification.

See [`docs/BASELINE_SIMULATION.md`](docs/BASELINE_SIMULATION.md) for the
Random and Greedy full-game simulation baselines.

See [`docs/STRATEGIC_SIMULATION.md`](docs/STRATEGIC_SIMULATION.md) for the
lock-aware heuristic comparison.

See [`docs/THREE_SEASON_SIMULATION_RERUN.md`](docs/THREE_SEASON_SIMULATION_RERUN.md)
for the consolidated two-season versus three-season simulation results and
the resulting decision to retain the 120 → +35 Upper Bonus.

See [`docs/GDD_V1_1_CHANGELOG.md`](docs/GDD_V1_1_CHANGELOG.md) for the evidence-
based change from the original 140-point bonus threshold to the 120-point
prototype rule.

See [`docs/GDD_V1_2_CHANGELOG.md`](docs/GDD_V1_2_CHANGELOG.md) and
[`docs/HUMAN_PLAYTEST_01.md`](docs/HUMAN_PLAYTEST_01.md) for the cumulative
accolade rule and terminology changes made after the first human playtest.

See [`docs/GDD_V1_3_CHANGELOG.md`](docs/GDD_V1_3_CHANGELOG.md) for the
playtest-driven reroll difference rule, repeat-rate audit, and rationale for
not yet adding a game-wide player ban.

See [`docs/GDD_V1_4_CHANGELOG.md`](docs/GDD_V1_4_CHANGELOG.md) for the stronger
unlocked-slot reroll rule, clarified used-category state, and clean transition
from the interrupted v0.3 batch to v0.4 validation.

## Rebuild a dataset

```bash
python scripts/build_dataset.py --season 2023-24
python scripts/build_dataset.py --season 2024-25
python scripts/build_boxscore_dataset.py --season 2025-26 \
  --boxscores data/raw/2025-26/player_boxscores_2026.csv
```

## Rebuild the distribution report

```bash
python scripts/analyze_distributions.py
```

## Verify the game engine

```bash
python -m unittest discover -v
python scripts/verify_engine.py
```

## Run the baseline simulations

```bash
python scripts/simulate_baselines.py
python scripts/simulate_strategic.py
python scripts/simulate_bonus_sensitivity.py
python scripts/summarize_simulation_rerun.py
```

## Play one terminal game

```bash
python scripts/play_game.py
```

## Run the browser prototype

```bash
python scripts/run_web.py
```

Then open `http://127.0.0.1:8000`. The prototype uses only the Python standard
library and the existing game engine; no additional packages are required.
See [`docs/WEB_PROTOTYPE.md`](docs/WEB_PROTOTYPE.md) for the included features,
architecture, v0.2 playtest-driven interface changes, and deliberate limitations.
Prototype v0.4 guarantees that every unlocked slot changes whenever a valid
combined outcome permits it, and gives used scorecard categories an unmistakable
filled and checked state.

Completed local games are automatically captured for **Playtest Batch 3 — v0.4
Unlocked-Slot Validation** in `playtest_logs/` as detailed JSONL plus a CSV summary. The
folder is intentionally excluded from Git.

## Game design snapshot

Each turn produces a valid `Season → Team → Player` combination. Before a
reroll, players explicitly choose which slots to **keep**; all other slots are
rerolled. The final player-team-season is assigned to an unused scorecard
category. The initial game design uses 14 categories and up to three spins per
turn.
