from __future__ import annotations

import random
import unittest
from collections import Counter

from nba_roulette.models import Lock, PlayerTeamSeason
from nba_roulette.roulette import RouletteEngine


def make_record(season: str, team: str, player_id: int, name: str | None = None) -> PlayerTeamSeason:
    return PlayerTeamSeason(
        season=season, player_id=player_id, player=name or f"Player {player_id}", team=team,
        gp=20, mpg=15.0, ppg=5.0, rpg=2.0, apg=1.0, spg=0.5, bpg=0.2,
        jersey=player_id % 100, all_nba=None, all_defense=None,
        champion=False, mvp=False, dpoy=False, roy=False,
    )


def pool() -> tuple[PlayerTeamSeason, ...]:
    return (
        make_record("S1", "A", 1, "Traded"),
        make_record("S1", "A", 2),
        make_record("S1", "B", 1, "Traded"),
        make_record("S1", "B", 3),
        make_record("S1", "B", 4),
        make_record("S2", "A", 1, "Traded"),
        make_record("S2", "A", 5),
        make_record("S2", "B", 6),
        make_record("S2", "B", 7),
        make_record("S2", "B", 8),
        make_record("S2", "B", 9),
    )


class RouletteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = pool()
        self.current = self.records[0]

    def test_same_seed_reproduces_sequence(self) -> None:
        first = RouletteEngine(self.records, random.Random(123))
        second = RouletteEngine(self.records, random.Random(123))
        self.assertEqual([first.spin() for _ in range(100)], [second.spin() for _ in range(100)])

    def test_standard_spin_is_hierarchical_not_record_flat(self) -> None:
        engine = RouletteEngine(self.records, random.Random(7))
        outcomes = [engine.spin() for _ in range(40_000)]
        seasons = Counter(row.season for row in outcomes)
        self.assertAlmostEqual(seasons["S1"] / len(outcomes), 0.5, delta=0.015)
        for season in ("S1", "S2"):
            subset = [row for row in outcomes if row.season == season]
            teams = Counter(row.team for row in subset)
            self.assertAlmostEqual(teams["A"] / len(subset), 0.5, delta=0.02)

    def test_every_lock_mask_produces_only_matching_valid_rows(self) -> None:
        all_rows = set(self.records)
        masks = (
            {Lock.SEASON}, {Lock.TEAM}, {Lock.PLAYER},
            {Lock.SEASON, Lock.TEAM}, {Lock.SEASON, Lock.PLAYER},
            {Lock.TEAM, Lock.PLAYER},
        )
        for mask in masks:
            with self.subTest(mask=mask):
                engine = RouletteEngine(self.records, random.Random(9))
                outcomes = [engine.spin(self.current, mask) for _ in range(2_000)]
                self.assertTrue(set(outcomes).issubset(all_rows))
                for row in outcomes:
                    if Lock.SEASON in mask:
                        self.assertEqual(row.season, self.current.season)
                    if Lock.TEAM in mask:
                        self.assertEqual(row.team, self.current.team)
                    if Lock.PLAYER in mask:
                        self.assertEqual(row.player_id, self.current.player_id)

    def test_player_lock_weights_season_before_team(self) -> None:
        engine = RouletteEngine(self.records, random.Random(11))
        outcomes = [engine.spin(self.current, {Lock.PLAYER}) for _ in range(40_000)]
        seasons = Counter(row.season for row in outcomes)
        self.assertAlmostEqual(seasons["S1"] / len(outcomes), 0.5, delta=0.015)
        s1 = [row for row in outcomes if row.season == "S1"]
        teams = Counter(row.team for row in s1)
        self.assertAlmostEqual(teams["A"] / len(s1), 0.5, delta=0.02)

    def test_season_and_player_lock_equal_weights_trade_stints(self) -> None:
        engine = RouletteEngine(self.records, random.Random(12))
        outcomes = [engine.spin(self.current, {Lock.SEASON, Lock.PLAYER}) for _ in range(20_000)]
        teams = Counter(row.team for row in outcomes)
        self.assertAlmostEqual(teams["A"] / len(outcomes), 0.5, delta=0.02)

    def test_season_and_team_lock_weights_players_equally(self) -> None:
        engine = RouletteEngine(self.records, random.Random(13))
        outcomes = [engine.spin(self.current, {Lock.SEASON, Lock.TEAM}) for _ in range(20_000)]
        players = Counter(row.player_id for row in outcomes)
        self.assertAlmostEqual(players[1] / len(outcomes), 0.5, delta=0.02)

    def test_all_locks_disable_reroll(self) -> None:
        engine = RouletteEngine(self.records)
        with self.assertRaises(ValueError):
            engine.spin(self.current, set(Lock))

    def test_locks_require_current_result(self) -> None:
        engine = RouletteEngine(self.records)
        with self.assertRaises(ValueError):
            engine.spin(None, {Lock.SEASON})

    def test_duplicate_records_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RouletteEngine((*self.records, self.records[0]))

    def test_dynamic_locks_apply_to_latest_result(self) -> None:
        engine = RouletteEngine(self.records, random.Random(21))
        second = engine.spin(self.current, {Lock.SEASON})
        third = engine.spin(second, {Lock.PLAYER})
        self.assertEqual(second.season, self.current.season)
        self.assertEqual(third.player_id, second.player_id)


if __name__ == "__main__":
    unittest.main()
