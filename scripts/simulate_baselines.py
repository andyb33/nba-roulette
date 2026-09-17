#!/usr/bin/env python3
"""Run reproducible Random and Greedy NBA Roulette baselines."""

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
from nba_roulette.simulation import GreedyPolicy, RandomPolicy, simulate_game, summarize_games


ANALYSIS = ROOT / "analysis"
DOC = ROOT / "docs" / "BASELINE_SIMULATION.md"
DEFAULT_GAMES = 10_000
DEFAULT_SEED = 20260917


def run_policy(records, policy, games: int, seed: int) -> dict:
    results = [simulate_game(records, policy, seed + index) for index in range(games)]
    return summarize_games(results)


def write_category_csv(summary: dict) -> None:
    path = ANALYSIS / "baseline_category_summary.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("policy", "category", "mean_score", "zero_rate"),
        )
        writer.writeheader()
        for policy, result in summary["policies"].items():
            for category in Category:
                values = result["categories"][category.value]
                writer.writerow({
                    "policy": policy,
                    "category": category.value,
                    "mean_score": round(values["mean"], 6),
                    "zero_rate": round(values["zero_rate"], 6),
                })


def write_report(summary: dict) -> None:
    lines = [
        "# NBA Roulette — Random and Greedy Baselines",
        "",
        "This report establishes two reproducible, non-strategic full-game baselines",
        "before introducing lock-aware play.",
        "",
        "## Policy definitions",
        "",
        "- **Random:** uses no locks, chooses 1–3 spins uniformly, then assigns the",
        "  result to a uniformly random open category.",
        "- **Greedy:** uses no locks, selects the highest current open-category score,",
        "  and rerolls only while that score is below the expected best score of a fresh",
        "  unlocked spin. It does not plan across future turns.",
        "",
        f"Both policies played **{summary['games_per_policy']:,} complete 14-turn games**",
        f"with master seed `{summary['seed']}` against {summary['dataset_records']} records.",
        "",
        "## Full-game results",
        "",
        "| Policy | Mean | P10 | Median | P90 | Bonus rate | Spins/game |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for policy, result in summary["policies"].items():
        total = result["total_score"]
        lines.append(
            f"| {policy.title()} | {total['mean']:.1f} | {total['p10']:.0f} | "
            f"{total['median']:.0f} | {total['p90']:.0f} | "
            f"{result['upper_bonus_rate']:.2%} | {result['average_spins_per_game']:.2f} |"
        )
    lines.extend([
        "",
        "## Category outcomes",
        "",
        "| Category | Random mean | Random zero | Greedy mean | Greedy zero |",
        "|---|---:|---:|---:|---:|",
    ])
    random_result = summary["policies"]["random"]["categories"]
    greedy_result = summary["policies"]["greedy"]["categories"]
    for category in Category:
        random_values = random_result[category.value]
        greedy_values = greedy_result[category.value]
        lines.append(
            f"| {category.value.replace('_', ' ').title()} | "
            f"{random_values['mean']:.2f} | {random_values['zero_rate']:.2%} | "
            f"{greedy_values['mean']:.2f} | {greedy_values['zero_rate']:.2%} |"
        )
    lines.extend([
        "",
        "## Initial findings",
        "",
        f"- Greedy improves mean score by **{summary['policies']['greedy']['total_score']['mean'] - summary['policies']['random']['total_score']['mean']:.1f} points** over Random without using locks.",
        f"- The Upper Bonus appeared in **{summary['policies']['random']['upper_bonus_rate']:.2%}** of Random games and **{summary['policies']['greedy']['upper_bonus_rate']:.2%}** of Greedy games.",
        "- Accolades remain the main source of zeroes. Even Greedy scored zero in most",
        "  exact-team All-NBA, All-Defense, and Major Award slots.",
        "- GP is the strongest reliable category, while Jersey provides a large but",
        "  volatile score. A strategic policy must account for both before judging balance.",
        "",
        "## Interpretation boundary",
        "",
        "These are calibration baselines, not estimates of skilled-player performance.",
        "Neither policy locks Season, Team, or Player. The Greedy policy is intentionally",
        "myopic and compares category point values directly; the next simulation milestone",
        "is a lock-aware strategy that values scarcity and remaining turns.",
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

    records = load_records()
    summary = {
        "seed": args.seed,
        "games_per_policy": args.games,
        "dataset_records": len(records),
        "seasons": sorted({record.season for record in records}),
        "policies": {
            "random": run_policy(records, RandomPolicy(), args.games, args.seed),
            "greedy": run_policy(records, GreedyPolicy(records), args.games, args.seed + 10_000_000),
        },
    }
    ANALYSIS.mkdir(exist_ok=True)
    (ANALYSIS / "baseline_simulation.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_category_csv(summary)
    write_report(summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
