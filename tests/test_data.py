from __future__ import annotations

import unittest
from collections import Counter

from nba_roulette.data import load_records


class DataLoaderTests(unittest.TestCase):
    def test_loads_validated_two_season_pool(self) -> None:
        records = load_records()
        self.assertEqual(len(records), 895)
        self.assertEqual(Counter(row.season for row in records), {"2023-24": 441, "2024-25": 454})
        self.assertEqual(len({(row.season, row.team) for row in records}), 60)
        self.assertTrue(all(row.gp >= 15 and row.mpg >= 10.0 for row in records))
        self.assertTrue(all(0 <= row.jersey <= 99 for row in records))


if __name__ == "__main__":
    unittest.main()
