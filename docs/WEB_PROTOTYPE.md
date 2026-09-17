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
