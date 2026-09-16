#!/usr/bin/env python3
"""Build NBA Roulette's 2023-24 player-team-season dataset from NBA Stats."""

from __future__ import annotations

import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SEASON = "2023-24"
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / SEASON
PROCESSED = ROOT / "data" / "processed"
GAME = ROOT / "data" / "game"

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

ALL_NBA = {
    1: {"Nikola Jokić", "Shai Gilgeous-Alexander", "Luka Dončić", "Giannis Antetokounmpo", "Jayson Tatum"},
    2: {"Jalen Brunson", "Anthony Edwards", "Kevin Durant", "Kawhi Leonard", "Anthony Davis"},
    3: {"Devin Booker", "Stephen Curry", "LeBron James", "Tyrese Haliburton", "Domantas Sabonis"},
}
ALL_DEFENSE = {
    1: {"Bam Adebayo", "Anthony Davis", "Rudy Gobert", "Herbert Jones", "Victor Wembanyama"},
    2: {"Alex Caruso", "Jrue Holiday", "Jaden McDaniels", "Jalen Suggs", "Derrick White"},
}
MVP = "Nikola Jokić"
DPOY = "Rudy Gobert"
ROY = "Victor Wembanyama"
CHAMPION = "BOS"

# The historical roster endpoint reflects the end-of-season roster. Players
# traded or waived before then need their number on the specific former team.
# These explicit overrides make that limitation visible and reviewable.
JERSEY_OVERRIDES = {
    ("ATL", 201988): 8,
    ("BKN", 1626220): 00, ("BKN", 203915): 26,
    ("CHA", 202330): 20, ("CHA", 202397): 14, ("CHA", 1641877): 31,
    ("CHA", 1629023): 25, ("CHA", 1626179): 3,
    ("DAL", 1629684): 3, ("DAL", 1626158): 20, ("DAL", 203552): 30,
    ("DET", 202692): 14, ("DET", 202711): 44, ("DET", 1630587): 12,
    ("DET", 203925): 31, ("DET", 1628995): 24, ("DET", 1630165): 7,
    ("DET", 1628963): 35, ("GSW", 202709): 1,
    ("IND", 1628971): 11, ("IND", 1627741): 7, ("IND", 1629670): 13,
    ("MEM", 202687): 18, ("MEM", 1631223): 21, ("MEM", 1631367): 0,
    ("MEM", 1630214): 2, ("MIA", 200768): 7, ("MIL", 1626166): 15,
    ("MIN", 1629003): 18, ("MIN", 1628972): 23,
    ("NYK", 1630193): 5, ("NYK", 1629656): 6, ("NYK", 1629628): 9,
    ("NYK", 201959): 67, ("OKC", 203995): 29,
    ("PHI", 1627863): 25, ("PHI", 1630531): 11, ("PHI", 202694): 5,
    ("PHI", 201976): 22, ("PHX", 1629002): 4, ("PHX", 1630692): 0,
    ("PHX", 1628966): 21, ("PHX", 1629139): 18, ("POR", 1630219): 5,
    ("SAS", 203926): 17, ("TOR", 203471): 17, ("TOR", 1629007): 34,
    ("TOR", 1630201): 22, ("TOR", 1628384): 3, ("TOR", 203490): 32,
    ("TOR", 1627783): 43, ("TOR", 1630173): 5, ("TOR", 201152): 21,
    ("UTA", 203482): 41, ("UTA", 1630534): 30, ("UTA", 1631323): 16,
    ("WAS", 1629655): 21, ("WAS", 201568): 88, ("WAS", 1626153): 55,
    ("WAS", 203488): 35,
}

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nba.com/"}


def nba_get(endpoint: str, params: dict, retries: int = 4) -> dict:
    url = f"https://stats.nba.com/stats/{endpoint}?{urlencode(params)}"
    error = None
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=45) as response:
                return json.loads(response.read())
        except Exception as exc:  # network retries are intentionally broad
            error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"NBA Stats request failed: {endpoint} {params}") from error


