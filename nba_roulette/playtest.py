"""Persistent local logging for structured browser playtest batches."""

from __future__ import annotations

import csv
import json
import threading
from pathlib import Path


class PlaytestBatchLogger:
    def __init__(self, directory: Path, batch_id: str, batch_name: str, target: int = 10) -> None:
        self.directory = directory
        self.batch_id = batch_id
        self.batch_name = batch_name
        self.target = target
        self.jsonl_path = directory / f"{batch_id}.jsonl"
        self.csv_path = directory / f"{batch_id}.csv"
        self._lock = threading.Lock()

    def completed_count(self) -> int:
        if not self.jsonl_path.exists():
            return 0
        return sum(1 for line in self.jsonl_path.read_text(encoding="utf-8").splitlines() if line)

    def save(self, record: dict) -> int | None:
        with self._lock:
            completed = self.completed_count()
            if completed >= self.target:
                return None
            index = completed + 1
            self.directory.mkdir(parents=True, exist_ok=True)
            payload = {
                "batch_id": self.batch_id,
                "batch_name": self.batch_name,
                "batch_game": index,
                "batch_target": self.target,
                **record,
            }
            with self.jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self._append_summary(payload)
            return index

    def _append_summary(self, payload: dict) -> None:
        fields = (
            "batch_game", "game_id", "completed_at", "final_score", "upper_score",
            "bonus", "zero_accolades", "spins_seen", "rerolls_used", "keep_uses",
            "unique_players_seen", "repeated_player_appearances",
        )
        write_header = not self.csv_path.exists()
        with self.csv_path.open("a", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            if write_header:
                writer.writeheader()
            writer.writerow({field: payload[field] for field in fields})
