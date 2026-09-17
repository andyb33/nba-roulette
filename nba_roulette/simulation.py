"""Reproducible full-game simulation policies and result collection."""

from __future__ import annotations

import random
from dataclasses import dataclass
from functools import lru_cache
from statistics import mean

from .game import GameState, MAX_SPINS_PER_TURN
from .models import PlayerTeamSeason
from .roulette import RouletteEngine
from .scoring import Category, category_score


@dataclass(frozen=True, slots=True)
class SimulatedGame:
    total_score: int
    bonus: int
    spins_used: int
    scorecard: dict[Category, int]


class RandomPolicy:
    """Choose a random legal spin count and a random open category."""

    name = "random"

    def play_turn(self, game: GameState, rng: random.Random) -> int:
        game.start_turn()
        target_spins = rng.randint(1, MAX_SPINS_PER_TURN)
        while game.turn is not None and game.turn.spins_used < target_spins:
            game.reroll()
        category = rng.choice(game.open_categories)
        spins_used = game.turn.spins_used
        game.score(category)
        return spins_used


class GreedyPolicy:
    """Maximize the current turn's score without locks or future-turn planning.

    The policy stops when the best current category score is at least the
    expected best score from one fresh unlocked spin. Otherwise it uses another
    unlocked reroll. Ties between categories follow scorecard order.
    """

    name = "greedy"

    def __init__(self, records: tuple[PlayerTeamSeason, ...]) -> None:
        self.weighted_records = _standard_spin_weights(records)

    @lru_cache(maxsize=None)
    def expected_best_score(self, open_categories: tuple[Category, ...]) -> float:
        return sum(
            weight * max(category_score(record, category) for category in open_categories)
            for record, weight in self.weighted_records
        )

    def play_turn(self, game: GameState, rng: random.Random) -> int:
        del rng  # Roulette randomness lives in the engine; tie-breaking is stable.
        game.start_turn()
        open_categories = game.open_categories
        while game.turn is not None:
            preview = game.preview()
            best_category = max(open_categories, key=lambda category: preview[category])
            best_score = preview[best_category]
            if (
                game.turn.spins_used == MAX_SPINS_PER_TURN
                or best_score >= self.expected_best_score(open_categories)
            ):
                spins_used = game.turn.spins_used
                game.score(best_category)
                return spins_used
            game.reroll()
        raise AssertionError("Turn unexpectedly ended without scoring")


def _standard_spin_weights(
    records: tuple[PlayerTeamSeason, ...],
) -> tuple[tuple[PlayerTeamSeason, float], ...]:
    seasons = sorted({record.season for record in records})
    teams_by_season = {
        season: sorted({record.team for record in records if record.season == season})
        for season in seasons
    }
    players_by_team = {
        (season, team): sum(
            record.season == season and record.team == team for record in records
        )
        for season in seasons
        for team in teams_by_season[season]
    }
    weighted = []
    for record in records:
        weight = (
            1 / len(seasons)
            / len(teams_by_season[record.season])
            / players_by_team[(record.season, record.team)]
        )
        weighted.append((record, weight))
    if abs(sum(weight for _, weight in weighted) - 1.0) > 1e-12:
        raise ValueError("Standard-spin weights do not sum to one")
    return tuple(weighted)


def simulate_game(
    records: tuple[PlayerTeamSeason, ...],
    policy: RandomPolicy | GreedyPolicy,
    seed: int,
) -> SimulatedGame:
    roulette_rng = random.Random(seed)
    policy_rng = random.Random(seed ^ 0x9E3779B9)
    game = GameState(RouletteEngine(records, roulette_rng))
    spins_used = 0
    while not game.is_complete:
        spins_used += policy.play_turn(game, policy_rng)
    return SimulatedGame(
        total_score=game.total_score,
        bonus=game.bonus,
        spins_used=spins_used,
        scorecard=dict(game.scorecard),
    )


def summarize_games(games: list[SimulatedGame]) -> dict:
    if not games:
        raise ValueError("At least one simulated game is required")
    totals = sorted(game.total_score for game in games)

    def percentile(probability: float) -> float:
        position = (len(totals) - 1) * probability
        lower = int(position)
        upper = min(lower + 1, len(totals) - 1)
        fraction = position - lower
        return totals[lower] * (1 - fraction) + totals[upper] * fraction

    return {
        "games": len(games),
        "total_score": {
            "mean": mean(totals),
            "p10": percentile(0.10),
            "median": percentile(0.50),
            "p90": percentile(0.90),
            "min": totals[0],
            "max": totals[-1],
        },
        "upper_bonus_rate": mean(game.bonus > 0 for game in games),
        "average_spins_per_game": mean(game.spins_used for game in games),
        "average_spins_per_turn": mean(game.spins_used for game in games) / len(Category),
        "categories": {
            category.value: {
                "mean": mean(game.scorecard[category] for game in games),
                "zero_rate": mean(game.scorecard[category] == 0 for game in games),
            }
            for category in Category
        },
    }
