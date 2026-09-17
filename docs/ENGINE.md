# NBA Roulette — Core Engine

The core engine implements the rules independently of any web interface or
simulation strategy. This keeps probability, scoring, and game-state behavior
testable before bots or animations are added.

## Modules

- `nba_roulette/models.py`: immutable player-team-season records and lock names.
- `nba_roulette/data.py`: validated game JSON loader.
- `nba_roulette/roulette.py`: hierarchical roulette and lock resolution.
- `nba_roulette/scoring.py`: the 14 categories and Upper Bonus.
- `nba_roulette/game.py`: spins, rerolls, category consumption, and game totals.
- `nba_roulette/simulation.py`: reusable full-game policies and summaries.

## Roulette Resolution

A standard spin resolves with equal probability at each stage:

1. Season
2. Team within that season
3. Eligible player within that team-season

Locks constrain the valid pool. Unlocked stages still resolve in hierarchy
order with equal weighting among valid choices. Player locks use `player_id`,
not display names. This preserves the intended behavior for players with
multiple eligible seasons or team stints.

| Locks | Resolution |
|---|---|
| None | Season → Team → Player |
| Season | Team → Player |
| Team | Valid Season → Player |
| Player | Valid Season → Valid Team |
| Season + Team | Player |
| Season + Player | Valid Team |
| Team + Player | Valid Season |
| All three | Reroll disabled |

Locks are supplied again before every reroll, so the player may freely change
them. A new lock set applies to the current result.

## Scoring Defaults

- Statistical scores use round-half-up, not Python's default bankers' rounding.
- All-NBA and All-Defense categories require the exact team level.
- Major Award scores 50 once if MVP, DPOY, or ROTY is true; awards do not stack.
- Individual awards follow the player-season metadata on each eligible stint.
- Champion follows the selected team-specific record.
- The +35 Upper Bonus is derived from the five statistical categories at 140+.

## Verification

Run deterministic unit tests:

```bash
python -m unittest discover -v
```

Run the empirical production-pool probability audit:

```bash
python scripts/verify_engine.py
```

The audit uses a fixed seed and writes `analysis/engine_verification.json`.
It checks standard season/team weighting, player weighting inside a locked
team-season, traded-player hierarchical weighting, and validity under every
rerollable lock mask.

## Simulation baselines

Run the reproducible Random and Greedy full-game baselines:

```bash
python scripts/simulate_baselines.py
```

The command writes `analysis/baseline_simulation.json`,
`analysis/baseline_category_summary.csv`, and
`docs/BASELINE_SIMULATION.md`. Neither baseline uses locks; this cleanly
separates calibration from the later strategic lock-aware policy.

Run the lock-aware heuristic comparison:

```bash
python scripts/simulate_strategic.py
```

The Strategic policy evaluates all seven rerollable lock masks using exact
hierarchical outcome probabilities. Its category heuristic uses replacement
value and limited Upper Bonus equity. It is a transparent benchmark for
sensitivity testing, not an optimal-play solver.
