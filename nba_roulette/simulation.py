"""Reproducible full-game simulation policies and result collection."""

from __future__ import annotations

import random
from dataclasses import dataclass
from functools import lru_cache
from statistics import mean

from .game import GameState, MAX_SPINS_PER_TURN
from .models import Lock, PlayerTeamSeason
from .roulette import RouletteEngine
from .scoring import Category, UPPER_CATEGORIES, category_score


@dataclass(frozen=True, slots=True)
class SimulatedGame:
    total_score: int
    bonus: int
    spins_used: int
    scorecard: dict[Category, int]
    lock_counts: dict[str, int]
    upper_score: int


@dataclass(frozen=True, slots=True)
class SimulatedTurn:
    spins_used: int
    lock_counts: dict[str, int]


class RandomPolicy:
    """Choose a random legal spin count and a random open category."""

    name = "random"

    def play_turn(self, game: GameState, rng: random.Random) -> SimulatedTurn:
        game.start_turn()
        target_spins = rng.randint(1, MAX_SPINS_PER_TURN)
        while game.turn is not None and game.turn.spins_used < target_spins:
            game.reroll()
        category = rng.choice(game.open_categories)
        spins_used = game.turn.spins_used
        game.score(category)
        return SimulatedTurn(spins_used, {})


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

    def play_turn(self, game: GameState, rng: random.Random) -> SimulatedTurn:
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
                return SimulatedTurn(spins_used, {})
            game.reroll()
        raise AssertionError("Turn unexpectedly ended without scoring")


