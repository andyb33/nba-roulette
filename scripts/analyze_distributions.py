#!/usr/bin/env python3
"""Produce the three-season NBA Roulette distribution analysis and charts."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
SEASONS = ("2023-24", "2024-25", "2025-26")
SLUGS = {season: season.replace("-", "_") for season in SEASONS}
ANALYSIS = ROOT / "analysis"
CHARTS = ANALYSIS / "charts"
DOC = ROOT / "docs" / "DISTRIBUTION_REPORT.md"

RAW_METRICS = ("ppg", "rpg", "apg", "spg", "bpg", "gp", "jersey")
SCORE_FIELDS = ("pts_score", "reb_score", "ast_score", "stl_score", "blk_score")
SCORE_LABELS = {
    "pts_score": "PTS ×2",
    "reb_score": "REB ×3",
    "ast_score": "AST ×3",
    "stl_score": "STL ×10",
    "blk_score": "BLK ×10",
}
PALETTE = ["#2B5CE6", "#0F9D8A", "#F59E0B", "#8B5CF6", "#EF4444"]


def round_half_up(value: float) -> int:
    """Match the GDD rule: round a non-negative score to the nearest integer."""
    return math.floor(value + 0.5)


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot calculate a percentile for an empty list")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def weighted_percentile(values: list[float], weights: list[float], probability: float) -> float:
    ordered = sorted(zip(values, weights), key=lambda item: item[0])
    target = probability * sum(weights)
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= target:
            return value
    return ordered[-1][0]


def summarize(values: list[float], weights: list[float] | None = None) -> dict[str, float]:
    if weights is None:
        quantile = lambda p: percentile(values, p)
        average = mean(values)
    else:
        quantile = lambda p: weighted_percentile(values, weights, p)
        average = sum(value * weight for value, weight in zip(values, weights)) / sum(weights)
    return {
        "min": min(values),
        "p10": quantile(0.10),
        "p25": quantile(0.25),
        "median": quantile(0.50),
        "mean": average,
        "p75": quantile(0.75),
        "p90": quantile(0.90),
        "p95": quantile(0.95),
        "max": max(values),
    }


def load_records() -> list[dict]:
    records = []
    for season in SEASONS:
        path = ROOT / "data" / "processed" / f"nba_roulette_{SLUGS[season]}.csv"
        with path.open(encoding="utf-8-sig") as handle:
            for source in csv.DictReader(handle):
                row = dict(source)
                for field in ("gp", "jersey"):
                    row[field] = int(row[field])
                for field in ("mpg", "ppg", "rpg", "apg", "spg", "bpg"):
                    row[field] = float(row[field])
                for field in ("all_nba", "all_defense"):
                    row[field] = int(row[field]) if row[field] else None
                for field in ("champion", "mvp", "dpoy", "roy"):
                    row[field] = row[field] == "True"
                row.update({
                    "pts_score": round_half_up(row["ppg"] * 2),
                    "reb_score": round_half_up(row["rpg"] * 3),
                    "ast_score": round_half_up(row["apg"] * 3),
                    "stl_score": round_half_up(row["spg"] * 10),
                    "blk_score": round_half_up(row["bpg"] * 10),
                })
                records.append(row)
    return records


def add_roulette_weights(records: list[dict]) -> None:
    counts = Counter((row["season"], row["team"]) for row in records)
    season_count = len(SEASONS)
    for row in records:
        row["roulette_weight"] = 1 / (season_count * 30 * counts[(row["season"], row["team"])])
    if not math.isclose(sum(row["roulette_weight"] for row in records), 1.0, abs_tol=1e-12):
        raise ValueError("Roulette weights do not sum to one")


def threshold_rates(records: list[dict], field: str, thresholds: list[int]) -> dict[str, float]:
    return {
        str(threshold): sum(row["roulette_weight"] for row in records if row[field] >= threshold)
        for threshold in thresholds
    }


def top_records(records: list[dict], field: str, limit: int = 5) -> list[dict]:
    return [
        {
            "season": row["season"], "team": row["team"], "player": row["player"],
            "value": row[field],
        }
        for row in sorted(records, key=lambda row: (-row[field], row["player"]))[:limit]
    ]


def build_summary(records: list[dict]) -> dict:
    weights = [row["roulette_weight"] for row in records]
    team_counts = Counter((row["season"], row["team"]) for row in records)
    distribution = {}
    distribution_by_season = {season: {} for season in SEASONS}
    for field in RAW_METRICS + SCORE_FIELDS:
        values = [row[field] for row in records]
        distribution[field] = {
            "record_weighted": summarize(values),
            "roulette_weighted": summarize(values, weights),
        }
        for season in SEASONS:
            season_rows = [row for row in records if row["season"] == season]
            distribution_by_season[season][field] = summarize(
                [row[field] for row in season_rows],
                [row["roulette_weight"] for row in season_rows],
            )

    score_thresholds = {
        field: threshold_rates(records, field, [10, 20, 30, 40, 50, 60])
        for field in SCORE_FIELDS
    }
    score_thresholds["gp"] = threshold_rates(records, "gp", [50, 60, 70, 75, 80, 82])
    score_thresholds["jersey"] = threshold_rates(records, "jersey", [20, 30, 40, 50, 60, 70, 80, 90])

    accolade = {}
    qualifiers = {
        "all_nba_third": lambda r: r["all_nba"] in (1, 2, 3),
        "all_nba_second": lambda r: r["all_nba"] in (1, 2),
        "all_nba_first": lambda r: r["all_nba"] == 1,
        "champion": lambda r: r["champion"],
        "all_defense_second": lambda r: r["all_defense"] in (1, 2),
        "all_defense_first": lambda r: r["all_defense"] == 1,
        "major_award": lambda r: r["mvp"] or r["dpoy"] or r["roy"],
    }
    for name, predicate in qualifiers.items():
        accolade[name] = {
            "records": sum(predicate(row) for row in records),
            "standard_spin_probability": sum(row["roulette_weight"] for row in records if predicate(row)),
            "by_season": {
                season: sum(predicate(row) for row in records if row["season"] == season)
                for season in SEASONS
            },
        }

    jersey_bands = [(0, 9), (10, 19), (20, 29), (30, 39), (40, 49),
                    (50, 59), (60, 69), (70, 79), (80, 89), (90, 99)]
    gp_bands = [(15, 29), (30, 49), (50, 69), (70, 79), (80, 82), (83, 99)]

    baseline_rows = [row for row in records if row["season"] != "2025-26"]
    baseline_weight_total = sum(row["roulette_weight"] for row in baseline_rows)
    baseline_weights = [row["roulette_weight"] / baseline_weight_total for row in baseline_rows]

    return {
        "scope": {
            "seasons": list(SEASONS),
            "records": len(records),
            "teams_per_season": 30,
            "eligibility": {"minimum_team_gp": 15, "minimum_team_mpg": 10.0},
            "weighting": "Equal season, then equal team, then equal eligible player",
        },
        "records_by_season": Counter(row["season"] for row in records),
        "eligible_records_per_team": {
            season: summarize([count for (item_season, _), count in team_counts.items() if item_season == season])
            for season in SEASONS
        },
        "distributions": distribution,
        "roulette_distributions_by_season": distribution_by_season,
        "two_season_baseline": {
            field: summarize([row[field] for row in baseline_rows], baseline_weights)
            for field in RAW_METRICS + SCORE_FIELDS
        },
        "roulette_threshold_probabilities": score_thresholds,
        "jersey_bands": {
            f"{low}-{high}": {
                "records": sum(low <= row["jersey"] <= high for row in records),
                "standard_spin_probability": sum(row["roulette_weight"] for row in records if low <= row["jersey"] <= high),
            }
            for low, high in jersey_bands
        },
        "gp_bands": {
            f"{low}-{high}" if high < 99 else "83+": {
                "records": sum(low <= row["gp"] <= high for row in records),
                "standard_spin_probability": sum(row["roulette_weight"] for row in records if low <= row["gp"] <= high),
            }
            for low, high in gp_bands
        },
        "accolades": accolade,
        "top_records": {
            field: top_records(records, field) for field in SCORE_FIELDS + ("gp", "jersey")
        },
    }


def save_chart_percentiles(summary: dict) -> None:
    fields = list(SCORE_FIELDS)
    quantiles = ("median", "p75", "p90", "p95")
    x = range(len(fields))
    width = 0.19
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for index, quantile in enumerate(quantiles):
        values = [summary["distributions"][field]["roulette_weighted"][quantile] for field in fields]
        ax.bar([item + (index - 1.5) * width for item in x], values, width, label=quantile.upper())
    ax.set_xticks(list(x), [SCORE_LABELS[field] for field in fields])
    ax.set_ylabel("Score")
    ax.set_title("Roulette-weighted statistical score percentiles")
    ax.legend(ncols=4, frameon=False)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(CHARTS / "category_percentiles.png", dpi=180, transparent=False)
    plt.close(fig)


def save_chart_distributions(records: list[dict]) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    weights = [row["roulette_weight"] for row in records]
    for ax, field, color in zip(axes.flat, SCORE_FIELDS, PALETTE):
        values = [row[field] for row in records]
        bins = range(0, max(values) + 4, 4)
        ax.hist(values, bins=bins, weights=weights, color=color, alpha=0.82, edgecolor="white")
        ax.set_title(SCORE_LABELS[field])
        ax.set_xlabel("Score")
        ax.set_ylabel("Spin probability")
        ax.grid(axis="y", alpha=0.15)
    axes.flat[-1].axis("off")
    fig.suptitle("Statistical category score distributions", fontsize=15)
    fig.tight_layout()
    fig.savefig(CHARTS / "stat_score_distributions.png", dpi=180, transparent=False)
    plt.close(fig)


def save_chart_jokers(records: list[dict]) -> None:
    weights = [row["roulette_weight"] for row in records]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].hist([row["gp"] for row in records], bins=range(15, 86, 5), weights=weights,
                 color=PALETTE[0], edgecolor="white")
    axes[0].set(title="Games played", xlabel="GP score", ylabel="Spin probability")
    axes[1].hist([row["jersey"] for row in records], bins=range(0, 101, 10), weights=weights,
                 color=PALETTE[1], edgecolor="white")
    axes[1].set(title="Jersey number", xlabel="Jersey score", ylabel="Spin probability")
    for ax in axes:
        ax.grid(axis="y", alpha=0.15)
    fig.suptitle("Joker category distributions", fontsize=15)
    fig.tight_layout()
    fig.savefig(CHARTS / "joker_distributions.png", dpi=180, transparent=False)
    plt.close(fig)


def save_chart_accolades(summary: dict) -> None:
    labels = ["All-NBA 3rd", "All-NBA 2nd", "All-NBA 1st", "Champion",
              "All-Defense 2nd", "All-Defense 1st", "Major Award"]
    keys = list(summary["accolades"])
    probabilities = [summary["accolades"][key]["standard_spin_probability"] * 100 for key in keys]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    bars = ax.barh(labels, probabilities, color="#2B5CE6")
    ax.invert_yaxis()
    ax.set_xlabel("Probability on a standard unlocked spin (%)")
    ax.set_title("Accolade qualification rarity")
    ax.grid(axis="x", alpha=0.2)
    ax.bar_label(bars, labels=[f"{value:.2f}%" for value in probabilities], padding=4)
    fig.tight_layout()
    fig.savefig(CHARTS / "accolade_probabilities.png", dpi=180, transparent=False)
    plt.close(fig)


def save_chart_season_comparison(summary: dict) -> None:
    fields = list(SCORE_FIELDS)
    x = range(len(fields))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    for index, season in enumerate(SEASONS):
        values = [summary["roulette_distributions_by_season"][season][field]["mean"] for field in fields]
        offset = index - (len(SEASONS) - 1) / 2
        ax.bar([item + offset * width for item in x], values, width, label=season)
    ax.set_xticks(list(x), [SCORE_LABELS[field] for field in fields])
    ax.set_ylabel("Mean score")
    ax.set_title("Mean statistical scores by season")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(CHARTS / "season_score_comparison.png", dpi=180, transparent=False)
    plt.close(fig)


def format_value(value: float) -> str:
    return f"{value:.1f}" if not float(value).is_integer() else str(int(value))


def markdown_table(summary: dict) -> str:
    lines = [
        "| Category | Mean | Median | P75 | P90 | P95 | Maximum |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for field in SCORE_FIELDS:
        item = summary["distributions"][field]["roulette_weighted"]
        lines.append(
            f"| {SCORE_LABELS[field]} | {format_value(item['mean'])} | {format_value(item['median'])} | "
            f"{format_value(item['p75'])} | {format_value(item['p90'])} | "
            f"{format_value(item['p95'])} | {format_value(item['max'])} |"
        )
    return "\n".join(lines)


def write_report(summary: dict) -> None:
    gp = summary["distributions"]["gp"]["roulette_weighted"]
    jersey = summary["distributions"]["jersey"]["roulette_weighted"]
    accolades = summary["accolades"]
    def pct(value: float) -> str:
        return f"{value * 100:.2f}%"

    season_header = " | ".join(f"{season} mean" for season in SEASONS)
    season_alignment = "|".join("---:" for _ in SEASONS)
    season_rows = []
    for field in SCORE_FIELDS:
        values = [summary["roulette_distributions_by_season"][season][field]["mean"] for season in SEASONS]
        season_rows.append(
            f"| {SCORE_LABELS[field]} | " + " | ".join(f"{value:.1f}" for value in values) + " |"
        )
    season_table = (
        f"| Category | {season_header} |\n"
        f"|---|{season_alignment}|\n" + "\n".join(season_rows)
    )
    comparison_rows = []
    for field in SCORE_FIELDS + ("gp", "jersey"):
        old = summary["two_season_baseline"][field]["mean"]
        new = summary["distributions"][field]["roulette_weighted"]["mean"]
        comparison_rows.append(
            f"| {SCORE_LABELS.get(field, field.upper())} | {old:.1f} | {new:.1f} | {new-old:+.1f} |"
        )
    comparison_table = (
        "| Category | Two-season mean | Three-season mean | Change |\n"
        "|---|---:|---:|---:|\n" + "\n".join(comparison_rows)
    )
    report = f"""# NBA Roulette — Three-Season Distribution Report

