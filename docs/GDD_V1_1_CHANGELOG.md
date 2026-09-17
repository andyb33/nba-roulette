# NBA Roulette — GDD v1.1 Change Log

GDD v1.1 preserves every v1.0 rule except the Upper Bonus threshold.

## Upper Bonus

- **v1.0 hypothesis:** 140+ across PTS, REB, AST, STL, and BLK → +35.
- **v1.1 prototype rule:** 120+ across PTS, REB, AST, STL, and BLK → +35.

The reward remains +35 and Games Played remains excluded.

## Evidence

Two-season simulations found approximately:

- 140+: 2–3% attainment under lock-aware sensitivity profiles;
- 130+: 9–10%;
- 120+: 20–26%.

Increasing bonus priority did not materially improve 140 attainment and often
caused upper categories to be consumed too early. The 120 threshold was selected
for the prototype because it remains demanding while being realistically
attainable. The 130 threshold remains a harder playtest alternative.

See [`BONUS_SENSITIVITY.md`](BONUS_SENSITIVITY.md) for the experiment.
