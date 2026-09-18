"""Serialization and commands for the dependency-free browser prototype."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .game import GameState, MAX_SPINS_PER_TURN
from .models import Lock, PlayerTeamSeason
from .playtest import PlaytestBatchLogger
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

CATEGORY_META = {
    Category.POINTS: {"formula": "×2", "glow_threshold": 40},
    Category.REBOUNDS: {"formula": "×3", "glow_threshold": 30},
    Category.ASSISTS: {"formula": "×3", "glow_threshold": 30},
    Category.STEALS: {"formula": "×10", "glow_threshold": 20},
    Category.BLOCKS: {"formula": "×10", "glow_threshold": 20},
    Category.GAMES_PLAYED: {"formula": "×1", "glow_threshold": 80},
    Category.ALL_NBA_THIRD: {"fixed_value": 20, "icon": "🥉"},
    Category.ALL_NBA_SECOND: {"fixed_value": 30, "icon": "🥈"},
    Category.ALL_NBA_FIRST: {"fixed_value": 40, "icon": "🥇"},
    Category.CHAMPION: {"fixed_value": 25, "icon": "🏆"},
    Category.ALL_DEFENSE_SECOND: {"fixed_value": 30, "icon": "🛡️"},
    Category.ALL_DEFENSE_FIRST: {"fixed_value": 40, "icon": "🛡️"},
    Category.MAJOR_AWARD: {"fixed_value": 50, "icon": "⭐"},
    Category.JERSEY: {"formula": "×1", "glow_threshold": 70},
}

TEAM_COLORS = {
    "ATL": ("#E03A3E", "#C1D32F"), "BOS": ("#007A33", "#BA9653"),
    "BKN": ("#000000", "#FFFFFF"), "CHA": ("#1D1160", "#00788C"),
    "CHI": ("#CE1141", "#000000"), "CLE": ("#860038", "#FDBB30"),
    "DAL": ("#00538C", "#B8C4CA"), "DEN": ("#0E2240", "#FEC524"),
    "DET": ("#C8102E", "#1D42BA"), "GSW": ("#1D428A", "#FFC72C"),
    "HOU": ("#CE1141", "#000000"), "IND": ("#002D62", "#FDBB30"),
    "LAC": ("#C8102E", "#1D428A"), "LAL": ("#552583", "#FDB927"),
    "MEM": ("#5D76A9", "#12173F"), "MIA": ("#98002E", "#F9A01B"),
    "MIL": ("#00471B", "#EEE1C6"), "MIN": ("#0C2340", "#78BE20"),
    "NOP": ("#0C2340", "#C8102E"), "NYK": ("#006BB6", "#F58426"),
    "OKC": ("#007AC1", "#EF3B24"), "ORL": ("#0077C0", "#C4CED4"),
    "PHI": ("#006BB6", "#ED174C"), "PHX": ("#1D1160", "#E56020"),
    "POR": ("#E03A3E", "#000000"), "SAC": ("#5A2D81", "#63727A"),
    "SAS": ("#C4CED4", "#000000"), "TOR": ("#CE1141", "#000000"),
    "UTA": ("#002B5C", "#6CACE4"), "WAS": ("#002B5C", "#E31837"),
}

AWARD_META = {
    "Champion": "🏆", "MVP": "⭐", "DPOY": "🛡️", "ROTY": "🌟",
    "All-NBA First": "🥇", "All-NBA Second": "🥈", "All-NBA Third": "🥉",
    "All-Defense First": "🛡️", "All-Defense Second": "🛡️",
}


@dataclass(slots=True)
class BrowserGame:
    records: tuple[PlayerTeamSeason, ...]
    seed: int | None = None
    logger: PlaytestBatchLogger | None = None
    game: GameState = field(init=False)
    game_id: str = field(init=False)
    started_at: str = field(init=False)
    events: list[dict[str, Any]] = field(init=False, default_factory=list)
    saved_batch_game: int | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.game = GameState(RouletteEngine(self.records, random.Random(self.seed)))
        self.game_id = uuid.uuid4().hex
        self.started_at = datetime.now(timezone.utc).isoformat()

    def spin(self, keeps: list[str] | None = None) -> dict:
        if self.game.is_complete:
            raise ValueError("The game is complete")
        if self.game.turn is None:
            self.game.start_turn()
            selected_keeps: list[str] = []
        else:
            try:
                locks = tuple(Lock(value) for value in (keeps or []))
            except ValueError as error:
                raise ValueError("Unknown Keep selection") from error
            self.game.reroll(locks)
            selected_keeps = [lock.value for lock in locks]
        turn = self.game.turn
        self.events.append({
            "event": "spin",
            "turn": self.game.turns_completed + 1,
            "spin": turn.spins_used,
            "keeps": selected_keeps,
            "result": self._record_identity(turn.current),
        })
        return self.state()

    def score(self, category_name: str) -> dict:
        if self.game.turn is None:
            raise ValueError("Spin before choosing a category")
        try:
            category = Category(category_name)
        except ValueError as error:
            raise ValueError("Unknown score category") from error
        current = self.game.turn.current
        spins_used = self.game.turn.spins_used
        value = self.game.score(category)
        self.events.append({
            "event": "score",
            "turn": self.game.turns_completed,
            "category": category.value,
            "score": value,
            "spins_used": spins_used,
            "result": self._record_identity(current),
        })
        if self.game.is_complete and self.logger and self.saved_batch_game is None:
            self.saved_batch_game = self.logger.save(self._playtest_record())
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
            "playtest": self._playtest_status(),
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
                    **CATEGORY_META[category],
                }
                for category in Category
            ],
        }

    def _playtest_status(self) -> dict | None:
        if not self.logger:
            return None
        completed = self.logger.completed_count()
        return {
            "batch_id": self.logger.batch_id,
            "batch_name": self.logger.batch_name,
            "target": self.logger.target,
            "completed": completed,
            "saved_batch_game": self.saved_batch_game,
            "full": completed >= self.logger.target,
        }

    def _playtest_record(self) -> dict:
        spin_events = [event for event in self.events if event["event"] == "spin"]
        player_ids = [event["result"]["player_id"] for event in spin_events]
        accolade_categories = {
            Category.ALL_NBA_THIRD, Category.ALL_NBA_SECOND, Category.ALL_NBA_FIRST,
            Category.CHAMPION, Category.ALL_DEFENSE_SECOND,
            Category.ALL_DEFENSE_FIRST, Category.MAJOR_AWARD,
        }
        upper_score = sum(self.game.scorecard.get(category, 0) for category in UPPER_CATEGORIES)
        categories = {
            category.value: {
                "score": self.game.scorecard[category],
                **self._record_identity(self.game.scored_records[category]),
            }
            for category in Category
        }
        return {
            "game_id": self.game_id,
            "started_at": self.started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "final_score": self.game.total_score,
            "upper_score": upper_score,
            "bonus": self.game.bonus,
            "zero_accolades": sum(
                self.game.scorecard[category] == 0 for category in accolade_categories
            ),
            "spins_seen": len(spin_events),
            "rerolls_used": len(spin_events) - len(Category),
            "keep_uses": sum(bool(event["keeps"]) for event in spin_events),
            "unique_players_seen": len(set(player_ids)),
            "repeated_player_appearances": len(player_ids) - len(set(player_ids)),
            "categories": categories,
            "events": self.events,
        }

    @staticmethod
    def _record_identity(record: PlayerTeamSeason) -> dict:
        return {
            "season": record.season,
            "team": record.team,
            "player_id": record.player_id,
            "player": record.player,
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
        awards: list[dict[str, str]] = []
        if record.all_nba:
            label = {1: "All-NBA First", 2: "All-NBA Second", 3: "All-NBA Third"}[record.all_nba]
            awards.append({"label": label, "icon": AWARD_META[label]})
        if record.all_defense:
            label = {1: "All-Defense First", 2: "All-Defense Second"}[record.all_defense]
            awards.append({"label": label, "icon": AWARD_META[label]})
        if record.champion:
            awards.append({"label": "Champion", "icon": AWARD_META["Champion"]})
        if record.mvp:
            awards.append({"label": "MVP", "icon": AWARD_META["MVP"]})
        if record.dpoy:
            awards.append({"label": "DPOY", "icon": AWARD_META["DPOY"]})
        if record.roy:
            awards.append({"label": "ROTY", "icon": AWARD_META["ROTY"]})
        primary, secondary = TEAM_COLORS.get(record.team, ("#4D7CFF", "#FFFFFF"))
        return {
            "season": record.season,
            "team": record.team,
            "player_id": record.player_id,
            "name": record.player,
            "jersey": record.jersey,
            "team_colors": {"primary": primary, "secondary": secondary},
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
