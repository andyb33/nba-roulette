"""Turn and scorecard state for a complete NBA Roulette game."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .models import Lock, PlayerTeamSeason
from .roulette import RouletteEngine
from .scoring import Category, category_score, score_preview, upper_bonus


MAX_SPINS_PER_TURN = 3


@dataclass(slots=True)
class TurnState:
    current: PlayerTeamSeason
    spins_used: int = 1
    last_locks: frozenset[Lock] = field(default_factory=frozenset)


class GameState:
    def __init__(self, roulette: RouletteEngine) -> None:
        self.roulette = roulette
        self.scorecard: dict[Category, int] = {}
        self.turn: TurnState | None = None
        self.scored_records: dict[Category, PlayerTeamSeason] = {}

    @property
    def turns_completed(self) -> int:
        return len(self.scorecard)

    @property
    def is_complete(self) -> bool:
        return self.turns_completed == len(Category)

    @property
    def bonus(self) -> int:
        return upper_bonus(self.scorecard)

    @property
    def total_score(self) -> int:
        return sum(self.scorecard.values()) + self.bonus

    @property
    def open_categories(self) -> tuple[Category, ...]:
        return tuple(category for category in Category if category not in self.scorecard)

    def start_turn(self) -> PlayerTeamSeason:
        if self.is_complete:
            raise RuntimeError("The game is complete")
        if self.turn is not None:
            raise RuntimeError("A turn is already active")
        current = self.roulette.spin()
        self.turn = TurnState(current=current)
        return current

    def reroll(self, locks: Iterable[Lock] = ()) -> PlayerTeamSeason:
        if self.turn is None:
            raise RuntimeError("Start a turn before rerolling")
        if self.turn.spins_used >= MAX_SPINS_PER_TURN:
            raise RuntimeError("No rerolls remain this turn")
        lock_set = frozenset(locks)
        current = self.roulette.spin(self.turn.current, lock_set)
        self.turn.current = current
        self.turn.spins_used += 1
        self.turn.last_locks = lock_set
        return current

    def preview(self) -> dict[Category, int]:
        if self.turn is None:
            raise RuntimeError("No active turn")
        return {category: score for category, score in score_preview(self.turn.current).items()
                if category in self.open_categories}

    def score(self, category: Category) -> int:
        if self.turn is None:
            raise RuntimeError("No active turn")
        if category in self.scorecard:
            raise ValueError(f"Category already used: {category.value}")
        value = category_score(self.turn.current, category)
        self.scorecard[category] = value
        self.scored_records[category] = self.turn.current
        self.turn = None
        return value
