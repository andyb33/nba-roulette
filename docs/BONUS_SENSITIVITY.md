# NBA Roulette — Upper Bonus Sensitivity

This experiment varies only the heuristic value assigned to progress in each
upper category. Roulette rules, locks, score values, seeds, and dataset remain
unchanged. Bonus equity is a decision weight, not points added to the game score.

Each profile played **1,000 complete games** against
895 records using common starting seed `20260919`.

| Profile | Equity/category | Mean total | Median | Mean upper | Upper P90 | Bonus rate |
|---|---:|---:|---:|---:|---:|---:|
| Neutral | 0 | 319.7 | 318 | 110.7 | 129 | 3.20% |
| Balanced | 7 | 315.3 | 312 | 107.8 | 128 | 2.30% |
| Aggressive | 14 | 314.0 | 311 | 107.4 | 129 | 3.00% |
| Very Aggressive | 28 | 309.2 | 305 | 105.6 | 128 | 2.80% |

## Threshold attainment

| Profile | 120+ | 130+ | 135+ | 140+ | 145+ | 150+ |
|---|---:|---:|---:|---:|---:|---:|
| Neutral | 25.80% | 9.70% | 5.30% | 3.20% | 1.30% | 0.60% |
| Balanced | 20.70% | 8.90% | 4.10% | 2.30% | 1.30% | 0.70% |
| Aggressive | 20.90% | 9.00% | 5.50% | 3.00% | 2.20% | 0.90% |
| Very Aggressive | 20.10% | 8.70% | 5.00% | 2.80% | 1.40% | 0.60% |

## Interpretation

- Raising bonus priority did not materially increase 140 attainment. Aggressive
  profiles often consumed upper categories with mediocre scores too early.
- **140 remained around 2–3%**, while 130 was approximately 9–10% and 120 was
  approximately 20–26% across profiles.
- **Prototype recommendation: test 120 → +35.** It is still demanding, but its
  modeled attainment is close to one game in four rather than one in forty.
- Keep 130 as the harder alternative during human playtesting; restore 140 only
  if real players outperform the simulation or the third season changes the pool.
- These simulations guide the prototype setting; human playtesting remains the
  final check because people do not optimize like a deterministic heuristic.
