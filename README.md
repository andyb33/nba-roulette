# NBA Roulette

NBA Roulette is a Yahtzee-inspired NBA strategy game built around historical
player-team-season statistics, accolades, games played, and jersey numbers.

## Current status

The 2023–24 data pilot is complete:

- 441 eligible player-team records across all 30 NBA teams;
- eligibility of at least 15 games and 10.0 minutes per game for that team;
- team-specific statistics for traded players;
- final jersey number for each team stint;
- All-NBA, All-Defensive, champion, MVP, DPOY, and ROTY fields;
- 60 historical jersey overrides verified against official NBA last-game box scores.

## Repository structure

```text
data/
├── game/          # Lightweight JSON consumed by the game
└── processed/     # Auditable CSV and validation summaries
docs/              # Data architecture and methodology
scripts/           # Reproducible collection and verification scripts
```

See [`docs/DATA_README.md`](docs/DATA_README.md) for the schema, source notes,
eligibility rules, jersey-number policy, and rebuild instructions.

## Rebuild the 2023–24 dataset

```bash
python scripts/build_2023_24_dataset.py
python scripts/verify_historical_jerseys.py
```

## Game design snapshot

Each turn produces a valid `Season → Team → Player` combination. Players may
lock and reroll those slots before assigning the final player-team-season to an
unused scorecard category. The initial game design uses 14 categories and up to
three spins per turn.
