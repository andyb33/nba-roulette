#!/usr/bin/env python3
"""Build the consolidated three-season simulation rerun report."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
OUTPUT = ROOT / "docs" / "THREE_SEASON_SIMULATION_RERUN.md"


def main() -> None:
    baseline = json.loads((ANALYSIS / "baseline_simulation.json").read_text(encoding="utf-8"))
    strategic_payload = json.loads((ANALYSIS / "strategic_simulation.json").read_text(encoding="utf-8"))
    sensitivity = json.loads((ANALYSIS / "bonus_sensitivity.json").read_text(encoding="utf-8"))
    strategic = strategic_payload["strategic"]
    old_strategic = strategic_payload["two_season_baseline"]["strategic"]

    lines = [
        "# NBA Roulette — Three-Season Simulation Rerun",
        "",
        "- **Pool:** 1,346 eligible player-team-season records",
        "- **Seasons:** 2023–24 through 2025–26",
        "- **Policies:** Random, Greedy, Strategic, and four Upper Bonus sensitivity profiles",
        "- **Rule set:** GDD v1.2, cumulative accolade eligibility, 120 → +35 Upper Bonus",
        "",
        "## Full-game comparison",
        "",
        "| Policy | Games | Two-season mean | Three-season mean | Change | Two-season bonus | Three-season bonus |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("random", "greedy"):
        new = baseline["policies"][name]
        old = baseline["two_season_baseline"]["policies"][name]
        lines.append(
            f"| {name.title()} | {baseline['games_per_policy']:,} | {old['total_score']['mean']:.1f} | "
            f"{new['total_score']['mean']:.1f} | {new['total_score']['mean'] - old['total_score']['mean']:+.1f} | "
            f"{old['upper_bonus_rate']:.2%} | {new['upper_bonus_rate']:.2%} |"
        )
    lines.append(
        f"| Strategic | {strategic_payload['games']:,} | {old_strategic['total_score']['mean']:.1f} | "
        f"{strategic['total_score']['mean']:.1f} | "
        f"{strategic['total_score']['mean'] - old_strategic['total_score']['mean']:+.1f} | "
        f"{old_strategic['upper_bonus_rate']:.2%} | {strategic['upper_bonus_rate']:.2%} |"
    )
    lines.extend([
        "",
        "## Upper Bonus sensitivity",
        "",
        "| Profile | Mean total | Mean upper | 120+ | 130+ | 140+ |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for name, profile in sensitivity["profiles"].items():
        result = profile["result"]
        rates = result["upper_score"]["threshold_rates"]
        lines.append(
            f"| {name.replace('_', ' ').title()} | {result['total_score']['mean']:.1f} | "
            f"{result['upper_score']['mean']:.1f} | {rates['120']:.2%} | "
            f"{rates['130']:.2%} | {rates['140']:.2%} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "1. **Keep 120 → +35.** Strategic profiles reached 120 in 17.25%–23.55% of games. This is demanding but realistically attainable.",
        "2. **Do not return to 140.** Only 1.60%–2.35% of sensitivity games reached 140.",
        "3. **Do not increase the bonus-chasing weight.** The Neutral profile produced both the highest mean total and the highest 120 attainment; forcing bonus pursuit caused premature upper-category placement.",
        "4. **Keep the rest of the scoring system unchanged for the browser prototype.** Adding 2025–26 moved full-game means by only −1.3 to +2.9 points across the primary policies.",
        "5. **Validate with Human Playtest 2.** Simulation supports the current rules, but player understanding and enjoyment remain the deciding evidence.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python scripts/simulate_baselines.py",
        "python scripts/simulate_strategic.py",
        "python scripts/simulate_bonus_sensitivity.py",
        "python scripts/summarize_simulation_rerun.py",
        "```",
        "",
    ])
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
