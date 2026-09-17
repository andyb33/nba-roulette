# NBA Roulette — Human Playtest 1

**Date:** 2026-09-17  
**Build:** GDD v1.1 terminal prototype  
**Seed:** `20260917`  
**Result:** 257 points in 38 spins

## Final scorecard

| Category | Player used | Score |
|---|---|---:|
| Points | Paul George | 45 |
| Rebounds | Jalen Johnson | 30 |
| Assists | Patrick Beverley | 9 |
| Steals | Desmond Bane | 12 |
| Blocks | Jabari Walker | 1 |
| Games Played | Keegan Murray | 77 |
| All-NBA Third | Terrence Shannon Jr. | 0 |
| All-NBA Second | Josh Okogie | 0 |
| All-NBA First | Nick Smith Jr. | 0 |
| Champion | Ajay Mitchell | 25 |
| All-Defense Second | Duop Reath | 0 |
| All-Defense First | Luguentz Dort | 40 |
| Major Award | Alec Burks | 0 |
| Jersey Number | Alec Burks (Miami) | 18 |

Upper score: **97**. Upper Bonus: **0**. Final score: **257**.

## Findings and decisions

1. **Reroll wording was ambiguous.** A phrase such as “reroll team” was being
   used to mean that Team stayed fixed. The interface will instead ask which
   slots to **keep**.
2. **Accolade tiers should be cumulative.** All-NBA First qualifies for First,
   Second, or Third; All-NBA Second qualifies for Second or Third. All-Defense
   First qualifies for First or Second. This creates useful flexibility without
   increasing the score awarded by any category.
3. **Keep the 120-point Upper Bonus threshold.** The playtest upper score was
   97. A discarded 19-point blocks result would have raised the theoretical
   finish to 115, so 120 remained demanding but plausible.
4. **Season streaks felt suspicious but were valid randomness.** Engine tests
   continue to verify equal season weighting; no probability rule changed.
5. **The eligibility cutoff behaved as designed.** An unfamiliar result,
   Onuralp Bitim, was verified as eligible with 23 games and 11.7 MPG.

## Follow-up

- Implement the terminology and cumulative-tier changes as GDD v1.2.
- Rerun random, greedy, strategic, and bonus-sensitivity simulations. **Complete.**
- Repeat the terminal playtest after reviewing the new model results.
