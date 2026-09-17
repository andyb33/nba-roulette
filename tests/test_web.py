import unittest

from nba_roulette.scoring import Category
from nba_roulette.web import BrowserGame

from .test_roulette import pool


class BrowserGameTests(unittest.TestCase):
    def test_initial_state_is_ready_to_spin(self) -> None:
        state = BrowserGame(pool(), seed=1).state()
        self.assertIsNone(state["player"])
        self.assertEqual(state["turn"], 1)
        self.assertEqual(len(state["categories"]), 14)

    def test_spin_keep_and_score_round_trip(self) -> None:
        browser = BrowserGame(pool(), seed=7)
        first = browser.spin()
        season = first["player"]["season"]
        second = browser.spin(["season"])
        self.assertEqual(second["player"]["season"], season)
        self.assertEqual(second["spins_used"], 2)
        scored = browser.score(Category.POINTS.value)
        points = next(item for item in scored["categories"] if item["id"] == "points")
        self.assertTrue(points["used"])
        self.assertIsNone(scored["player"])
        self.assertEqual(scored["turn"], 2)

    def test_all_three_keeps_are_rejected_by_engine(self) -> None:
        browser = BrowserGame(pool(), seed=3)
        browser.spin()
        with self.assertRaisesRegex(ValueError, "all three"):
            browser.spin(["season", "team", "player"])

    def test_unknown_category_is_rejected(self) -> None:
        browser = BrowserGame(pool(), seed=3)
        browser.spin()
        with self.assertRaisesRegex(ValueError, "Unknown score category"):
            browser.score("not-a-category")

    def test_complete_browser_game_reports_final_state(self) -> None:
        browser = BrowserGame(pool(), seed=9)
        state = None
        for category in Category:
            browser.spin()
            state = browser.score(category.value)
        self.assertIsNotNone(state)
        self.assertTrue(state["complete"])
        self.assertEqual(state["turn"], 14)
        self.assertEqual(sum(item["used"] for item in state["categories"]), 14)


if __name__ == "__main__":
    unittest.main()
