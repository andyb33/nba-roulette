"""NBA Roulette scorecard categories and deterministic score calculations."""

from __future__ import annotations

import math
from enum import Enum

from .models import PlayerTeamSeason


class Category(str, Enum):
    POINTS = "points"
    REBOUNDS = "rebounds"
    ASSISTS = "assists"
    STEALS = "steals"
    BLOCKS = "blocks"
    GAMES_PLAYED = "games_played"
    ALL_NBA_THIRD = "all_nba_third"
    ALL_NBA_SECOND = "all_nba_second"
    ALL_NBA_FIRST = "all_nba_first"
    CHAMPION = "champion"
    ALL_DEFENSE_SECOND = "all_defense_second"
    ALL_DEFENSE_FIRST = "all_defense_first"
    MAJOR_AWARD = "major_award"
    JERSEY = "jersey"


UPPER_CATEGORIES = (
    Category.POINTS, Category.REBOUNDS, Category.ASSISTS,
    Category.STEALS, Category.BLOCKS,
)
UPPER_BONUS_THRESHOLD = 120
UPPER_BONUS_SCORE = 35


def round_half_up(value: float) -> int:
    if value < 0:
        raise ValueError("Scores cannot be negative")
    return math.floor(value + 0.5)


def category_score(record: PlayerTeamSeason, category: Category) -> int:
    scorers = {
        Category.POINTS: lambda: round_half_up(record.ppg * 2),
        Category.REBOUNDS: lambda: round_half_up(record.rpg * 3),
        Category.ASSISTS: lambda: round_half_up(record.apg * 3),
        Category.STEALS: lambda: round_half_up(record.spg * 10),
        Category.BLOCKS: lambda: round_half_up(record.bpg * 10),
        Category.GAMES_PLAYED: lambda: record.gp,
        Category.ALL_NBA_THIRD: lambda: 20 if record.all_nba in (1, 2, 3) else 0,
        Category.ALL_NBA_SECOND: lambda: 30 if record.all_nba in (1, 2) else 0,
        Category.ALL_NBA_FIRST: lambda: 40 if record.all_nba == 1 else 0,
        Category.CHAMPION: lambda: 25 if record.champion else 0,
        Category.ALL_DEFENSE_SECOND: lambda: 30 if record.all_defense in (1, 2) else 0,
        Category.ALL_DEFENSE_FIRST: lambda: 40 if record.all_defense == 1 else 0,
        Category.MAJOR_AWARD: lambda: 50 if record.major_award else 0,
        Category.JERSEY: lambda: record.jersey,
    }
    return scorers[category]()


def score_preview(record: PlayerTeamSeason) -> dict[Category, int]:
    return {category: category_score(record, category) for category in Category}


def upper_bonus(scorecard: dict[Category, int]) -> int:
    if not all(category in scorecard for category in UPPER_CATEGORIES):
        return 0
    total = sum(scorecard[category] for category in UPPER_CATEGORIES)
    return UPPER_BONUS_SCORE if total >= UPPER_BONUS_THRESHOLD else 0