- **Seasons:** 2023–24 through 2025–26
- **Eligible player-team-season records:** {summary['scope']['records']}
- **Eligibility:** 15+ GP and 10.0+ MPG for the selected team
- **Status:** Descriptive balance analysis; the three-season roulette simulation follows separately.

## Executive Summary

- The five performance categories are not naturally equal after weighting. PTS has a roulette-weighted median of {format_value(summary['distributions']['pts_score']['roulette_weighted']['median'])}, while BLK has a median of {format_value(summary['distributions']['blk_score']['roulette_weighted']['median'])}.
- PTS supplies the highest routine scores. AST, STL, and especially BLK remain the specialist outcomes most likely to constrain the 120-point Upper Bonus.
- GP is a consistently valuable Joker: median {format_value(gp['median'])}, P90 {format_value(gp['p90'])}, and maximum {format_value(gp['max'])}.
- Jersey is intentionally volatile: median {format_value(jersey['median'])}, P90 {format_value(jersey['p90'])}, and maximum {format_value(jersey['max'])}. High numbers produce rare rescue or jackpot outcomes.
- Cumulative tiers create the intended rarity ladder: All-NBA Third accepts {pct(accolades['all_nba_third']['standard_spin_probability'])} of unlocked spins, Second accepts {pct(accolades['all_nba_second']['standard_spin_probability'])}, and First accepts {pct(accolades['all_nba_first']['standard_spin_probability'])}.
- Adding 2025–26 does not by itself justify a scoring change. The 120 → +35 rule should be judged again in the upcoming three-season simulation.