def fetch_team(abbr: str, team_id: int) -> tuple[str, dict, dict]:
    stats_path = RAW / f"{abbr}_stats.json"
    roster_path = RAW / f"{abbr}_roster.json"
    if stats_path.exists() and roster_path.exists():
        return (
            abbr,
            json.loads(stats_path.read_text(encoding="utf-8")),
            json.loads(roster_path.read_text(encoding="utf-8")),
        )
    stats = nba_get("leaguedashplayerstats", {
        "College": "", "Conference": "", "Country": "", "DateFrom": "", "DateTo": "",
        "Division": "", "DraftPick": "", "DraftYear": "", "GameScope": "",
        "GameSegment": "", "Height": "", "LastNGames": 0, "LeagueID": "00",
        "Location": "", "MeasureType": "Base", "Month": 0, "OpponentTeamID": 0,
        "Outcome": "", "PORound": 0, "PaceAdjust": "N", "PerMode": "PerGame",
        "Period": 0, "PlayerExperience": "", "PlayerPosition": "", "PlusMinus": "N",
        "Rank": "N", "Season": SEASON, "SeasonSegment": "", "SeasonType": "Regular Season",
        "ShotClockRange": "", "StarterBench": "", "TeamID": team_id,
        "VsConference": "", "VsDivision": "", "Weight": "",
    })
    roster = nba_get("commonteamroster", {"LeagueID": "00", "Season": SEASON, "TeamID": team_id})
    return abbr, stats, roster


def result_rows(payload: dict, name: str) -> list[dict]:
    result = next(x for x in payload["resultSets"] if x["name"] == name)
    return [dict(zip(result["headers"], row)) for row in result["rowSet"]]


def award_team(name: str, mapping: dict[int, set[str]]) -> int | None:
    return next((team for team, names in mapping.items() if name in names), None)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    GAME.mkdir(parents=True, exist_ok=True)

    payloads = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch_team, abbr, team_id): abbr for abbr, team_id in TEAMS.items()}
        for future in as_completed(futures):
            abbr, stats, roster = future.result()
            payloads[abbr] = (stats, roster)
            (RAW / f"{abbr}_stats.json").write_text(json.dumps(stats), encoding="utf-8")
            (RAW / f"{abbr}_roster.json").write_text(json.dumps(roster), encoding="utf-8")
            print(f"Fetched {abbr}")

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
            jersey_raw = jersey_by_id.get(player_id, JERSEY_OVERRIDES.get((abbr, player_id)))
            record = {
                "season": SEASON,
                "player_id": player_id,
                "player": name,
                "team": abbr,
                "gp": int(row["GP"]),
                "mpg": round(float(row["MIN"]), 1),
                "ppg": round(float(row["PTS"]), 1),
                "rpg": round(float(row["REB"]), 1),
                "apg": round(float(row["AST"]), 1),
                "spg": round(float(row["STL"]), 1),
                "bpg": round(float(row["BLK"]), 1),
                "jersey": int(jersey_raw) if jersey_raw is not None and str(jersey_raw).isdigit() else None,
                "all_nba": award_team(name, ALL_NBA),
                "all_defense": award_team(name, ALL_DEFENSE),
                "champion": abbr == CHAMPION,
                "mvp": name == MVP,
                "dpoy": name == DPOY,
                "roy": name == ROY,
            }
            records.append(record)

    records.sort(key=lambda x: (x["team"], x["player"]))
    fields = list(records[0])
    csv_path = PROCESSED / "nba_roulette_2023_24.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    json_path = GAME / "players_2023_24.json"
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    missing = [r for r in records if r["jersey"] is None]
    summary = {
        "season": SEASON,
        "eligibility": {"minimum_team_gp": 15, "minimum_team_mpg": 10.0},
        "eligible_player_team_records": len(records),
        "eligible_records_by_team": {team: sum(r["team"] == team for r in records) for team in TEAMS},
        "missing_jersey_records": len(missing),
        "missing_jerseys": [{"team": r["team"], "player": r["player"], "player_id": r["player_id"]} for r in missing],
        "all_nba_records": sum(r["all_nba"] is not None for r in records),
        "all_defense_records": sum(r["all_defense"] is not None for r in records),
        "champion_records": sum(r["champion"] for r in records),
        "major_award_records": sum(r["mvp"] or r["dpoy"] or r["roy"] for r in records),
    }
    (PROCESSED / "nba_roulette_2023_24_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
