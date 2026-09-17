from __future__ import annotations

import unittest

from nba_roulette.models import PlayerTeamSeason
from nba_roulette.scoring import (
    Category, UPPER_BONUS_SCORE, UPPER_BONUS_THRESHOLD,
    category_score, round_half_up, upper_bonus,
)


def record(**overrides) -> PlayerTeamSeason:
    values = {
        "season": "2024-25", "player_id": 1, "player": "Test Player", "team": "AAA",
        "gp": 81, "mpg": 32.0, "ppg": 10.25, "rpg": 4.5, "apg": 3.5,
        "spg": 1.2, "bpg": 0.5, "jersey": 77, "all_nba": 1,
        "all_defense": 2, "champion": True, "mvp": True, "dpoy": True, "roy": False,
    }
    values.update(overrides)
    return PlayerTeamSeason(**values)


class ScoringTests(unittest.TestCase):
    def test_round_half_up_boundaries(self) -> None:
        self.assertEqual(round_half_up(20.49), 20)
        self.assertEqual(round_half_up(20.50), 21)
        self.assertEqual(round_half_up(20.51), 21)
        with self.assertRaises(ValueError):
            round_half_up(-0.1)

    def test_stat_and_joker_scores(self) -> None:
        item = record()
        self.assertEqual(category_score(item, Category.POINTS), 21)
        self.assertEqual(category_score(item, Category.REBOUNDS), 14)
        self.assertEqual(category_score(item, Category.ASSISTS), 11)
        self.assertEqual(category_score(item, Category.STEALS), 12)
        self.assertEqual(category_score(item, Category.BLOCKS), 5)
        self.assertEqual(category_score(item, Category.GAMES_PLAYED), 81)
        self.assertEqual(category_score(item, Category.JERSEY), 77)

    def test_accolades_require_exact_tiers(self) -> None:
        item = record()
        self.assertEqual(category_score(item, Category.ALL_NBA_FIRST), 40)
        self.assertEqual(category_score(item, Category.ALL_NBA_SECOND), 0)
        self.assertEqual(category_score(item, Category.ALL_NBA_THIRD), 0)
        self.assertEqual(category_score(item, Category.ALL_DEFENSE_FIRST), 0)
        self.assertEqual(category_score(item, Category.ALL_DEFENSE_SECOND), 30)
        self.assertEqual(category_score(item, Category.CHAMPION), 25)
        self.assertEqual(category_score(item, Category.MAJOR_AWARD), 50)

    def test_major_awards_do_not_stack(self) -> None:
        self.assertEqual(category_score(record(mvp=True, dpoy=True, roy=True), Category.MAJOR_AWARD), 50)
        self.assertEqual(category_score(record(mvp=False, dpoy=False, roy=False), Category.MAJOR_AWARD), 0)

    def test_upper_bonus_boundaries_and_exclusions(self) -> None:
        base = {
            Category.POINTS: 35, Category.REBOUNDS: 25, Category.ASSISTS: 25,
            Category.STEALS: 18, Category.BLOCKS: 16,
            Category.GAMES_PLAYED: 82, Category.JERSEY: 99,
        }
        self.assertEqual(sum(base[category] for category in (
            Category.POINTS, Category.REBOUNDS, Category.ASSISTS,
            Category.STEALS, Category.BLOCKS,
        )), UPPER_BONUS_THRESHOLD - 1)
        self.assertEqual(upper_bonus(base), 0)
        base[Category.BLOCKS] = 17
        self.assertEqual(upper_bonus(base), UPPER_BONUS_SCORE)
        base[Category.BLOCKS] = 18
        self.assertEqual(upper_bonus(base), UPPER_BONUS_SCORE)
        del base[Category.BLOCKS]
        self.assertEqual(upper_bonus(base), 0)


if __name__ == "__main__":
    unittest.main()