class StrategicPolicy:
    """A transparent lock-aware heuristic with category opportunity costs.

    This is not an optimal solver. It compares each result with the expected
    replacement value of every open category, gives upper-section selections a
    share of the possible bonus, and evaluates every legal lock mask using the
    roulette's exact hierarchical outcome probabilities.
    """

    name = "strategic"
    lock_options = (
        frozenset(),
        frozenset({Lock.SEASON}),
        frozenset({Lock.TEAM}),
        frozenset({Lock.PLAYER}),
        frozenset({Lock.SEASON, Lock.TEAM}),
        frozenset({Lock.SEASON, Lock.PLAYER}),
        frozenset({Lock.TEAM, Lock.PLAYER}),
    )
    upper_targets = {
        Category.POINTS: 40,
        Category.REBOUNDS: 30,
        Category.ASSISTS: 30,
        Category.STEALS: 20,
        Category.BLOCKS: 20,
    }

    def __init__(
        self,
        records: tuple[PlayerTeamSeason, ...],
        bonus_equity_per_category: float = 7.0,
        gap_aware_bonus: bool = False,
    ) -> None:
        self.records = records
        if bonus_equity_per_category < 0:
            raise ValueError("Bonus equity cannot be negative")
        self.bonus_equity_per_category = bonus_equity_per_category
        self.gap_aware_bonus = gap_aware_bonus
        self.standard_weights = _standard_spin_weights(records)
        self.replacement_values = {
            category: sum(
                weight * category_score(record, category)
                for record, weight in self.standard_weights
            )
            for category in Category
        }
        self._scores = {
            (record.season, record.team, record.player_id): {
                category: category_score(record, category) for category in Category
            }
            for record in records
        }
        self._outcome_cache: dict[
            tuple[str, str, int, frozenset[Lock]],
            tuple[tuple[PlayerTeamSeason, float], ...],
        ] = {}
        self._expectation_cache: dict[
            tuple[str, str, int, frozenset[Lock], tuple[Category, ...], int], float
        ] = {}
        self._best_choice_cache: dict[
            tuple[str, str, int, tuple[Category, ...], int], tuple[Category, float]
        ] = {}

    def _category_utility(
        self,
        record: PlayerTeamSeason,
        category: Category,
        upper_score_so_far: int,
        open_categories: tuple[Category, ...],
    ) -> float:
        score = self._scores[(record.season, record.team, record.player_id)][category]
        utility = score - self.replacement_values[category]
        if category in UPPER_CATEGORIES and upper_score_so_far < 140:
            if self.gap_aware_bonus:
                remaining_upper = tuple(
                    item for item in open_categories if item in UPPER_CATEGORIES
                )
                target = max(1.0, (140 - upper_score_so_far) / len(remaining_upper))
                cap = 1.5
            else:
                target = self.upper_targets[category]
                cap = 1.25
            utility += self.bonus_equity_per_category * min(score / target, cap)
        return utility

    def _best_choice(
        self,
        record: PlayerTeamSeason,
        open_categories: tuple[Category, ...],
        upper_score_so_far: int,
    ) -> tuple[Category, float]:
        key = (
            record.season, record.team, record.player_id,
            open_categories, upper_score_so_far,
        )
        if key not in self._best_choice_cache:
            category = max(
                open_categories,
                key=lambda item: self._category_utility(
                    record, item, upper_score_so_far, open_categories
                ),
            )
            self._best_choice_cache[key] = (
                category,
                self._category_utility(
                    record, category, upper_score_so_far, open_categories
                ),
            )
        return self._best_choice_cache[key]

    def _weighted_outcomes(
        self,
        current: PlayerTeamSeason,
        locks: frozenset[Lock],
    ) -> tuple[tuple[PlayerTeamSeason, float], ...]:
        key = (current.season, current.team, current.player_id, locks)
        if key not in self._outcome_cache:
            candidates = tuple(
                record for record in self.records
                if (Lock.SEASON not in locks or record.season == current.season)
                and (Lock.TEAM not in locks or record.team == current.team)
                and (Lock.PLAYER not in locks or record.player_id == current.player_id)
            )
            self._outcome_cache[key] = _hierarchical_weights(candidates, locks)
        return self._outcome_cache[key]

    def _expected_utility(
        self,
        current: PlayerTeamSeason,
        locks: frozenset[Lock],
        open_categories: tuple[Category, ...],
        upper_score_so_far: int,
    ) -> float:
        key = (
            current.season, current.team, current.player_id,
            locks, open_categories, upper_score_so_far,
        )
        if key not in self._expectation_cache:
            self._expectation_cache[key] = sum(
                weight * self._best_choice(
                    record, open_categories, upper_score_so_far
                )[1]
                for record, weight in self._weighted_outcomes(current, locks)
            )
        return self._expectation_cache[key]

    def play_turn(self, game: GameState, rng: random.Random) -> SimulatedTurn:
        del rng
        game.start_turn()
        used_locks: dict[str, int] = {}
        while game.turn is not None:
            open_categories = game.open_categories
            upper_score_so_far = sum(
                game.scorecard.get(category, 0) for category in UPPER_CATEGORIES
            )
            best_category, current_utility = self._best_choice(
                game.turn.current, open_categories, upper_score_so_far
            )
            if game.turn.spins_used == MAX_SPINS_PER_TURN:
                spins_used = game.turn.spins_used
                game.score(best_category)
                return SimulatedTurn(spins_used, used_locks)

            expected = [
                (
                    self._expected_utility(
                        game.turn.current, locks, open_categories, upper_score_so_far
                    ),
                    locks,
                )
                for locks in self.lock_options
            ]
            best_expected, best_locks = max(
                expected,
                key=lambda item: (item[0], -len(item[1]), _lock_name(item[1])),
            )
            if current_utility >= best_expected:
                spins_used = game.turn.spins_used
                game.score(best_category)
                return SimulatedTurn(spins_used, used_locks)
            used_locks[_lock_name(best_locks)] = used_locks.get(_lock_name(best_locks), 0) + 1
            game.reroll(best_locks)
        raise AssertionError("Turn unexpectedly ended without scoring")


def _lock_name(locks: frozenset[Lock]) -> str:
    return "+".join(lock.value for lock in Lock if lock in locks) or "none"


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