## Method

The canonical observation is one **Player × Team × Season** record. The report distinguishes:

1. **Record-weighted distributions**, where each of the 1,346 rows counts equally.
2. **Roulette-weighted distributions**, matching the game rule: equal Season → equal Team → equal eligible Player.

The second view is the relevant gameplay baseline because team roster sizes vary. Scores use the GDD multipliers and round-half-up rule:

- PTS = PPG × 2
- REB = RPG × 3
- AST = APG × 3
- STL = SPG × 10
- BLK = BPG × 10
- GP = games played
- Jersey = final jersey number for the team stint

## Statistical Score Distributions

{markdown_table(summary)}

![Statistical category distributions](../analysis/charts/stat_score_distributions.png)

![Category percentiles](../analysis/charts/category_percentiles.png)

### Interpretation

- A P90 outcome is approximately {format_value(summary['distributions']['pts_score']['roulette_weighted']['p90'])} PTS points, {format_value(summary['distributions']['reb_score']['roulette_weighted']['p90'])} REB points, {format_value(summary['distributions']['ast_score']['roulette_weighted']['p90'])} AST points, {format_value(summary['distributions']['stl_score']['roulette_weighted']['p90'])} STL points, and {format_value(summary['distributions']['blk_score']['roulette_weighted']['p90'])} BLK points.
- Even strong percentile selections do not make the Upper Bonus automatic. The player must assemble quality across five different outcomes and categories.
- Category multipliers should not be judged by equal medians alone. Scarcity and the value of targeted locks are part of the intended strategy.

