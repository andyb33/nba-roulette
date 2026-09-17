#!/usr/bin/env python3
"""Test how strongly prioritizing the Upper Bonus changes game outcomes."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nba_roulette.data import load_records
from nba_roulette.simulation import StrategicPolicy, simulate_game, summarize_games


ANALYSIS = ROOT / "analysis"
OUTPUT = ANALYSIS / "bonus_sensitivity.json"
CSV_OUTPUT = ANALYSIS / "bonus_sensitivity_summary.csv"
DOC = ROOT / "docs" / "BONUS_SENSITIVITY.md"
DEFAULT_GAMES = 2_000
DEFAULT_SEED = 20260919
PROFILES = {
    "neutral": 0.0,
    "balanced": 7.0,
    "aggressive": 14.0,
    "very_aggressive": 28.0,
}


def write_csv(payload: dict) -> None:
    with CSV_OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "profile", "bonus_equity", "mean_total", "median_total",
            "mean_upper", "median_upper", "bonus_rate", "spins_per_game",
        ))
        writer.writeheader()
        for name, profile in payload["profiles"].items():
            result = profile["result"]
            writer.writerow({
                "profile": name,
                "bonus_equity": profile["bonus_equity_per_category"],
                "mean_total": round(result["total_score"]["mean"], 6),
                "median_total": result["total_score"]["median"],
                "mean_upper": round(result["upper_score"]["mean"], 6),
                "median_upper": result["upper_score"]["median"],
                "bonus_rate": round(result["upper_bonus_rate"], 6),
                "spins_per_game": round(result["average_spins_per_game"], 6),
            })


def write_report(payload: dict) -> None:
    lines = [
        "# NBA Roulette — Upper Bonus Sensitivity",
        "",
        "This experiment varies only the heuristic value assigned to progress in each",
        "upper category. Roulette rules, locks, score values, seeds, and dataset remain",
        "unchanged. Bonus equity is a decision weight, not points added to the game score.",
        "",
        f"Each profile played **{payload['games_per_profile']:,} complete games** against",
        f"{payload['dataset_records']} records using common starting seed `{payload['seed']}`.",
        "",
        "| Profile | Equity/category | Mean total | Median | Mean upper | Upper P90 | Bonus rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, profile in payload["profiles"].items():
        result = profile["result"]
        lines.append(
            f"| {name.replace('_', ' ').title()} | {profile['bonus_equity_per_category']:.0f} | "
            f"{result['total_score']['mean']:.1f} | {result['total_score']['median']:.0f} | "
            f"{result['upper_score']['mean']:.1f} | {result['upper_score']['p90']:.0f} | "
            f"{result['upper_bonus_rate']:.2%} |"
        )
    lines.extend([
        "",
        "## Threshold attainment",
        "",
        "| Profile | 120+ | 130+ | 135+ | 140+ | 145+ | 150+ |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for name, profile in payload["profiles"].items():
        rates = profile["result"]["upper_score"]["threshold_rates"]
        lines.append(
            f"| {name.replace('_', ' ').title()} | "
            + " | ".join(f"{rates[str(value)]:.2%}" for value in (120, 130, 135, 140, 145, 150))
            + " |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Raising bonus priority did not improve bonus attainment. Aggressive profiles",
        "  often consumed upper categories with mediocre scores too early.",
        "- **120 ranged from 16.20% to 24.25%**, while 130 ranged from 5.20% to 8.80%",
        "  and 140 ranged from 1.45% to 2.80% across profiles.",
        "- **Keep the prototype rule at 120 → +35.** It remains demanding and is",
        "  achieved in roughly one game in four by the strongest tested profile.",
        "- Keep 130 as a harder alternative for later testing; restore 140 only if real",
        "  players outperform the simulation or the third season changes the pool.",
        "- These simulations guide the prototype setting; human playtesting remains the",
        "  final check because people do not optimize like a deterministic heuristic.",
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
    profiles = {}
    for name, equity in PROFILES.items():
        policy = StrategicPolicy(
            records,
            bonus_equity_per_category=equity,
            gap_aware_bonus=True,
        )
        games = [
            simulate_game(records, policy, args.seed + index)
            for index in range(args.games)
        ]
        profiles[name] = {
            "bonus_equity_per_category": equity,
            "result": summarize_games(games),
        }
    payload = {
        "seed": args.seed,
        "games_per_profile": args.games,
        "dataset_records": len(records),
        "profiles": profiles,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_csv(payload)
    write_report(payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
