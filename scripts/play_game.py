#!/usr/bin/env python3
"""Play one complete NBA Roulette game in a terminal."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nba_roulette.data import load_records
from nba_roulette.game import GameState, MAX_SPINS_PER_TURN
from nba_roulette.models import Lock
from nba_roulette.roulette import RouletteEngine
from nba_roulette.scoring import Category, UPPER_CATEGORIES


def show_turn(game: GameState) -> None:
    assert game.turn is not None
    item = game.turn.current
    print(f"\nTurn {game.turns_completed + 1}/14 · Spin {game.turn.spins_used}/3")
    print(f"{item.season} | {item.team} | {item.player} | #{item.jersey}")
    print(
        f"{item.ppg:.1f} PPG · {item.rpg:.1f} RPG · {item.apg:.1f} APG · "
        f"{item.spg:.1f} SPG · {item.bpg:.1f} BPG · {item.gp} GP"
    )
    preview = game.preview()
    print("Open scores:")
    print("  " + " | ".join(
        f"{index + 1}:{category.value}={preview[category]}"
        for index, category in enumerate(game.open_categories)
    ))


def parse_kept_slots(words: list[str]) -> set[Lock]:
    mapping = {lock.value: lock for lock in Lock}
    unknown = [word for word in words if word not in mapping]
    if unknown:
        raise ValueError(f"Unknown slot(s) to keep: {', '.join(unknown)}")
    locks = {mapping[word] for word in words}
    if locks == set(Lock):
        raise ValueError("Keeping all three slots leaves nothing to reroll")
    return locks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1_000_000_000)
    game = GameState(RouletteEngine(load_records(), random.Random(seed)))
    print(f"NBA Roulette · seed {seed}")
    print("Commands: keep [season] [team] [player] | reroll | score <number/name>")

    while not game.is_complete:
        game.start_turn()
        while game.turn is not None:
            show_turn(game)
            command = input("Choice: ").strip().lower().split()
            if not command:
                continue
            try:
                if command[0] in {"k", "keep"}:
                    if game.turn.spins_used >= MAX_SPINS_PER_TURN:
                        raise ValueError("No rerolls remain")
                    if len(command) == 1:
                        raise ValueError("Name at least one slot to keep")
                    game.reroll(parse_kept_slots(command[1:]))
                elif command[0] in {"r", "reroll"}:
                    if game.turn.spins_used >= MAX_SPINS_PER_TURN:
                        raise ValueError("No rerolls remain")
                    if len(command) != 1:
                        raise ValueError("Use 'keep season/team/player' to preserve slots")
                    game.reroll()
                elif command[0] in {"s", "score"} and len(command) == 2:
                    open_categories = game.open_categories
                    if command[1].isdigit():
                        position = int(command[1]) - 1
                        if not 0 <= position < len(open_categories):
                            raise ValueError("Category number is out of range")
                        category = open_categories[position]
                    else:
                        category = Category(command[1])
                    value = game.score(category)
                    print(f"Scored {value} in {category.value}.")
                else:
                    raise ValueError("Use: keep [slots], reroll, or score <number/name>")
            except (ValueError, RuntimeError) as error:
                print(f"Invalid choice: {error}")

    upper_total = sum(game.scorecard[category] for category in UPPER_CATEGORIES)
    print("\nGame complete")
    print(f"Upper total: {upper_total} · Bonus: {game.bonus}")
    print(f"Final score: {game.total_score}")


if __name__ == "__main__":
    main()
