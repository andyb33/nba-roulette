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
| Random | 129.3 | 88 | 128 | 171 | 0.00% | 28.02 |
| Greedy | 246.7 | 188 | 243 | 310 | 0.22% | 33.35 |
| Strategic | 315.8 | 250 | 313 | 385 | 2.50% | 35.31 |

## Strategic category outcomes

| Category | Mean | Zero rate | Greedy zero rate |
|---|---:|---:|---:|
| Points | 43.74 | 0.00% | 0.00% |
| Rebounds | 24.59 | 0.00% | 0.00% |
| Assists | 17.00 | 0.00% | 0.00% |
| Steals | 12.20 | 0.00% | 0.00% |
| Blocks | 11.71 | 0.00% | 0.89% |
| Games Played | 76.67 | 0.00% | 0.00% |
| All Nba Third | 1.67 | 91.64% | 90.69% |
| All Nba Second | 6.28 | 79.08% | 84.46% |
| All Nba First | 14.20 | 64.50% | 81.24% |
| Champion | 14.52 | 41.94% | 54.58% |
| All Defense Second | 11.69 | 61.04% | 72.84% |
| All Defense First | 16.20 | 59.50% | 77.39% |
| Major Award | 17.82 | 64.36% | 79.17% |
| Jersey | 46.68 | 0.00% | 0.00% |

## Lock use

| Lock mask | Average uses per game |
|---|---:|
| none | 4.17 |
| player | 2.53 |
| season | 5.83 |
| season+player | 0.16 |
| season+team | 5.65 |
| team | 2.80 |
| team+player | 0.16 |

## Findings

- Strategic play changes mean score by **+69.1 points** versus Greedy.
- The Upper Bonus rate rises from **0.22%** to **2.50%**.
- Category zero rates show whether lock knowledge meaningfully improves rare
  accolades rather than merely increasing common statistical scores.
- The heuristic's assumptions should be varied in sensitivity tests before any
  permanent scoring change is made.
