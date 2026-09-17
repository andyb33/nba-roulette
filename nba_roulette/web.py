"""Serialization and commands for the dependency-free browser prototype."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .game import GameState, MAX_SPINS_PER_TURN
from .models import Lock, PlayerTeamSeason
from .roulette import RouletteEngine
from .scoring import Category, UPPER_BONUS_THRESHOLD, UPPER_CATEGORIES


CATEGORY_LABELS = {
    Category.POINTS: "Points",
    Category.REBOUNDS: "Rebounds",
    Category.ASSISTS: "Assists",
    Category.STEALS: "Steals",
    Category.BLOCKS: "Blocks",
    Category.GAMES_PLAYED: "Games Played",
    Category.ALL_NBA_THIRD: "All-NBA Third",
    Category.ALL_NBA_SECOND: "All-NBA Second",
    Category.ALL_NBA_FIRST: "All-NBA First",
    Category.CHAMPION: "Champion",
    Category.ALL_DEFENSE_SECOND: "All-Defense Second",
    Category.ALL_DEFENSE_FIRST: "All-Defense First",
    Category.MAJOR_AWARD: "Major Award",
    Category.JERSEY: "Jersey Number",
}


@dataclass(slots=True)
class BrowserGame:
    records: tuple[PlayerTeamSeason, ...]
    seed: int | None = None
    game: GameState = field(init=False)

    def __post_init__(self) -> None:
        self.game = GameState(RouletteEngine(self.records, random.Random(self.seed)))

    def spin(self, keeps: list[str] | None = None) -> dict:
        if self.game.is_complete:
            raise ValueError("The game is complete")
        if self.game.turn is None:
            self.game.start_turn()
        else:
            try:
                locks = tuple(Lock(value) for value in (keeps or []))
            except ValueError as error:
                raise ValueError("Unknown Keep selection") from error
            self.game.reroll(locks)
        return self.state()

    def score(self, category_name: str) -> dict:
        if self.game.turn is None:
            raise ValueError("Spin before choosing a category")
        try:
            category = Category(category_name)
        except ValueError as error:
            raise ValueError("Unknown score category") from error
        self.game.score(category)
        return self.state()

    def state(self) -> dict:
        turn = self.game.turn
        upper_total = sum(
            self.game.scorecard.get(category, 0) for category in UPPER_CATEGORIES
        )
        scored = {
            category.value: {
                "score": score,
                "player": self.game.scored_records[category].player,
                "season": self.game.scored_records[category].season,
                "team": self.game.scored_records[category].team,
            }
            for category, score in self.game.scorecard.items()
        }
        preview = self.game.preview() if turn else {}
        return {
            "turn": self.game.turns_completed + (0 if self.game.is_complete else 1),
            "turns_total": len(Category),
            "complete": self.game.is_complete,
            "total_score": self.game.total_score,
            "upper_total": upper_total,
            "upper_target": UPPER_BONUS_THRESHOLD,
            "bonus": self.game.bonus,
            "spins_used": turn.spins_used if turn else 0,
            "spins_total": MAX_SPINS_PER_TURN,
            "rerolls_left": MAX_SPINS_PER_TURN - turn.spins_used if turn else 0,
            "player": self._player(turn.current) if turn else None,
            "categories": [
                {
                    "id": category.value,
                    "label": CATEGORY_LABELS[category],
                    "section": self._section(category),
                    "used": category in self.game.scorecard,
                    "score": scored.get(category.value, {}).get("score"),
                    "preview": preview.get(category),
                    "selection": scored.get(category.value),
                }
                for category in Category
            ],
        }

    @staticmethod
    def _section(category: Category) -> str:
        if category in UPPER_CATEGORIES or category == Category.GAMES_PLAYED:
            return "Stats"
        if category == Category.JERSEY:
            return "Joker"
        return "Accolades"

    @staticmethod
    def _player(record: PlayerTeamSeason) -> dict:
        awards = []
        if record.all_nba:
            awards.append(f"All-NBA {record.all_nba}")
        if record.all_defense:
            awards.append(f"All-Defense {record.all_defense}")
        if record.champion:
            awards.append("Champion")
        if record.mvp:
            awards.append("MVP")
        if record.dpoy:
            awards.append("DPOY")
        if record.roy:
            awards.append("ROTY")
        return {
            "season": record.season,
            "team": record.team,
            "player_id": record.player_id,
            "name": record.player,
            "jersey": record.jersey,
            "stats": {
                "PPG": record.ppg,
                "RPG": record.rpg,
                "APG": record.apg,
                "SPG": record.spg,
                "BPG": record.bpg,
                "GP": record.gp,
            },
            "awards": awards,
        }
