# GDD v1.3 — Reroll Difference Rule

## Evidence

Human Playtests 7–9 ended at 335, 321, and 399. Across all eight recorded
browser games, the mean is 308.4 and the median is 303.5. The player reported
that scoring became easier to understand with experience, score variation felt
good, but Keeps felt weak because a reroll could return the exact same result.

Example: keeping 2024–25 San Antonio and rerolling Jeremy Sochan could return
the same player-team-season. Likewise, keeping Stephon Castle + San Antonio did
not guarantee movement to his other eligible season.

## Rule change

Every reroll excludes the exact current Player × Team × Season result whenever
at least one legal alternative satisfies the selected Keeps.

- Keep Team + Player: the season must change.
- Keep Season + Team: the player must change.
- Keep Season + Player: the team must change when another eligible team stint
  exists.
- Other Keep masks and full rerolls cannot return the identical three-slot
  result.
- If the selected Keeps leave only one legal record, that record may repeat.

The remaining valid outcomes continue to use hierarchical equal weighting.

## Duplicate-player audit

A 5,000-game audit using fair, fully unlocked spins found:

| Observation window | Mean repeated-player appearances | Games with at least one repeat |
|---|---:|---:|
| 14 final-style results | 0.186 | 17.3% |
| 42 visible results | 1.758 | 84.4% |

Seeing repeat players is therefore expected when a player views up to 42
results. This does not indicate that individual players are overweighted.

## Decision

Implement the reroll difference rule now because it directly improves agency.
Do not yet ban a player from reappearing elsewhere in the same game: that would
materially change the stated Season → Team → Player probabilities and reduce
the value of knowledge about multi-season players. Reassess only if repeats
remain frustrating after testing v0.3.
