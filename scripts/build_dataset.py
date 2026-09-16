#!/usr/bin/env python3
"""Build a validated NBA Roulette player-team-season dataset from NBA Stats."""

from __future__ import annotations

import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from season_config import SEASON_CONFIGS

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
GAME = ROOT / "data" / "game"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nba.com/"}

TEAMS = {
    "ATL": 1610612737, "BOS": 1610612738, "CLE": 1610612739,
    "NOP": 1610612740, "CHI": 1610612741, "DAL": 1610612742,
    "DEN": 1610612743, "GSW": 1610612744, "HOU": 1610612745,
    "LAC": 1610612746, "LAL": 1610612747, "MIA": 1610612748,
    "MIL": 1610612749, "MIN": 1610612750, "BKN": 1610612751,
    "NYK": 1610612752, "ORL": 1610612753, "IND": 1610612754,
    "PHI": 1610612755, "PHX": 1610612756, "POR": 1610612757,
    "SAC": 1610612758, "SAS": 1610612759, "OKC": 1610612760,
    "TOR": 1610612761, "UTA": 1610612762, "MEM": 1610612763,
    "WAS": 1610612764, "DET": 1610612765, "CHA": 1610612766,
}


def season_slug(season: str) -> str:
    return season.replace("-", "_")


def nba_get(endpoint: str, params: dict, retries: int = 7) -> dict:
    url = f"https://stats.nba.com/stats/{endpoint}?{urlencode(params)}"
    error = None
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=45) as response:
                return json.loads(response.read())
        except Exception as exc:
            error = exc
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"NBA Stats request failed: {endpoint} {params}") from error


def url_get(url: str, retries: int = 7) -> dict:
    error = None
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=45) as response:
                return json.loads(response.read())
        except Exception as exc:
            error = exc
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"Request failed: {url}") from error


def result_rows(payload: dict, name: str | None = None) -> list[dict]:
    result = payload["resultSets"][0] if name is None else next(
        item for item in payload["resultSets"] if item["name"] == name
    )
    return [dict(zip(result["headers"], row)) for row in result["rowSet"]]


def fetch_team(season: str, raw: Path, abbr: str, team_id: int) -> tuple[str, dict, dict]:
    stats_path = raw / f"{abbr}_stats.json"
    roster_path = raw / f"{abbr}_roster.json"
    if stats_path.exists() and roster_path.exists():
        return abbr, json.loads(stats_path.read_text()), json.loads(roster_path.read_text())
    stats = nba_get("leaguedashplayerstats", {
        "College": "", "Conference": "", "Country": "", "DateFrom": "", "DateTo": "",
        "Division": "", "DraftPick": "", "DraftYear": "", "GameScope": "",
        "GameSegment": "", "Height": "", "LastNGames": 0, "LeagueID": "00",
        "Location": "", "MeasureType": "Base", "Month": 0, "OpponentTeamID": 0,
        "Outcome": "", "PORound": 0, "PaceAdjust": "N", "PerMode": "PerGame",
        "Period": 0, "PlayerExperience": "", "PlayerPosition": "", "PlusMinus": "N",
        "Rank": "N", "Season": season, "SeasonSegment": "", "SeasonType": "Regular Season",
        "ShotClockRange": "", "StarterBench": "", "TeamID": team_id,
        "VsConference": "", "VsDivision": "", "Weight": "",
    })
    roster = nba_get("commonteamroster", {"LeagueID": "00", "Season": season, "TeamID": team_id})
    return abbr, stats, roster


def final_game_jersey(season: str, team: str, player_id: int, player_name: str) -> dict:
    logs = result_rows(nba_get("playergamelog", {
        "PlayerID": player_id, "Season": season, "SeasonType": "Regular Season"
    }))
    team_games = [game for game in logs if game["MATCHUP"].startswith(team)]
    if not team_games:
        raise ValueError(f"No {team} game found for {player_name} ({player_id})")
    team_games.sort(key=lambda game: time.strptime(game["GAME_DATE"], "%b %d, %Y"), reverse=True)
    game = team_games[0]
    box = url_get(
        f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game['Game_ID']}.json"
    )
    for side in (box["game"]["homeTeam"], box["game"]["awayTeam"]):
        if side["teamTricode"] != team:
            continue
        for player in side["players"]:
            if int(player["personId"]) == player_id:
                return {
                    "team": team,
                    "player_id": player_id,
                    "player": player_name,
                    "last_game_date": game["GAME_DATE"],
                    "game_id": game["Game_ID"],
                    "verified_final_jersey": int(player["jerseyNum"]),
                    "status": "VERIFIED",
                }
    raise ValueError(f"No box-score jersey found for {player_name} ({player_id})")