def _hierarchical_weights(
    records: tuple[PlayerTeamSeason, ...],
    locks: frozenset[Lock],
) -> tuple[tuple[PlayerTeamSeason, float], ...]:
    if not records:
        raise ValueError("Cannot weight an empty outcome pool")
    seasons = sorted({record.season for record in records})
    teams_by_season = {
        season: sorted({record.team for record in records if record.season == season})
        for season in seasons
    }
    player_counts = {
        (season, team): sum(
            record.season == season and record.team == team for record in records
        )
        for season in seasons
        for team in teams_by_season[season]
    }
    weighted = []
    for record in records:
        season_weight = 1.0 if Lock.SEASON in locks else 1 / len(seasons)
        team_weight = (
            1.0 if Lock.TEAM in locks else 1 / len(teams_by_season[record.season])
        )
        player_weight = (
            1.0 if Lock.PLAYER in locks
            else 1 / player_counts[(record.season, record.team)]
        )
        weighted.append((record, season_weight * team_weight * player_weight))
    if abs(sum(weight for _, weight in weighted) - 1.0) > 1e-12:
        raise ValueError("Locked outcome weights do not sum to one")
    return tuple(weighted)


def simulate_game(
    records: tuple[PlayerTeamSeason, ...],
    policy: RandomPolicy | GreedyPolicy | StrategicPolicy,
    seed: int,
) -> SimulatedGame:
    roulette_rng = random.Random(seed)
    policy_rng = random.Random(seed ^ 0x9E3779B9)
    game = GameState(RouletteEngine(records, roulette_rng))
    spins_used = 0
    lock_counts: dict[str, int] = {}
    while not game.is_complete:
        turn = policy.play_turn(game, policy_rng)
        spins_used += turn.spins_used
        for lock_name, count in turn.lock_counts.items():
            lock_counts[lock_name] = lock_counts.get(lock_name, 0) + count
    return SimulatedGame(
        total_score=game.total_score,
        bonus=game.bonus,
        spins_used=spins_used,
        scorecard=dict(game.scorecard),
        lock_counts=lock_counts,
        upper_score=sum(game.scorecard[category] for category in UPPER_CATEGORIES),
    )


def summarize_games(games: list[SimulatedGame]) -> dict:
    if not games:
        raise ValueError("At least one simulated game is required")
    totals = sorted(game.total_score for game in games)
    upper_scores = sorted(game.upper_score for game in games)

    def percentile(probability: float) -> float:
        position = (len(totals) - 1) * probability
        lower = int(position)
        upper = min(lower + 1, len(totals) - 1)
        fraction = position - lower
        return totals[lower] * (1 - fraction) + totals[upper] * fraction

    def upper_percentile(probability: float) -> float:
        position = (len(upper_scores) - 1) * probability
        lower = int(position)
        upper = min(lower + 1, len(upper_scores) - 1)
        fraction = position - lower
        return upper_scores[lower] * (1 - fraction) + upper_scores[upper] * fraction

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
        "upper_score": {
            "mean": mean(upper_scores),
            "p10": upper_percentile(0.10),
            "median": upper_percentile(0.50),
            "p90": upper_percentile(0.90),
            "threshold_rates": {
                str(threshold): mean(game.upper_score >= threshold for game in games)
                for threshold in (120, 130, 135, 140, 145, 150)
            },
        },
        "average_spins_per_game": mean(game.spins_used for game in games),
        "average_spins_per_turn": mean(game.spins_used for game in games) / len(Category),
        "average_lock_uses_per_game": {
            lock_name: mean(game.lock_counts.get(lock_name, 0) for game in games)
            for lock_name in sorted({name for game in games for name in game.lock_counts})
        },
        "categories": {
            category.value: {
                "mean": mean(game.scorecard[category] for game in games),
                "zero_rate": mean(game.scorecard[category] == 0 for game in games),
            }
            for category in Category
        },
    }
