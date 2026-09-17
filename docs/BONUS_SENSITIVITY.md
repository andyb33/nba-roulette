# NBA Roulette — Upper Bonus Sensitivity

This experiment varies only the heuristic value assigned to progress in each
upper category. Roulette rules, locks, score values, seeds, and dataset remain
unchanged. Bonus equity is a decision weight, not points added to the game score.

Each profile played **2,000 complete games** against
1346 records using common starting seed `20260919`.

| Profile | Equity/category | Mean total | Median | Mean upper | Upper P90 | Bonus rate |
|---|---:|---:|---:|---:|---:|---:|
| Neutral | 0 | 329.7 | 327 | 109.2 | 128 | 23.55% |
| Balanced | 7 | 324.5 | 320 | 106.8 | 125 | 19.10% |
| Aggressive | 14 | 321.5 | 318 | 106.1 | 126 | 19.95% |
| Very Aggressive | 28 | 307.7 | 305 | 103.5 | 124 | 17.25% |

## Threshold attainment

| Profile | 120+ | 130+ | 135+ | 140+ | 145+ | 150+ |
|---|---:|---:|---:|---:|---:|---:|
| Neutral | 23.55% | 7.55% | 3.25% | 1.60% | 0.75% | 0.30% |
| Balanced | 19.10% | 6.25% | 3.90% | 2.35% | 1.15% | 0.60% |
| Aggressive | 19.95% | 7.40% | 4.75% | 2.35% | 1.35% | 0.90% |
| Very Aggressive | 17.25% | 5.55% | 3.15% | 1.95% | 1.00% | 0.50% |

## Effect of adding 2025–26

| Profile | Two-season mean | Three-season mean | Change | Two-season bonus | Three-season bonus |
|---|---:|---:|---:|---:|---:|
| Neutral | 327.4 | 329.7 | +2.3 | 24.25% | 23.55% |
| Balanced | 321.1 | 324.5 | +3.4 | 18.15% | 19.10% |
| Aggressive | 318.6 | 321.5 | +2.9 | 19.20% | 19.95% |
| Very Aggressive | 306.8 | 307.7 | +0.9 | 16.20% | 17.25% |

## Interpretation

- The strongest tested 120-point attainment came from **Neutral** at **23.55%**.
- Across profiles, 120-point attainment ranged from **17.25% to 23.55%**.
- Keep or change **120 → +35** only after comparing these three-season results
  with the saved two-season baseline and the strategic-policy score trade-off.
- Keep 130 as a harder alternative for later testing; restore 140 only if real
  players substantially outperform the simulation.
- These simulations guide the prototype setting; human playtesting remains the
  final check because people do not optimize like a deterministic heuristic.
