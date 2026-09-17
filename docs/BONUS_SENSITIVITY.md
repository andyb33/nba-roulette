# NBA Roulette — Upper Bonus Sensitivity

This experiment varies only the heuristic value assigned to progress in each
upper category. Roulette rules, locks, score values, seeds, and dataset remain
unchanged. Bonus equity is a decision weight, not points added to the game score.

Each profile played **2,000 complete games** against
895 records using common starting seed `20260919`.

| Profile | Equity/category | Mean total | Median | Mean upper | Upper P90 | Bonus rate |
|---|---:|---:|---:|---:|---:|---:|
| Neutral | 0 | 327.4 | 324 | 110.3 | 128 | 24.25% |
| Balanced | 7 | 321.1 | 318 | 106.4 | 125 | 18.15% |
| Aggressive | 14 | 318.6 | 315 | 106.1 | 127 | 19.20% |
| Very Aggressive | 28 | 306.8 | 303 | 103.2 | 124 | 16.20% |

## Threshold attainment

| Profile | 120+ | 130+ | 135+ | 140+ | 145+ | 150+ |
|---|---:|---:|---:|---:|---:|---:|
| Neutral | 24.25% | 8.80% | 4.85% | 2.50% | 0.95% | 0.40% |
| Balanced | 18.15% | 6.80% | 3.30% | 2.10% | 0.85% | 0.35% |
| Aggressive | 19.20% | 7.95% | 4.85% | 2.80% | 1.55% | 0.65% |
| Very Aggressive | 16.20% | 5.20% | 2.80% | 1.45% | 0.75% | 0.30% |

## Interpretation

- Raising bonus priority did not improve bonus attainment. Aggressive profiles
  often consumed upper categories with mediocre scores too early.
- **120 ranged from 16.20% to 24.25%**, while 130 ranged from 5.20% to 8.80%
  and 140 ranged from 1.45% to 2.80% across profiles.
- **Keep the prototype rule at 120 → +35.** It remains demanding and is
  achieved in roughly one game in four by the strongest tested profile.
- Keep 130 as a harder alternative for later testing; restore 140 only if real
  players outperform the simulation or the third season changes the pool.
- These simulations guide the prototype setting; human playtesting remains the
  final check because people do not optimize like a deterministic heuristic.
