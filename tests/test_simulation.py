from __future__ import annotations

import random
import unittest

from nba_roulette.game import GameState
from nba_roulette.roulette import RouletteEngine
from nba_roulette.scoring import Category
from nba_roulette.simulation import GreedyPolicy, RandomPolicy, simulate_game, summarize_games

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