def load_jersey_audit(path: Path) -> tuple[dict[tuple[str, int], int], list[dict]]:
    if not path.exists():
        return {}, []
    with path.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    mapping = {
        (row["team"], int(row["player_id"])): int(row["verified_final_jersey"])
        for row in rows if row.get("verified_final_jersey") not in (None, "")
    }
    return mapping, rows


def award_team(name: str, mapping: dict[int, set[str]]) -> int | None:
    return next((team for team, names in mapping.items() if name in names), None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", required=True, choices=sorted(SEASON_CONFIGS))
    args = parser.parse_args()
    season = args.season
    slug = season_slug(season)
    config = SEASON_CONFIGS[season]
    raw = ROOT / "data" / "raw" / season
    audit_path = PROCESSED / f"jersey_verification_{slug}.csv"
    raw.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    GAME.mkdir(parents=True, exist_ok=True)

    payloads = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(fetch_team, season, raw, abbr, team_id): abbr
            for abbr, team_id in TEAMS.items()
        }
        for future in as_completed(futures):
            abbr, stats, roster = future.result()
            payloads[abbr] = (stats, roster)
            (raw / f"{abbr}_stats.json").write_text(json.dumps(stats), encoding="utf-8")
            (raw / f"{abbr}_roster.json").write_text(json.dumps(roster), encoding="utf-8")
            print(f"Fetched {abbr}")

    cached_jerseys, audit_rows = load_jersey_audit(audit_path)
    candidates = []
    records = []
    for abbr in TEAMS:
        stats, roster = payloads[abbr]
        jersey_by_id = {
            int(row["PLAYER_ID"]): row.get("NUM")
            for row in result_rows(roster, "CommonTeamRoster")
            if row.get("NUM") not in (None, "")
        }
        for row in result_rows(stats, "LeagueDashPlayerStats"):
            if int(row["GP"]) < 15 or float(row["MIN"]) < 10.0:
                continue
            player_id = int(row["PLAYER_ID"])
            name = row["PLAYER_NAME"]
            jersey_raw = jersey_by_id.get(player_id, cached_jerseys.get((abbr, player_id)))
            record = {
                "season": season, "player_id": player_id, "player": name, "team": abbr,
                "gp": int(row["GP"]), "mpg": round(float(row["MIN"]), 1),
                "ppg": round(float(row["PTS"]), 1), "rpg": round(float(row["REB"]), 1),
                "apg": round(float(row["AST"]), 1), "spg": round(float(row["STL"]), 1),
                "bpg": round(float(row["BLK"]), 1),
                "jersey": int(jersey_raw) if jersey_raw is not None and str(jersey_raw).isdigit() else None,
                "all_nba": award_team(name, config["all_nba"]),
                "all_defense": award_team(name, config["all_defense"]),
                "champion": abbr == config["champion"],
                "mvp": name == config["mvp"], "dpoy": name == config["dpoy"],
                "roy": name == config["roy"],
            }
            records.append(record)
            if record["jersey"] is None:
                candidates.append(record)

    discovered = []
    if candidates:
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                pool.submit(final_game_jersey, season, row["team"], row["player_id"], row["player"]): row
                for row in candidates
            }
            for future in as_completed(futures):
                audit = future.result()
                discovered.append(audit)
                row = futures[future]
                row["jersey"] = audit["verified_final_jersey"]
                print(f"Verified {row['team']} {row['player']} #{row['jersey']}")

    if discovered:
        audit_by_key = {(row["team"], int(row["player_id"])): row for row in audit_rows}
        audit_by_key.update({(row["team"], int(row["player_id"])): row for row in discovered})
        audit_rows = sorted(audit_by_key.values(), key=lambda row: (row["team"], row["player"]))
        fields = ["team", "player_id", "player", "last_game_date", "game_id", "verified_final_jersey", "status"]
        with audit_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(audit_rows)

    records.sort(key=lambda row: (row["team"], row["player"]))
    fields = list(records[0])
    csv_path = PROCESSED / f"nba_roulette_{slug}.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    (GAME / f"players_{slug}.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    missing = [row for row in records if row["jersey"] is None]
    summary = {
        "season": season,
        "eligibility": {"minimum_team_gp": 15, "minimum_team_mpg": 10.0},
        "eligible_player_team_records": len(records),
        "eligible_records_by_team": {
            team: sum(row["team"] == team for row in records) for team in TEAMS
        },
        "missing_jersey_records": len(missing),
        "historical_jersey_records_verified": len(audit_rows),
        "all_nba_records": sum(row["all_nba"] is not None for row in records),
        "all_defense_records": sum(row["all_defense"] is not None for row in records),
        "champion_records": sum(row["champion"] for row in records),
        "major_award_records": sum(row["mvp"] or row["dpoy"] or row["roy"] for row in records),
    }
    (PROCESSED / f"nba_roulette_{slug}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    if missing:
        raise SystemExit(f"Validation failed: {len(missing)} missing jerseys")


if __name__ == "__main__":
    main()
