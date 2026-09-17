#!/usr/bin/env python3
"""Run the lock-aware heuristic and compare it with saved baselines."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nba_roulette.data import load_records
from nba_roulette.scoring import Category
from nba_roulette.simulation import StrategicPolicy, simulate_game, summarize_games


ANALYSIS = ROOT / "analysis"
BASELINES = ANALYSIS / "baseline_simulation.json"
OUTPUT = ANALYSIS / "strategic_simulation.json"
CATEGORY_OUTPUT = ANALYSIS / "strategic_category_summary.csv"
DOC = ROOT / "docs" / "STRATEGIC_SIMULATION.md"
DEFAULT_GAMES = 5_000
DEFAULT_SEED = 20260918


def write_category_csv(result: dict) -> None:
    with CATEGORY_OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("category", "mean_score", "zero_rate"),
            lineterminator="\n",
        )
        writer.writeheader()
        for category in Category:
            values = result["categories"][category.value]
            writer.writerow({
                "category": category.value,
                "mean_score": round(values["mean"], 6),
                "zero_rate": round(values["zero_rate"], 6),
            })


def write_report(payload: dict, baselines: dict) -> None:
    strategic = payload["strategic"]
    policies = {**baselines["policies"], "strategic": strategic}
    lines = [
        "# NBA Roulette — Strategic Lock-Aware Simulation",
        "",
        "The Strategic policy is a transparent heuristic, not a claim of optimal play.",
        "It values each score against that category's expected replacement value, adds",
        "limited Upper Bonus equity, and compares every legal lock mask using exact",
        "hierarchical outcome probabilities before each reroll.",
        "",
        f"The policy played **{payload['games']:,} complete games** with master seed",
        f"`{payload['seed']}` against {payload['dataset_records']} player-team records.",
        "",
        "## Comparison",
        "",
        "| Policy | Mean | P10 | Median | P90 | Bonus rate | Spins/game |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("random", "greedy", "strategic"):
        result = policies[name]
        total = result["total_score"]
        lines.append(
            f"| {name.title()} | {total['mean']:.1f} | {total['p10']:.0f} | "
            f"{total['median']:.0f} | {total['p90']:.0f} | "
            f"{result['upper_bonus_rate']:.2%} | {result['average_spins_per_game']:.2f} |"
        )
    lines.extend([
        "",
        "## Strategic category outcomes",
        "",
        "| Category | Mean | Zero rate | Greedy zero rate |",
        "|---|---:|---:|---:|",
    ])
    greedy_categories = policies["greedy"]["categories"]
    for category in Category:
        values = strategic["categories"][category.value]
        lines.append(
            f"| {category.value.replace('_', ' ').title()} | {values['mean']:.2f} | "
            f"{values['zero_rate']:.2%} | "
            f"{greedy_categories[category.value]['zero_rate']:.2%} |"
        )
    lines.extend([
        "",
        "## Lock use",
        "",
        "| Lock mask | Average uses per game |",
        "|---|---:|",
    ])
    for lock_name, average in strategic["average_lock_uses_per_game"].items():
        lines.append(f"| {lock_name} | {average:.2f} |")
    greedy_mean = policies["greedy"]["total_score"]["mean"]
    lines.extend([
        "",
        "## Findings",
        "",
        f"- Strategic play changes mean score by **{strategic['total_score']['mean'] - greedy_mean:+.1f} points** versus Greedy.",
        f"- The Upper Bonus rate rises from **{policies['greedy']['upper_bonus_rate']:.2%}** to **{strategic['upper_bonus_rate']:.2%}**.",
        "- Category zero rates show whether lock knowledge meaningfully improves rare",
        "  accolades rather than merely increasing common statistical scores.",
        "- The heuristic's assumptions should be varied in sensitivity tests before any",
        "  permanent scoring change is made.",
    ])
    previous = payload.get("two_season_baseline")
    if previous:
        old = previous["strategic"]
        lines.extend([
            "",
            "## Effect of adding 2025–26",
            "",
            "| Metric | Two-season | Three-season | Change |",
            "|---|---:|---:|---:|",
            f"| Mean score | {old['total_score']['mean']:.1f} | {strategic['total_score']['mean']:.1f} | {strategic['total_score']['mean'] - old['total_score']['mean']:+.1f} |",
            f"| Median score | {old['total_score']['median']:.0f} | {strategic['total_score']['median']:.0f} | {strategic['total_score']['median'] - old['total_score']['median']:+.0f} |",
            f"| Upper Bonus rate | {old['upper_bonus_rate']:.2%} | {strategic['upper_bonus_rate']:.2%} | {strategic['upper_bonus_rate'] - old['upper_bonus_rate']:+.2%} |",
        ])
    lines.extend([
        "",
    ])
    DOC.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    if args.games <= 0:
        parser.error("--games must be positive")
    if not BASELINES.exists():
        raise FileNotFoundError("Run scripts/simulate_baselines.py first")

    records = load_records()
    previous = None
    if OUTPUT.exists():
        saved = json.loads(OUTPUT.read_text(encoding="utf-8"))
        previous = saved.get("two_season_baseline", saved)
        if previous.get("dataset_records") != 895:
            previous = None
    policy = StrategicPolicy(records)
    games = [simulate_game(records, policy, args.seed + index) for index in range(args.games)]
    result = summarize_games(games)
    payload = {
        "seed": args.seed,
        "games": args.games,
        "dataset_records": len(records),
        "seasons": sorted({record.season for record in records}),
        "policy_definition": "replacement-value, bonus-aware, exact lock-mask heuristic",
        "strategic": result,
    }
    if previous:
        payload["two_season_baseline"] = previous
    baselines = json.loads(BASELINES.read_text(encoding="utf-8"))
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_category_csv(result)
    write_report(payload, baselines)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