## Season Comparison

{season_table}

![Season score comparison](../analysis/charts/season_score_comparison.png)

## Effect of Adding 2025–26

{comparison_table}

This comparison uses roulette weighting in both pools. It isolates whether adding the third season materially changes the distribution rather than merely adding more rows.

## Joker Categories

| Category | Mean | Median | P75 | P90 | P95 | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| GP | {format_value(gp['mean'])} | {format_value(gp['median'])} | {format_value(gp['p75'])} | {format_value(gp['p90'])} | {format_value(gp['p95'])} | {format_value(gp['max'])} |
| Jersey | {format_value(jersey['mean'])} | {format_value(jersey['median'])} | {format_value(jersey['p75'])} | {format_value(jersey['p90'])} | {format_value(jersey['p95'])} | {format_value(jersey['max'])} |

![Joker distributions](../analysis/charts/joker_distributions.png)

GP is the safer Joker; Jersey has the heavier upside tail. That distinction supports the intended rescue mechanic without making the categories function identically.

## Accolade Rarity

| Category | Eligible records | Standard-spin probability | Score |
|---|---:|---:|---:|
| All-NBA Third (First/Second/Third eligible) | {accolades['all_nba_third']['records']} | {pct(accolades['all_nba_third']['standard_spin_probability'])} | 20 |
| All-NBA Second (First/Second eligible) | {accolades['all_nba_second']['records']} | {pct(accolades['all_nba_second']['standard_spin_probability'])} | 30 |
| All-NBA First | {accolades['all_nba_first']['records']} | {pct(accolades['all_nba_first']['standard_spin_probability'])} | 40 |
| Champion | {accolades['champion']['records']} | {pct(accolades['champion']['standard_spin_probability'])} | 25 |
| All-Defense Second (First/Second eligible) | {accolades['all_defense_second']['records']} | {pct(accolades['all_defense_second']['standard_spin_probability'])} | 30 |
| All-Defense First | {accolades['all_defense_first']['records']} | {pct(accolades['all_defense_first']['standard_spin_probability'])} | 40 |
| Major Award | {accolades['major_award']['records']} | {pct(accolades['major_award']['standard_spin_probability'])} | 50 |

