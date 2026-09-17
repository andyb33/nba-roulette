from __future__ import annotations

import random
import unittest

from nba_roulette.game import GameState
from nba_roulette.roulette import RouletteEngine
from nba_roulette.scoring import Category
from nba_roulette.simulation import (
    GreedyPolicy, RandomPolicy, StrategicPolicy, simulate_game, summarize_games,
)

from .test_roulette import pool


class SimulationTests(unittest.TestCase):
    def test_random_policy_completes_legal_game(self) -> None:
        records = pool()
        result = simulate_game(records, RandomPolicy(), 123)
        self.assertEqual(set(result.scorecard), set(Category))
        self.assertGreaterEqual(result.spins_used, 14)
        self.assertLessEqual(result.spins_used, 42)

    def test_greedy_policy_completes_legal_game(self) -> None:
        records = pool()
        result = simulate_game(records, GreedyPolicy(records), 456)
        self.assertEqual(set(result.scorecard), set(Category))
        self.assertGreaterEqual(result.spins_used, 14)
        self.assertLessEqual(result.spins_used, 42)

    def test_strategic_policy_completes_game_and_uses_legal_locks(self) -> None:
        records = pool()
        result = simulate_game(records, StrategicPolicy(records), 789)
        self.assertEqual(set(result.scorecard), set(Category))
        self.assertGreaterEqual(result.spins_used, 14)
        self.assertLessEqual(result.spins_used, 42)
        legal = {
            "none", "season", "team", "player", "season+team",
            "season+player", "team+player",
        }
        self.assertTrue(set(result.lock_counts).issubset(legal))
        self.assertEqual(
            result.upper_score,
            sum(result.scorecard[category] for category in (
                Category.POINTS, Category.REBOUNDS, Category.ASSISTS,
                Category.STEALS, Category.BLOCKS,
            )),
        )

    def test_strategic_policy_rejects_negative_bonus_equity(self) -> None:
        with self.assertRaises(ValueError):
            StrategicPolicy(pool(), bonus_equity_per_category=-1)

    def test_gap_aware_bonus_mode_completes_game(self) -> None:
        records = pool()
        result = simulate_game(
            records,
            StrategicPolicy(records, bonus_equity_per_category=14, gap_aware_bonus=True),
            790,
        )
        self.assertEqual(set(result.scorecard), set(Category))

    def test_greedy_threshold_is_stable(self) -> None:
        records = pool()
        policy = GreedyPolicy(records)
        categories = tuple(Category)
        self.assertEqual(
            policy.expected_best_score(categories),
            policy.expected_best_score(categories),
        )

    def test_same_seed_reproduces_simulation(self) -> None:
        records = pool()
        first = simulate_game(records, RandomPolicy(), 999)
        second = simulate_game(records, RandomPolicy(), 999)
        self.assertEqual(first, second)

    def test_summary_includes_every_category(self) -> None:
        records = pool()
        games = [simulate_game(records, RandomPolicy(), seed) for seed in range(10)]
        summary = summarize_games(games)
        self.assertEqual(set(summary["categories"]), {category.value for category in Category})


if __name__ == "__main__":
    unittest.main()
