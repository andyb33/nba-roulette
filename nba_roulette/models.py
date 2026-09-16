"""Shared models for the roulette and scoring engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Lock(str, Enum):
    SEASON = "season"
    TEAM = "team"
    PLAYER = "player"


@dataclass(frozen=True, slots=True)
class PlayerTeamSeason:
    season: str
    player_id: int
    player: str
    team: str
    gp: int
    mpg: float
    ppg: float
    rpg: float
    apg: float
    spg: float
    bpg: float
    jersey: int
    all_nba: int | None
    all_defense: int | None
    champion: bool
    mvp: bool
    dpoy: bool
    roy: bool

    @classmethod
    def from_dict(cls, row: dict) -> "PlayerTeamSeason":
        return cls(
            season=str(row["season"]),
            player_id=int(row["player_id"]),
            player=str(row["player"]),
            team=str(row["team"]),
            gp=int(row["gp"]),
            mpg=float(row["mpg"]),
            ppg=float(row["ppg"]),
            rpg=float(row["rpg"]),
            apg=float(row["apg"]),
            spg=float(row["spg"]),
            bpg=float(row["bpg"]),
            jersey=int(row["jersey"]),
            all_nba=int(row["all_nba"]) if row.get("all_nba") is not None else None,
            all_defense=int(row["all_defense"]) if row.get("all_defense") is not None else None,
            champion=bool(row["champion"]),
            mvp=bool(row["mvp"]),
            dpoy=bool(row["dpoy"]),
            roy=bool(row["roy"]),
        )

    @property
    def major_award(self) -> bool:
        return self.mvp or self.dpoy or self.roy
