# NBA Roulette — Minimal Browser Prototype

The first browser prototype is a deliberately small interface for validating
the game loop before investing in production visuals or animation.

## Run locally

```bash
python scripts/run_web.py
```

Open `http://127.0.0.1:8000` in a browser. The server uses only Python's
standard library and the existing NBA Roulette package.

## Included

- Complete 14-turn game using the three-season, 1,346-record pool.
- Season, Team, and Player roulette slots.
- Explicit **Keep** controls with persistent, reversible selections.
- One initial spin and up to two rerolls per turn.
- Live player statistics, jersey number, and qualifying accolades.
- Live previews for every unused score category.
- Cumulative All-NBA and All-Defense eligibility.
- 120-point Upper Bonus progress and +35 award.
- Mandatory category assignment, including zero-point sacrifices.
- Final score dialog and New Game flow.
- Responsive desktop and mobile layouts.

## Prototype v0.2 — Playtest-driven interface

Human Playtests 2–6 produced the following interface changes:

- Desktop scorecard moved to the left, with roulette and player information on
  the right; mobile keeps the action-first single-column flow.
- Statistical and Joker formulas are always visible on the scorecard.
- Accolade rows show their emoji and fixed point value.
- Any currently qualifying accolade receives a gold animated glow.
- Elite score previews receive a green glow at PTS 40+, REB 30+, AST 30+,
  STL 20+, BLK 20+, GP 80+, and Jersey 70+.
- Previously scored elite/qualifying outcomes retain a small marker without
  continuing to pulse.
- Jersey number is presented in a jersey silhouette using team colors.
- Player accolades appear as vertical icon badges.
- Reduced-motion preferences disable the pulsing animations.

## Architecture

The browser sends commands to a small JSON server. `BrowserGame` serializes the
existing `GameState`; it does not reimplement roulette or scoring rules in
JavaScript. In-memory sessions keep separate games isolated through a cookie.

## Prototype limitations

- Local development server only; it is not production hardened.
- Games are lost when the server restarts.
- No animation, sound, accounts, leaderboard, or sharing.
- Team abbreviations are shown instead of licensed team branding.
- Player photos and NBA logos are intentionally absent.

These limitations keep the prototype focused on the next evidence question:
does the full browser game remain understandable and replayable for Human
Playtest 2?

## Reroll difference rule

Prototype v0.3 excludes the exact current Player × Team × Season result from a
reroll whenever another valid outcome exists. Keeping Team + Player therefore
forces a different season; keeping Season + Team forces a different player.
The fallback permits a repeat only when the selected Keeps leave no alternative.

## Prototype v0.4 — Unlocked slots visibly reroll

Human testing showed that keeping Team could still return the same Season,
which made an unlocked roulette slot appear not to reroll. v0.4 now requires
every unlocked slot to change whenever one valid combined outcome permits it.
If strict change is impossible, the engine falls back to a different complete
result rather than invalidating the turn.

Used scorecard categories now use a filled slate background, inset status bar,
and check badge. High-value used categories retain gold emphasis, but no longer
look like currently selectable glowing opportunities.

## Playtest Batch 3 logging

The next ten completed local games are automatically recorded as **Playtest
Batch 3 — v0.4 Unlocked-Slot Validation**. The server creates two untracked
local files:

- `playtest_logs/playtest_batch_03_v0_4_unlocked_slot_validation.jsonl` contains one
  detailed JSON record per game, including every visible spin, Keep selection,
  scored player, category result, repeat count, and final score.
- `playtest_logs/playtest_batch_03_v0_4_unlocked_slot_validation.csv` contains one
  summary row per game for quick spreadsheet analysis.

The batch stops recording after ten completed games. Starting or abandoning an
unfinished game does not consume a batch slot. The `playtest_logs/` directory is
excluded from Git so local participant data is not committed accidentally.
Any partially completed Batch 2 files remain untouched for diagnostic analysis.
