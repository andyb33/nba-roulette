# NBA Roulette — GDD v1.2 Change Log

GDD v1.2 records the decisions made after Human Playtest 1. All other v1.1
rules remain unchanged.

## Rule changes

### Explicit Keep terminology

The player now chooses which roulette slots to **keep** before a reroll. The
wording no longer describes a kept slot as the slot being rerolled.

- `keep season` preserves Season and rerolls Team + Player.
- `keep team` preserves Team and rerolls Season + Player.
- `keep player` preserves Player and rerolls Season + Team.
- `reroll` with no slots rerolls all three.

The underlying temporary-lock mechanic is unchanged.

### Cumulative accolade eligibility

Higher team selections may score in their own category or a lower category:

| Selection | Eligible All-NBA categories |
|---|---|
| First Team | First, Second, Third |
| Second Team | Second, Third |
| Third Team | Third |

| Selection | Eligible All-Defense categories |
|---|---|
| First Team | First, Second |
| Second Team | Second |

This follows the Yahtzee relationship between a large straight and a small
straight. Each roulette result may still fill only one category.

## Confirmed rule

The Upper Bonus remains **+35 at an upper score of 120 or more**. Human
Playtest 1 did not justify changing it.

## Evidence

These changes came from Human Playtest 1 (`seed 20260917`). See
[`HUMAN_PLAYTEST_01.md`](HUMAN_PLAYTEST_01.md).

## Post-change simulation validation

The updated rules were tested with 10,000 Random games, 10,000 Greedy games,
5,000 Strategic games, and four 2,000-game bonus-sensitivity profiles.

- Random mean: **130.5**; 120 bonus rate: **0.06%**.
- Greedy mean: **249.0**; 120 bonus rate: **4.16%**.
- Strategic mean: **325.3**; 120 bonus rate: **23.34%**.
- Sensitivity profiles reached 120 in **16.20%–24.25%** of games.
- Increasing bonus priority reduced rather than improved total score and bonus
  attainment, so no bonus-chasing rule was added.

Conclusion: retain the **120 → +35** rule and cumulative accolades for the next
human playtest.
