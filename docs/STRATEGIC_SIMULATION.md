# NBA Roulette — Strategic Lock-Aware Simulation

The Strategic policy is a transparent heuristic, not a claim of optimal play.
It values each score against that category's expected replacement value, adds
limited Upper Bonus equity, and compares every legal lock mask using exact
hierarchical outcome probabilities before each reroll.

The policy played **5,000 complete games** with master seed
`20260918` against 895 player-team records.

## Comparison

| Policy | Mean | P10 | Median | P90 | Bonus rate | Spins/game |
|---|---:|---:|---:|---:|---:|---:|
| Random | 130.5 | 89 | 129 | 172 | 0.06% | 28.02 |
| Greedy | 249.0 | 189 | 244 | 316 | 4.16% | 33.32 |
| Strategic | 325.3 | 257 | 322 | 399 | 23.34% | 35.01 |

## Strategic category outcomes

| Category | Mean | Zero rate | Greedy zero rate |
|---|---:|---:|---:|
| Points | 43.76 | 0.00% | 0.00% |
| Rebounds | 24.45 | 0.00% | 0.00% |
| Assists | 16.81 | 0.00% | 0.00% |
| Steals | 12.18 | 0.00% | 0.00% |
| Blocks | 11.81 | 0.00% | 0.86% |
| Games Played | 76.69 | 0.00% | 0.00% |
| All Nba Third | 6.05 | 69.76% | 89.64% |
| All Nba Second | 14.41 | 51.96% | 83.25% |
| All Nba First | 11.11 | 72.22% | 81.25% |
| Champion | 14.35 | 42.60% | 54.82% |
| All Defense Second | 15.05 | 49.84% | 71.32% |
| All Defense First | 12.35 | 69.12% | 77.39% |
| Major Award | 11.44 | 77.12% | 79.20% |
| Jersey | 46.65 | 0.00% | 0.00% |

## Lock use

| Lock mask | Average uses per game |
|---|---:|
| none | 3.95 |
| player | 2.61 |
| season | 5.35 |
| season+player | 0.16 |
| season+team | 5.84 |
| team | 2.94 |
| team+player | 0.16 |

## Findings

- Strategic play changes mean score by **+76.3 points** versus Greedy.
- The Upper Bonus rate rises from **4.16%** to **23.34%**.
- Category zero rates show whether lock knowledge meaningfully improves rare
  accolades rather than merely increasing common statistical scores.
- The heuristic's assumptions should be varied in sensitivity tests before any
  permanent scoring change is made.
