# NBA Roulette — Three-Season Distribution Report

- **Seasons:** 2023–24 through 2025–26
- **Eligible player-team-season records:** 1346
- **Eligibility:** 15+ GP and 10.0+ MPG for the selected team
- **Status:** Descriptive balance analysis; the three-season roulette simulation follows separately.

## Executive Summary

- The five performance categories are not naturally equal after weighting. PTS has a roulette-weighted median of 19, while BLK has a median of 4.
- PTS supplies the highest routine scores. AST, STL, and especially BLK remain the specialist outcomes most likely to constrain the 120-point Upper Bonus.
- GP is a consistently valuable Joker: median 57, P90 78, and maximum 82.
- Jersey is intentionally volatile: median 12, P90 34, and maximum 99. High numbers produce rare rescue or jackpot outcomes.
- Cumulative tiers create the intended rarity ladder: All-NBA Third accepts 3.77% of unlocked spins, Second accepts 2.54%, and First accepts 1.28%.
- Adding 2025–26 does not by itself justify a scoring change. The 120 → +35 rule should be judged again in the upcoming three-season simulation.

## Method

The canonical observation is one **Player × Team × Season** record. The report distinguishes:

1. **Record-weighted distributions**, where each of the 1,346 rows counts equally.
2. **Roulette-weighted distributions**, matching the game rule: equal Season → equal Team → equal eligible Player.

The second view is the relevant gameplay baseline because team roster sizes vary. Scores use the GDD multipliers and round-half-up rule:

- PTS = PPG × 2
- REB = RPG × 3
- AST = APG × 3
- STL = SPG × 10
- BLK = BPG × 10
- GP = games played
- Jersey = final jersey number for the team stint

## Statistical Score Distributions

| Category | Mean | Median | P75 | P90 | P95 | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| PTS ×2 | 22.1 | 19 | 29 | 42 | 48 | 69 |
| REB ×3 | 12.7 | 11 | 16 | 22 | 27 | 42 |
| AST ×3 | 7.8 | 6 | 11 | 16 | 19 | 35 |
| STL ×10 | 7.8 | 7 | 10 | 13 | 15 | 30 |
| BLK ×10 | 4.7 | 4 | 6 | 10 | 12 | 38 |

![Statistical category distributions](../analysis/charts/stat_score_distributions.png)

![Category percentiles](../analysis/charts/category_percentiles.png)

### Interpretation

- A P90 outcome is approximately 42 PTS points, 22 REB points, 16 AST points, 13 STL points, and 10 BLK points.
- Even strong percentile selections do not make the Upper Bonus automatic. The player must assemble quality across five different outcomes and categories.
- Category multipliers should not be judged by equal medians alone. Scarcity and the value of targeted locks are part of the intended strategy.

## Season Comparison

| Category | 2023-24 mean | 2024-25 mean | 2025-26 mean |
|---|---:|---:|---:|
| PTS ×2 | 21.5 | 22.2 | 22.5 |
| REB ×3 | 12.5 | 12.9 | 12.6 |
| AST ×3 | 7.7 | 7.9 | 7.9 |
| STL ×10 | 7.2 | 8.1 | 8.1 |
| BLK ×10 | 4.9 | 4.7 | 4.5 |

![Season score comparison](../analysis/charts/season_score_comparison.png)

## Effect of Adding 2025–26

| Category | Two-season mean | Three-season mean | Change |
|---|---:|---:|---:|
| PTS ×2 | 21.9 | 22.1 | +0.2 |
| REB ×3 | 12.7 | 12.7 | -0.0 |
| AST ×3 | 7.8 | 7.8 | +0.0 |
| STL ×10 | 7.7 | 7.8 | +0.1 |
| BLK ×10 | 4.8 | 4.7 | -0.1 |
| GP | 54.0 | 54.0 | -0.0 |
| JERSEY | 16.5 | 16.4 | -0.1 |

This comparison uses roulette weighting in both pools. It isolates whether adding the third season materially changes the distribution rather than merely adding more rows.

## Joker Categories

| Category | Mean | Median | P75 | P90 | P95 | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| GP | 54.0 | 57 | 71 | 78 | 80 | 82 |
| Jersey | 16.4 | 12 | 24 | 34 | 44 | 99 |

![Joker distributions](../analysis/charts/joker_distributions.png)

GP is the safer Joker; Jersey has the heavier upside tail. That distinction supports the intended rescue mechanic without making the categories function identically.

## Accolade Rarity

| Category | Eligible records | Standard-spin probability | Score |
|---|---:|---:|---:|
| All-NBA Third (First/Second/Third eligible) | 45 | 3.77% | 20 |
| All-NBA Second (First/Second eligible) | 30 | 2.54% | 30 |
| All-NBA First | 15 | 1.28% | 40 |
| Champion | 38 | 3.33% | 25 |
| All-Defense Second (First/Second eligible) | 30 | 2.52% | 30 |
| All-Defense First | 15 | 1.24% | 40 |
| Major Award | 9 | 0.75% | 50 |

![Accolade probabilities](../analysis/charts/accolade_probabilities.png)

Major Award and First-team categories remain the rarest targets. The cumulative rule makes lower-tier categories appropriately easier without changing their fixed scores.

## Observed Category Ceilings

| Category | Highest eligible player-team-season | Score |
|---|---|---:|
| PTS ×2 | Joel Embiid — PHI 2023-24 | 69 |
| REB ×3 | Domantas Sabonis — SAC 2024-25 | 42 |
| AST ×3 | Trae Young — ATL 2024-25 | 35 |
| STL ×10 | Dyson Daniels — ATL 2024-25 | 30 |
| BLK ×10 | Victor Wembanyama — SAS 2024-25 | 38 |
| GP | Austin Reaves — LAL 2023-24 | 82 |
| JERSEY | Jae Crowder — MIL 2023-24 | 99 |


## Dataset and Season Checks

- 2023–24: 441 eligible records.
- 2024–25: 454 eligible records.
- 2025–26: 451 eligible records.
- Every season contains all 30 teams.
- Eligible roster sizes range from 11 to 22 players per team-season.
- The analysis contains no missing jersey values and no records below the eligibility thresholds.

## Balance Decisions Supported Now

1. Retain the existing statistical multipliers for the first playable prototype.
2. Retain GP and Jersey as deliberately different Joker distributions.
3. Retain cumulative accolade eligibility and the fixed accolade scores.
4. Retain **120 → +35** for the next simulation; distributions alone do not overturn the playtest and two-season simulation evidence.
5. Rerun Random, Greedy, Strategic, and sensitivity simulations before making another balance change.

## Reproduce

```bash
python scripts/analyze_distributions.py
```

This regenerates the JSON summary, CSV tables, charts, and this report from the three processed season datasets.
