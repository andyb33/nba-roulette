import unittest
from dataclasses import replace

from nba_roulette.scoring import Category
from nba_roulette.web import BrowserGame

from .test_roulette import make_record, pool


class BrowserGameTests(unittest.TestCase):
    def test_initial_state_is_ready_to_spin(self) -> None:
        state = BrowserGame(pool(), seed=1).state()
        self.assertIsNone(state["player"])
        self.assertEqual(state["turn"], 1)
        self.assertEqual(len(state["categories"]), 14)
        points = next(item for item in state["categories"] if item["id"] == "points")
        major = next(item for item in state["categories"] if item["id"] == "major_award")
        self.assertEqual(points["formula"], "×2")
        self.assertEqual(points["glow_threshold"], 40)
        self.assertEqual(major["fixed_value"], 50)
        self.assertEqual(major["icon"], "⭐")

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

    def test_player_card_exposes_team_colors_and_vertical_awards(self) -> None:
        record = replace(
            make_record("S1", "BOS", 50, "Winner"),
            all_nba=1,
            all_defense=2,
            champion=True,
            mvp=True,
        )
        player = BrowserGame._player(record)
        self.assertEqual(player["team_colors"]["primary"], "#007A33")
        self.assertEqual(
            [award["label"] for award in player["awards"]],
            ["All-NBA First", "All-Defense Second", "Champion", "MVP"],
        )
        self.assertTrue(all("icon" in award for award in player["awards"]))


if __name__ == "__main__":
    unittest.main()
