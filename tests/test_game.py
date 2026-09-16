from __future__ import annotations

import random
import unittest

from nba_roulette.game import GameState
from nba_roulette.models import Lock
from nba_roulette.roulette import RouletteEngine
from nba_roulette.scoring import Category

from .test_roulette import pool


class GameStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = GameState(RouletteEngine(pool(), random.Random(99)))

    def test_turn_allows_one_spin_and_two_rerolls(self) -> None:
        self.game.start_turn()
        self.assertEqual(self.game.turn.spins_used, 1)
        self.game.reroll({Lock.SEASON})
        self.game.reroll()
        self.assertEqual(self.game.turn.spins_used, 3)
        with self.assertRaises(RuntimeError):
            self.game.reroll()

    def test_scoring_after_any_spin_ends_turn(self) -> None:
        self.game.start_turn()
        value = self.game.score(Category.POINTS)
        self.assertIsInstance(value, int)
        self.assertIsNone(self.game.turn)
        self.assertEqual(self.game.turns_completed, 1)

    def test_preview_only_returns_open_categories(self) -> None:
        self.game.start_turn()
        self.game.score(Category.POINTS)
        self.game.start_turn()
        preview = self.game.preview()
        self.assertNotIn(Category.POINTS, preview)
        self.assertEqual(len(preview), len(Category) - 1)

    def test_nonqualifying_accolade_can_score_zero(self) -> None:
        self.game.start_turn()
        self.assertEqual(self.game.score(Category.ALL_NBA_FIRST), 0)

    def test_category_cannot_be_reused(self) -> None:
        self.game.start_turn()
        self.game.score(Category.JERSEY)
        self.game.start_turn()
        with self.assertRaises(ValueError):
            self.game.score(Category.JERSEY)

    def test_complete_game_consumes_all_fourteen_categories(self) -> None:
        for category in Category:
            self.game.start_turn()
            self.game.score(category)
        self.assertTrue(self.game.is_complete)
        self.assertEqual(self.game.turns_completed, 14)
        self.assertEqual(set(self.game.scorecard), set(Category))
        self.assertEqual(self.game.total_score, sum(self.game.scorecard.values()) + self.game.bonus)
        with self.assertRaises(RuntimeError):
            self.game.start_turn()

    def test_turn_must_be_active_for_actions(self) -> None:
        with self.assertRaises(RuntimeError):
            self.game.reroll()
        with self.assertRaises(RuntimeError):
            self.game.preview()
        with self.assertRaises(RuntimeError):
            self.game.score(Category.POINTS)

    def test_cannot_start_overlapping_turns(self) -> None:
        self.game.start_turn()
        with self.assertRaises(RuntimeError):
            self.game.start_turn()


if __name__ == "__main__":
    unittest.main()
