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
roulette-weighted two-season scoring, Joker, and accolade distributions.

See [`docs/ENGINE.md`](docs/ENGINE.md) for roulette resolution, lock semantics,
scoring defaults, and engine verification.

See [`docs/BASELINE_SIMULATION.md`](docs/BASELINE_SIMULATION.md) for the
Random and Greedy full-game simulation baselines.

See [`docs/STRATEGIC_SIMULATION.md`](docs/STRATEGIC_SIMULATION.md) for the
lock-aware heuristic comparison.

See [`docs/GDD_V1_1_CHANGELOG.md`](docs/GDD_V1_1_CHANGELOG.md) for the evidence-
based change from the original 140-point bonus threshold to the 120-point
prototype rule.

See [`docs/GDD_V1_2_CHANGELOG.md`](docs/GDD_V1_2_CHANGELOG.md) and
[`docs/HUMAN_PLAYTEST_01.md`](docs/HUMAN_PLAYTEST_01.md) for the cumulative
accolade rule and terminology changes made after the first human playtest.

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
```

## Play one terminal game

```bash
python scripts/play_game.py
```

## Game design snapshot

Each turn produces a valid `Season → Team → Player` combination. Before a
reroll, players explicitly choose which slots to **keep**; all other slots are
rerolled. The final player-team-season is assigned to an unused scorecard
category. The initial game design uses 14 categories and up to three spins per
turn.
