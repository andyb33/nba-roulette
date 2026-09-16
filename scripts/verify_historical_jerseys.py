#!/usr/bin/env python3
"""Verify final team-specific jerseys using each player's last NBA game for that team."""

from __future__ import annotations

import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from build_2023_24_dataset import HEADERS, JERSEY_OVERRIDES, SEASON

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/processed/jersey_verification_2023_24.csv"


def get_json(url: str, retries: int = 4) -> dict:
    error = None
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=45) as response:
                return json.loads(response.read())
        except Exception as exc:
            error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(url) from error


def rows(payload: dict) -> list[dict]:
    result = payload["resultSets"][0]
    return [dict(zip(result["headers"], row)) for row in result["rowSet"]]


def verify(item: tuple[tuple[str, int], int]) -> dict:
    (team, player_id), expected = item
    params = urlencode({"PlayerID": player_id, "Season": SEASON, "SeasonType": "Regular Season"})
    logs = rows(get_json(f"https://stats.nba.com/stats/playergamelog?{params}"))
    team_games = [g for g in logs if g["MATCHUP"].startswith(team)]
    if not team_games:
        raise ValueError(f"No {team} games for player {player_id}")
    # NBA PlayerGameLog is returned newest first; explicitly sort by game date.
    team_games.sort(key=lambda g: time.strptime(g["GAME_DATE"], "%b %d, %Y"), reverse=True)
    game = team_games[0]
    game_id = game["Game_ID"]
    box = get_json(f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json")
    verified = None
    player_name = None
    for side in (box["game"]["homeTeam"], box["game"]["awayTeam"]):
        if side["teamTricode"] != team:
            continue
        for player in side["players"]:
            if int(player["personId"]) == player_id:
                player_name = player["name"]
                verified = int(player["jerseyNum"])
                break
    return {
        "team": team,
        "player_id": player_id,
        "player": player_name,
        "last_game_date": game["GAME_DATE"],
        "game_id": game_id,
        "expected_final_jersey": expected,
        "verified_final_jersey": verified,
        "status": "MATCH" if expected == verified else "MISMATCH",
    }


def main() -> None:
    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(verify, item) for item in JERSEY_OVERRIDES.items()]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(result["status"], result["team"], result["player"], result["verified_final_jersey"])
    results.sort(key=lambda row: (row["team"], row["player"] or ""))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    mismatches = [row for row in results if row["status"] != "MATCH"]
    print(f"Verified {len(results)} overrides; mismatches: {len(mismatches)}")
    if mismatches:
        print(json.dumps(mismatches, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
