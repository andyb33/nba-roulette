from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from nba_roulette.playtest import PlaytestBatchLogger
from nba_roulette.scoring import Category
from nba_roulette.web import BrowserGame

from .test_roulette import pool


class PlaytestLoggingTests(unittest.TestCase):
    def test_completed_game_writes_detailed_jsonl_and_csv_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            logger = PlaytestBatchLogger(directory, "batch_test", "Batch Test", target=10)
            browser = BrowserGame(pool(), seed=17, logger=logger)
            for category in Category:
                browser.spin()
                browser.score(category.value)

            record = json.loads(logger.jsonl_path.read_text(encoding="utf-8").strip())
            with logger.csv_path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(record["batch_game"], 1)
            self.assertEqual(record["batch_name"], "Batch Test")
            self.assertEqual(len(record["categories"]), 14)
            self.assertEqual(len(record["events"]), 28)
            self.assertEqual(record["spins_seen"], 14)
            self.assertEqual(len(rows), 1)
            self.assertEqual(int(rows[0]["final_score"]), record["final_score"])
            self.assertEqual(browser.state()["playtest"]["completed"], 1)

    def test_batch_stops_after_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logger = PlaytestBatchLogger(Path(temporary), "batch_test", "Batch Test", target=1)
            self.assertEqual(logger.save(self._record("first")), 1)
            self.assertIsNone(logger.save(self._record("second")))
            self.assertEqual(logger.completed_count(), 1)

    @staticmethod
    def _record(game_id: str) -> dict:
        return {
            "game_id": game_id, "completed_at": "2026-09-18T00:00:00+00:00",
            "final_score": 300, "upper_score": 120, "bonus": 35,
            "zero_accolades": 3, "spins_seen": 42, "rerolls_used": 28,
            "keep_uses": 10, "unique_players_seen": 38,
            "repeated_player_appearances": 4,
        }


if __name__ == "__main__":
    unittest.main()