![Accolade probabilities](../analysis/charts/accolade_probabilities.png)

Major Award and First-team categories remain the rarest targets. The cumulative rule makes lower-tier categories appropriately easier without changing their fixed scores.

## Observed Category Ceilings

| Category | Highest eligible player-team-season | Score |
|---|---|---:|
"""
    for field in SCORE_FIELDS + ("gp", "jersey"):
        top = summary["top_records"][field][0]
        label = SCORE_LABELS.get(field, field.upper())
        report += f"| {label} | {top['player']} — {top['team']} {top['season']} | {top['value']} |\n"
    report += f"""

## Dataset and Season Checks

- 2023–24: {summary['records_by_season']['2023-24']} eligible records.
- 2024–25: {summary['records_by_season']['2024-25']} eligible records.
- 2025–26: {summary['records_by_season']['2025-26']} eligible records.
- Every season contains all 30 teams.
- Eligible roster sizes range from {int(min(summary['eligible_records_per_team'][season]['min'] for season in SEASONS))} to {int(max(summary['eligible_records_per_team'][season]['max'] for season in SEASONS))} players per team-season.
- The analysis contains no missing jersey values and no records below the eligibility thresholds.

## Balance Decisions Supported Now

1. Retain the existing statistical multipliers for the first playable prototype.
2. Retain GP and Jersey as deliberately different Joker distributions.
3. Retain cumulative accolade eligibility and the fixed accolade scores.
4. Retain **120 → +35** for the next simulation; distributions alone do not overturn the playtest and two-season simulation evidence.
5. Rerun Random, Greedy, Strategic, and sensitivity simulations before making another balance change.

