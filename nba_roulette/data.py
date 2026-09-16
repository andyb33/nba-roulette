"""Load validated player-team-season records for the game engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import PlayerTeamSeason


ROOT = Path(__file__).resolve().parent.parent


def load_records(
    seasons: Iterable[str] = ("2023-24", "2024-25"),
    data_dir: Path | None = None,
) -> tuple[PlayerTeamSeason, ...]:
    directory = data_dir or ROOT / "data" / "game"
    records: list[PlayerTeamSeason] = []
    for season in seasons:
        path = directory / f"players_{season.replace('-', '_')}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing game dataset: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.extend(PlayerTeamSeason.from_dict(row) for row in payload)
    if not records:
        raise ValueError("The roulette pool cannot be empty")
    keys = {(row.season, row.team, row.player_id) for row in records}
    if len(keys) != len(records):
        raise ValueError("Duplicate season/team/player records found")
    return tuple(records)
