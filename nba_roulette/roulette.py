"""Hierarchical Season → Team → Player roulette with dynamic locks."""

from __future__ import annotations

import random
from collections.abc import Iterable

from .models import Lock, PlayerTeamSeason


class RouletteEngine:
    def __init__(
        self,
        records: Iterable[PlayerTeamSeason],
        rng: random.Random | None = None,
    ) -> None:
        self.records = tuple(records)
        if not self.records:
            raise ValueError("The roulette pool cannot be empty")
        keys = {(row.season, row.team, row.player_id) for row in self.records}
        if len(keys) != len(self.records):
            raise ValueError("Duplicate season/team/player records found")
        self.rng = rng or random.Random()
        self._standard_tree = self._build_tree(self.records)
        self._locked_trees: dict[
            tuple[str, str, int, frozenset[Lock]],
            dict[str, dict[str, tuple[PlayerTeamSeason, ...]]],
        ] = {}

    def spin(
        self,
        current: PlayerTeamSeason | None = None,
        locks: Iterable[Lock] = (),
    ) -> PlayerTeamSeason:
        lock_set = frozenset(locks)
        if not lock_set and current is None:
            return self._resolve(self._standard_tree, lock_set, current)
        if not lock_set:
            if len(self.records) == 1:
                return self.records[0]
            while True:
                result = self._resolve(self._standard_tree, lock_set, current)
                if result != current:
                    return result
        if current is None:
            raise ValueError("Locks require a current roulette result")
        if lock_set == frozenset(Lock):
            raise ValueError("Cannot reroll while all three slots are locked")
        if not lock_set.issubset(frozenset(Lock)):
            raise ValueError("Unknown roulette lock")
        tree = self._tree_for_locks(current, lock_set)
        return self._resolve(tree, lock_set, current)

    def valid_outcomes(
        self,
        current: PlayerTeamSeason,
        locks: Iterable[Lock],
    ) -> tuple[PlayerTeamSeason, ...]:
        lock_set = frozenset(locks)
        tree = self._tree_for_locks(current, lock_set)
        return tuple(
            record
            for teams in tree.values()
            for players in teams.values()
            for record in players
        )

    def _resolve(
        self,
        tree: dict[str, dict[str, tuple[PlayerTeamSeason, ...]]],
        locks: frozenset[Lock],
        current: PlayerTeamSeason | None,
    ) -> PlayerTeamSeason:
        if Lock.SEASON in locks:
            season = current.season  # type: ignore[union-attr]
        else:
            season = self.rng.choice(tuple(tree))
        season_tree = tree[season]

        if Lock.TEAM in locks:
            team = current.team  # type: ignore[union-attr]
        else:
            team = self.rng.choice(tuple(season_tree))
        team_pool = season_tree[team]

        if Lock.PLAYER in locks:
            player_id = current.player_id  # type: ignore[union-attr]
            player_pool = tuple(record for record in team_pool if record.player_id == player_id)
            if len(player_pool) != 1:
                raise ValueError("Locked player did not resolve to one player-team-season record")
            return player_pool[0]
        return self.rng.choice(team_pool)

    def _tree_for_locks(
        self,
        current: PlayerTeamSeason,
        locks: frozenset[Lock],
    ) -> dict[str, dict[str, tuple[PlayerTeamSeason, ...]]]:
        key = (current.season, current.team, current.player_id, locks)
        if key not in self._locked_trees:
            candidates = tuple(
                record
                for record in self.records
                if self._matches(record, current, locks) and record != current
            )
            if not candidates:
                candidates = tuple(
                    record for record in self.records if self._matches(record, current, locks)
                )
            if not candidates:
                raise ValueError("No valid outcomes match the selected locks")
            self._locked_trees[key] = self._build_tree(candidates)
        return self._locked_trees[key]

    @staticmethod
    def _build_tree(
        records: Iterable[PlayerTeamSeason],
    ) -> dict[str, dict[str, tuple[PlayerTeamSeason, ...]]]:
        staged: dict[str, dict[str, list[PlayerTeamSeason]]] = {}
        for record in sorted(records, key=lambda row: (row.season, row.team, row.player_id)):
            staged.setdefault(record.season, {}).setdefault(record.team, []).append(record)
        return {
            season: {team: tuple(players) for team, players in teams.items()}
            for season, teams in staged.items()
        }

    @staticmethod
    def _matches(
        candidate: PlayerTeamSeason,
        current: PlayerTeamSeason,
        locks: frozenset[Lock],
    ) -> bool:
        return (
            (Lock.SEASON not in locks or candidate.season == current.season)
            and (Lock.TEAM not in locks or candidate.team == current.team)
            and (Lock.PLAYER not in locks or candidate.player_id == current.player_id)
        )
