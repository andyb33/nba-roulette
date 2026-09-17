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
with master seed `20260917` against 895 records.

## Full-game results

| Policy | Mean | P10 | Median | P90 | Bonus rate | Spins/game |
|---|---:|---:|---:|---:|---:|---:|
| Random | 130.5 | 89 | 129 | 172 | 0.06% | 28.02 |
| Greedy | 249.0 | 189 | 244 | 316 | 4.16% | 33.32 |

## Category outcomes

| Category | Random mean | Random zero | Greedy mean | Greedy zero |
|---|---:|---:|---:|---:|
| Points | 21.94 | 0.00% | 35.00 | 0.00% |
| Rebounds | 12.85 | 0.00% | 19.41 | 0.00% |
| Assists | 7.89 | 0.00% | 14.76 | 0.00% |
| Steals | 7.68 | 0.00% | 10.36 | 0.00% |
| Blocks | 4.89 | 2.22% | 9.09 | 0.86% |
| Games Played | 53.95 | 0.00% | 67.76 | 0.00% |
| All Nba Third | 0.78 | 96.10% | 2.07 | 89.64% |
| All Nba Second | 0.76 | 97.47% | 5.03 | 83.25% |
| All Nba First | 0.56 | 98.59% | 7.50 | 81.25% |
| Champion | 0.88 | 96.48% | 11.29 | 54.82% |
| All Defense Second | 0.67 | 97.76% | 8.60 | 71.32% |
| All Defense First | 0.55 | 98.63% | 9.04 | 77.39% |
| Major Award | 0.42 | 99.16% | 10.40 | 79.20% |
| Jersey | 16.66 | 6.53% | 37.24 | 0.00% |

## Initial findings

- Greedy improves mean score by **118.5 points** over Random without using locks.
- The Upper Bonus appeared in **0.06%** of Random games and **4.16%** of Greedy games.
- Accolades remain the main source of zeroes. Even Greedy scored zero in most
  cumulative-tier All-NBA and All-Defense slots, plus Major Award.
- GP is the strongest reliable category, while Jersey provides a large but
  volatile score. A strategic policy must account for both before judging balance.

## Interpretation boundary

These are calibration baselines, not estimates of skilled-player performance.
Neither policy locks Season, Team, or Player. The Greedy policy is intentionally
myopic and compares category point values directly; the next simulation milestone
is a lock-aware strategy that values scarcity and remaining turns.