## Reproduce

```bash
python scripts/analyze_distributions.py
```

This regenerates the JSON summary, CSV tables, charts, and this report from the three processed season datasets.
"""
    DOC.write_text(report, encoding="utf-8")


def write_csv_outputs(summary: dict) -> None:
    path = ANALYSIS / "category_distribution_summary.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["category", "weighting", "min", "p10", "p25", "median", "mean", "p75", "p90", "p95", "max"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for field in RAW_METRICS + SCORE_FIELDS:
            for weighting, values in summary["distributions"][field].items():
                writer.writerow({"category": field, "weighting": weighting, **values})

    path = ANALYSIS / "accolade_summary.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["category", "eligible_records", "standard_spin_probability", *SEASONS]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for category, values in summary["accolades"].items():
            writer.writerow({
                "category": category,
                "eligible_records": values["records"],
                "standard_spin_probability": values["standard_spin_probability"],
                **values["by_season"],
            })


def validate(records: list[dict], summary: dict) -> None:
    assert len(records) == 1346
    assert Counter(row["season"] for row in records) == Counter({
        "2023-24": 441, "2024-25": 454, "2025-26": 451,
    })
    assert len({(row["season"], row["team"]) for row in records}) == 90
    assert len({(row["season"], row["team"], row["player_id"]) for row in records}) == len(records)
    assert all(row["gp"] >= 15 and row["mpg"] >= 10.0 for row in records)
    assert all(row["jersey"] is not None for row in records)
    assert summary["accolades"]["all_nba_first"]["records"] == 15
    assert summary["accolades"]["all_nba_second"]["records"] == 30
    assert summary["accolades"]["all_nba_third"]["records"] == 45
    assert summary["accolades"]["all_defense_first"]["records"] == 15
    assert summary["accolades"]["all_defense_second"]["records"] == 30
    assert summary["accolades"]["major_award"]["records"] == 9


def validate_outputs() -> None:
    from PIL import Image

    expected = (
        "category_percentiles.png", "stat_score_distributions.png",
        "joker_distributions.png", "accolade_probabilities.png",
        "season_score_comparison.png",
    )
    for filename in expected:
        path = CHARTS / filename
        if not path.exists() or path.stat().st_size == 0:
            raise ValueError(f"Missing or empty chart: {path}")
        with Image.open(path) as image:
            image.verify()


def main() -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    records = load_records()
    add_roulette_weights(records)
    summary = build_summary(records)
    validate(records, summary)
    (ANALYSIS / "distribution_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_csv_outputs(summary)
    save_chart_percentiles(summary)
    save_chart_distributions(records)
    save_chart_jokers(records)
    save_chart_accolades(summary)
    save_chart_season_comparison(summary)
    write_report(summary)
    validate_outputs()
    print(json.dumps({
        "records": len(records),
        "outputs": [
            str(DOC.relative_to(ROOT)),
            str((ANALYSIS / "distribution_summary.json").relative_to(ROOT)),
            str((ANALYSIS / "category_distribution_summary.csv").relative_to(ROOT)),
            str((ANALYSIS / "accolade_summary.csv").relative_to(ROOT)),
            *[str(path.relative_to(ROOT)) for path in sorted(CHARTS.glob("*.png"))],
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
