# NBA Roulette — Three-Season Simulation Rerun

- **Pool:** 1,346 eligible player-team-season records
- **Seasons:** 2023–24 through 2025–26
- **Policies:** Random, Greedy, Strategic, and four Upper Bonus sensitivity profiles
- **Rule set:** GDD v1.2, cumulative accolade eligibility, 120 → +35 Upper Bonus

## Full-game comparison

| Policy | Games | Two-season mean | Three-season mean | Change | Two-season bonus | Three-season bonus |
|---|---:|---:|---:|---:|---:|---:|
| Random | 10,000 | 130.5 | 130.8 | +0.3 | 0.06% | 0.05% |
| Greedy | 10,000 | 249.0 | 247.7 | -1.3 | 4.16% | 3.84% |
| Strategic | 5,000 | 325.3 | 328.2 | +2.9 | 23.34% | 23.80% |

## Upper Bonus sensitivity

| Profile | Mean total | Mean upper | 120+ | 130+ | 140+ |
|---|---:|---:|---:|---:|---:|
| Neutral | 329.7 | 109.2 | 23.55% | 7.55% | 1.60% |
| Balanced | 324.5 | 106.8 | 19.10% | 6.25% | 2.35% |
| Aggressive | 321.5 | 106.1 | 19.95% | 7.40% | 2.35% |
| Very Aggressive | 307.7 | 103.5 | 17.25% | 5.55% | 1.95% |

## Decision

1. **Keep 120 → +35.** Strategic profiles reached 120 in 17.25%–23.55% of games. This is demanding but realistically attainable.
2. **Do not return to 140.** Only 1.60%–2.35% of sensitivity games reached 140.
3. **Do not increase the bonus-chasing weight.** The Neutral profile produced both the highest mean total and the highest 120 attainment; forcing bonus pursuit caused premature upper-category placement.
4. **Keep the rest of the scoring system unchanged for the browser prototype.** Adding 2025–26 moved full-game means by only −1.3 to +2.9 points across the primary policies.
5. **Validate with Human Playtest 2.** Simulation supports the current rules, but player understanding and enjoyment remain the deciding evidence.

## Reproduce

```bash
python scripts/simulate_baselines.py
python scripts/simulate_strategic.py
python scripts/simulate_bonus_sensitivity.py
python scripts/summarize_simulation_rerun.py
```
