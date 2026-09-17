# NBA Roulette — Strategic Lock-Aware Simulation

The Strategic policy is a transparent heuristic, not a claim of optimal play.
It values each score against that category's expected replacement value, adds
limited Upper Bonus equity, and compares every legal lock mask using exact
hierarchical outcome probabilities before each reroll.

The policy played **5,000 complete games** with master seed
`20260918` against 1346 player-team records.

## Comparison

| Policy | Mean | P10 | Median | P90 | Bonus rate | Spins/game |
|---|---:|---:|---:|---:|---:|---:|
| Random | 130.8 | 90 | 130 | 172 | 0.05% | 28.02 |
| Greedy | 247.7 | 188 | 243 | 314 | 3.84% | 33.31 |
| Strategic | 328.2 | 258 | 325 | 401 | 23.80% | 35.25 |

## Strategic category outcomes

| Category | Mean | Zero rate | Greedy zero rate |
|---|---:|---:|---:|
| Points | 43.77 | 0.00% | 0.00% |
| Rebounds | 24.57 | 0.00% | 0.00% |
| Assists | 16.71 | 0.00% | 0.00% |
| Steals | 12.07 | 0.00% | 0.00% |
| Blocks | 11.59 | 0.02% | 1.05% |
| Games Played | 76.64 | 0.00% | 0.00% |
| All Nba Third | 5.93 | 70.34% | 89.92% |
| All Nba Second | 14.33 | 52.24% | 82.34% |
| All Nba First | 11.09 | 72.28% | 83.26% |
| Champion | 15.67 | 37.32% | 54.13% |
| All Defense Second | 17.57 | 41.42% | 70.73% |
| All Defense First | 13.47 | 66.32% | 76.22% |
| Major Award | 10.59 | 78.82% | 79.37% |
| Jersey | 45.86 | 0.00% | 0.00% |

## Lock use

| Lock mask | Average uses per game |
|---|---:|
| none | 3.75 |
| player | 2.96 |
| season | 4.91 |
| season+player | 0.16 |
| season+team | 5.82 |
| team | 3.02 |
| team+player | 0.63 |

## Findings

- Strategic play changes mean score by **+80.5 points** versus Greedy.
- The Upper Bonus rate rises from **3.84%** to **23.80%**.
- Category zero rates show whether lock knowledge meaningfully improves rare
  accolades rather than merely increasing common statistical scores.
- The heuristic's assumptions should be varied in sensitivity tests before any
  permanent scoring change is made.

## Effect of adding 2025–26

| Metric | Two-season | Three-season | Change |
|---|---:|---:|---:|
| Mean score | 325.3 | 328.2 | +2.9 |
| Median score | 322 | 325 | +2 |
| Upper Bonus rate | 23.34% | 23.80% | +0.46% |
