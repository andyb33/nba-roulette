#!/usr/bin/env python3
"""Empirically verify roulette weighting and lock validity on production data."""

from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nba_roulette.data import load_records
from nba_roulette.models import Lock
from nba_roulette.roulette import RouletteEngine


OUTPUT = ROOT / "analysis" / "engine_verification.json"
SEED = 20260916


def max_deviation(counts: Counter, expected_probability: float, total: int) -> float:
    return max(abs(count / total - expected_probability) for count in counts.values())


def main() -> None:
    records = load_records()
    engine = RouletteEngine(records, random.Random(SEED))

    standard_samples = 120_000
    standard = [engine.spin() for _ in range(standard_samples)]
    seasons = sorted({row.season for row in records})
    teams = sorted({row.team for row in records})
    season_counts = Counter(row.season for row in standard)
    season_deviation = max_deviation(season_counts, 1 / len(seasons), standard_samples)

    team_deviations = {}
    for season in seasons:
        subset = [row for row in standard if row.season == season]
        counts = Counter(row.team for row in subset)
        team_deviations[season] = max_deviation(counts, 1 / len(teams), len(subset))

    by_team_season: dict[tuple[str, str], list] = defaultdict(list)
    by_player: dict[int, list] = defaultdict(list)
    for row in records:
        by_team_season[(row.season, row.team)].append(row)
        by_player[row.player_id].append(row)

    target_key, target_pool = max(by_team_season.items(), key=lambda item: len(item[1]))
    current = target_pool[0]
    player_samples = 60_000
    locked_pool = [
        engine.spin(current, {Lock.SEASON, Lock.TEAM}) for _ in range(player_samples)
    ]
    player_counts = Counter(row.player_id for row in locked_pool)
    player_deviation = max_deviation(player_counts, 1 / len(target_pool), player_samples)

    multi_season_players = [rows for rows in by_player.values() if len({row.season for row in rows}) > 1]
    traded_rows = max(multi_season_players, key=lambda rows: (len(rows), len({row.team for row in rows})))
    traded_current = traded_rows[0]
    traded_samples = 60_000
    player_locked = [engine.spin(traded_current, {Lock.PLAYER}) for _ in range(traded_samples)]
    valid_seasons = sorted({row.season for row in traded_rows})
    traded_season_counts = Counter(row.season for row in player_locked)
    traded_season_deviation = max_deviation(
        traded_season_counts, 1 / len(valid_seasons), traded_samples
    )
    traded_team_deviations = {}
    for season in valid_seasons:
        subset = [row for row in player_locked if row.season == season]
        valid_teams = {row.team for row in traded_rows if row.season == season}
        counts = Counter(row.team for row in subset)
        traded_team_deviations[season] = max_deviation(
            counts, 1 / len(valid_teams), len(subset)
        )

    lock_masks = (
        {Lock.SEASON}, {Lock.TEAM}, {Lock.PLAYER},
        {Lock.SEASON, Lock.TEAM}, {Lock.SEASON, Lock.PLAYER},
        {Lock.TEAM, Lock.PLAYER},
    )
    lock_checks = {}
    record_keys = {(row.season, row.team, row.player_id) for row in records}
    for mask in lock_masks:
        outcomes = [engine.spin(traded_current, mask) for _ in range(5_000)]
        valid = all(
            (row.season, row.team, row.player_id) in record_keys
            and (Lock.SEASON not in mask or row.season == traded_current.season)
            and (Lock.TEAM not in mask or row.team == traded_current.team)
            and (Lock.PLAYER not in mask or row.player_id == traded_current.player_id)
            for row in outcomes
        )
        lock_checks["+".join(sorted(lock.value for lock in mask))] = valid

    tolerances = {
        "season_absolute": 0.01,
        "team_absolute": 0.01,
        "player_absolute": 0.01,
        "locked_player_season_absolute": 0.01,
        "locked_player_team_absolute": 0.015,
    }
    checks = {
        "standard_season_weighting": season_deviation <= tolerances["season_absolute"],
        "standard_team_weighting": max(team_deviations.values()) <= tolerances["team_absolute"],
        "player_weighting_with_season_team_locked": player_deviation <= tolerances["player_absolute"],
        "locked_player_season_weighting": traded_season_deviation <= tolerances["locked_player_season_absolute"],
        "locked_player_team_weighting": max(traded_team_deviations.values()) <= tolerances["locked_player_team_absolute"],
        "all_lock_masks_valid": all(lock_checks.values()),
    }
    result = {
        "seed": SEED,
        "dataset_records": len(records),
        "sample_sizes": {
            "standard_spins": standard_samples,
            "season_team_locked_spins": player_samples,
            "player_locked_spins": traded_samples,
            "spins_per_lock_validity_check": 5_000,
        },
        "maximum_absolute_deviation": {
            "season": season_deviation,
            "team_by_season": team_deviations,
            "player_with_season_team_locked": player_deviation,
            "locked_player_season": traded_season_deviation,
            "locked_player_team_by_season": traded_team_deviations,
        },
        "fixtures": {
            "largest_team_season_pool": {
                "season": target_key[0], "team": target_key[1], "eligible_players": len(target_pool),
            },
            "multi_stint_player": {
                "player_id": traded_current.player_id,
                "player": traded_current.player,
                "eligible_records": len(traded_rows),
                "seasons": valid_seasons,
                "teams_by_season": {
                    season: sorted({row.team for row in traded_rows if row.season == season})
                    for season in valid_seasons
                },
            },
        },
        "lock_validity": lock_checks,
        "tolerances": tolerances,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit("Engine verification failed")


if __name__ == "__main__":
    main()
