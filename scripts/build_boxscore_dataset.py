#!/usr/bin/env python3
"""Build a season from game-level NBA box scores and Basketball Reference jerseys."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from season_config import SEASON_CONFIGS

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
GAME = ROOT / "data" / "game"

TEAM_IDS = {
    1610612737: "ATL", 1610612738: "BOS", 1610612739: "CLE",
    1610612740: "NOP", 1610612741: "CHI", 1610612742: "DAL",
    1610612743: "DEN", 1610612744: "GSW", 1610612745: "HOU",
    1610612746: "LAC", 1610612747: "LAL", 1610612748: "MIA",
    1610612749: "MIL", 1610612750: "MIN", 1610612751: "BKN",
    1610612752: "NYK", 1610612753: "ORL", 1610612754: "IND",
    1610612755: "PHI", 1610612756: "PHX", 1610612757: "POR",
    1610612758: "SAC", 1610612759: "SAS", 1610612760: "OKC",
    1610612761: "TOR", 1610612762: "UTA", 1610612763: "MEM",
    1610612764: "WAS", 1610612765: "DET", 1610612766: "CHA",
}
BREF_CODES = {"BKN": "BRK", "CHA": "CHO", "PHX": "PHO"}


def name_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"\b(jr|sr|ii|iii|iv)\.?$", "", value.strip(), flags=re.IGNORECASE)
    key = re.sub(r"[^a-z0-9]", "", value.lower())
    return {"ronaldholland": "ronholland"}.get(key, key)


def minutes_to_seconds(value: str) -> int:
    minutes, seconds = value.split(":")
    return int(minutes) * 60 + int(seconds)


def last_number(value: object) -> int | None:
    if pd.isna(value):
        return None
    matches = re.findall(r"\d+", str(value))
    return int(matches[-1]) if matches else None


def award_team(name: str, mapping: dict[int, set[str]]) -> int | None:
    key = name_key(name)
    return next((team for team, names in mapping.items() if key in {name_key(n) for n in names}), None)


def load_jerseys(raw_dir: Path) -> tuple[dict[tuple[str, str], int], list[dict]]:
    jerseys: dict[tuple[str, str], int] = {}
    audit: list[dict] = []
    for team in TEAM_IDS.values():
        bref = BREF_CODES.get(team, team)
        html = raw_dir / "bref" / f"{bref}.html"
        if not html.exists():
            raise FileNotFoundError(f"Missing Basketball Reference page: {html}")
        roster = pd.read_html(html)[0]
        for row in roster.to_dict("records"):
            number = last_number(row.get("No."))
            if number is None:
                continue
            player = str(row["Player"])
            jerseys[(team, name_key(player))] = number
            audit.append({
                "team": team,
                "player": player,
                "listed_numbers": row.get("No."),
                "verified_final_jersey": number,
                "source": f"https://www.basketball-reference.com/teams/{bref}/2026.html",
                "status": "VERIFIED",
            })
    return jerseys, audit


def validate_against_team_tables(raw_dir: Path, records: list[dict]) -> None:
    columns = {"gp": "G", "mpg": "MP", "ppg": "PTS", "rpg": "TRB", "apg": "AST", "spg": "STL", "bpg": "BLK"}
    errors = []
    for team in TEAM_IDS.values():
        bref = BREF_CODES.get(team, team)
        table = pd.read_html(raw_dir / "bref" / f"{bref}.html")[1]
        table = table[table["Player"] != "Team Totals"].copy()
        table["name_key"] = table["Player"].map(name_key)
        for record in (row for row in records if row["team"] == team):
            match = table[table["name_key"] == name_key(record["player"])]
            if len(match) != 1:
                errors.append(f"{team} {record['player']}: found {len(match)} team-table rows")
                continue
            row = match.iloc[0]
            for field, source_field in columns.items():
                if abs(float(record[field]) - float(row[source_field])) > 0.11:
                    errors.append(
                        f"{team} {record['player']} {field}: "
                        f"boxscore={record[field]} table={row[source_field]}"
                    )
    if errors:
        raise ValueError("Team-table validation failed:\n" + "\n".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", required=True, choices=sorted(SEASON_CONFIGS))
    parser.add_argument("--boxscores", type=Path, required=True)
    args = parser.parse_args()
    season = args.season
    if season != "2025-26":
        raise SystemExit("The mirrored box-score importer is currently verified for 2025-26 only")

    raw_dir = ROOT / "data" / "raw" / season
    config = SEASON_CONFIGS[season]
    box = pd.read_csv(args.boxscores, dtype={"game_id": str})
    box["game_id"] = box["game_id"].str.zfill(10)
    box = box[box["game_id"].str.startswith("002") & box["minutes"].notna()].copy()
    box["seconds"] = box["minutes"].map(minutes_to_seconds)
    grouped = box.groupby(
        ["team_id", "team_tricode", "person_id", "first_name", "family_name"],
        as_index=False,
    ).agg(
        gp=("game_id", "nunique"), seconds=("seconds", "sum"),
        pts=("points", "sum"), reb=("rebounds_total", "sum"),
        ast=("assists", "sum"), stl=("steals", "sum"), blk=("blocks", "sum"),
    )

    jerseys, jersey_audit = load_jerseys(raw_dir)
    records = []
    missing = []
    for row in grouped.to_dict("records"):
        gp = int(row["gp"])
        mpg = row["seconds"] / 60 / gp
        if gp < 15 or mpg < 10.0:
            continue
        team = TEAM_IDS[int(row["team_id"])]
        if team != row["team_tricode"]:
            raise ValueError(f"Team mismatch: {team} != {row['team_tricode']}")
        player = f"{row['first_name']} {row['family_name']}"
        jersey = jerseys.get((team, name_key(player)))
        if jersey is None:
            missing.append({"team": team, "player_id": int(row["person_id"]), "player": player})
        records.append({
            "season": season, "player_id": int(row["person_id"]), "player": player,
            "team": team, "gp": gp, "mpg": round(mpg, 1),
            "ppg": round(row["pts"] / gp, 1), "rpg": round(row["reb"] / gp, 1),
            "apg": round(row["ast"] / gp, 1), "spg": round(row["stl"] / gp, 1),
            "bpg": round(row["blk"] / gp, 1), "jersey": jersey,
            "all_nba": award_team(player, config["all_nba"]),
            "all_defense": award_team(player, config["all_defense"]),
            "champion": team == config["champion"],
            "mvp": name_key(player) == name_key(config["mvp"]),
            "dpoy": name_key(player) == name_key(config["dpoy"]),
            "roy": name_key(player) == name_key(config["roy"]),
        })

    records.sort(key=lambda row: (row["team"], row["player"]))
    validate_against_team_tables(raw_dir, records)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    GAME.mkdir(parents=True, exist_ok=True)
    slug = season.replace("-", "_")
    fields = list(records[0])
    with (PROCESSED / f"nba_roulette_{slug}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    (GAME / f"players_{slug}.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    audit_by_key = {(row["team"], name_key(row["player"])): row for row in jersey_audit}
    eligible_audit = []
    for record in records:
        audit_row = dict(audit_by_key[(record["team"], name_key(record["player"]))])
        audit_row["player_id"] = record["player_id"]
        audit_row["player"] = record["player"]
        eligible_audit.append(audit_row)
    audit_fields = ["team", "player_id", "player", "listed_numbers", "verified_final_jersey", "source", "status"]
    with (PROCESSED / f"jersey_verification_{slug}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=audit_fields)
        writer.writeheader()
        writer.writerows(sorted(eligible_audit, key=lambda row: (row["team"], row["player"])))

    summary = {
        "season": season,
        "eligibility": {"minimum_team_gp": 15, "minimum_team_mpg": 10.0},
        "source_regular_season_games": int(box["game_id"].nunique()),
        "eligible_player_team_records": len(records),
        "eligible_records_by_team": {
            team: sum(row["team"] == team for row in records) for team in TEAM_IDS.values()
        },
        "missing_jersey_records": len(missing),
        "jersey_records_verified": len(eligible_audit),
        "team_table_records_verified": len(records),
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
        print(json.dumps(missing, ensure_ascii=False, indent=2))
        raise SystemExit(f"Validation failed: {len(missing)} missing jerseys")


if __name__ == "__main__":
    main()
