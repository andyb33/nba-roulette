# NBA Roulette — Random and Greedy Baselines

This report establishes two reproducible, non-strategic full-game baselines
before introducing lock-aware play.

## Policy definitions

- **Random:** uses no locks, chooses 1–3 spins uniformly, then assigns the
  result to a uniformly random open category.
- **Greedy:** uses no locks, selects the highest current open-category score,
  and rerolls only while that score is below the expected best score of a fresh
  unlocked spin. It does not plan across future turns.

Both policies played **10,000 complete 14-turn games**
with master seed `20260917` against 1346 records.

## Full-game results

| Policy | Mean | P10 | Median | P90 | Bonus rate | Spins/game |
|---|---:|---:|---:|---:|---:|---:|
| Random | 130.8 | 90 | 130 | 172 | 0.05% | 28.02 |
| Greedy | 247.7 | 188 | 243 | 314 | 3.84% | 33.31 |

## Category outcomes

| Category | Random mean | Random zero | Greedy mean | Greedy zero |
|---|---:|---:|---:|---:|
| Points | 22.22 | 0.00% | 34.57 | 0.00% |
| Rebounds | 12.81 | 0.00% | 19.25 | 0.00% |
| Assists | 7.90 | 0.00% | 14.53 | 0.00% |
| Steals | 7.85 | 0.00% | 10.60 | 0.00% |
| Blocks | 4.74 | 2.27% | 8.80 | 1.05% |
| Games Played | 54.28 | 0.00% | 67.61 | 0.00% |
| All Nba Third | 0.74 | 96.32% | 2.02 | 89.92% |
| All Nba Second | 0.79 | 97.37% | 5.30 | 82.34% |
| All Nba First | 0.50 | 98.75% | 6.70 | 83.26% |
| Champion | 0.88 | 96.50% | 11.47 | 54.13% |
| All Defense Second | 0.78 | 97.40% | 8.78 | 70.73% |
| All Defense First | 0.54 | 98.64% | 9.51 | 76.22% |
| Major Award | 0.32 | 99.36% | 10.31 | 79.37% |
| Jersey | 16.41 | 6.67% | 36.89 | 0.00% |

## Initial findings

- Greedy improves mean score by **116.9 points** over Random without using locks.
- The Upper Bonus appeared in **0.05%** of Random games and **3.84%** of Greedy games.
- Accolades remain the main source of zeroes. Even Greedy scored zero in most
  cumulative-tier All-NBA and All-Defense slots, plus Major Award.
- GP is the strongest reliable category, while Jersey provides a large but
  volatile score. A strategic policy must account for both before judging balance.

## Effect of adding 2025–26

| Policy | Two-season mean | Three-season mean | Change | Two-season bonus | Three-season bonus |
|---|---:|---:|---:|---:|---:|
| Random | 130.5 | 130.8 | +0.3 | 0.06% | 0.05% |
| Greedy | 249.0 | 247.7 | -1.3 | 4.16% | 3.84% |

## Interpretation boundary

These are calibration baselines, not estimates of skilled-player performance.
Neither policy locks Season, Team, or Player. The Greedy policy is intentionally
myopic and compares category point values directly; the next simulation milestone
is a lock-aware strategy that values scarcity and remaining turns.
