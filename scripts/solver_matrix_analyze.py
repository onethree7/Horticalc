from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any


def _set_csv_field_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10


def _loads(value: str, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return ordered[index]


@dataclass
class ComparisonStats:
    scores: list[float] = field(default_factory=list)
    deltas: list[float] = field(default_factory=list)
    improvements_percent: list[float] = field(default_factory=list)
    elapsed: list[float] = field(default_factory=list)
    wins: int = 0
    ties: int = 0
    losses: int = 0

    def add(self, score: float, baseline: float, elapsed: float) -> None:
        delta = score - baseline
        improvement = ((baseline - score) / baseline * 100.0) if baseline else 0.0
        self.scores.append(score)
        self.deltas.append(delta)
        self.improvements_percent.append(improvement)
        self.elapsed.append(elapsed)
        tolerance = max(1e-9, abs(baseline) * 1e-12)
        if delta < -tolerance:
            self.wins += 1
        elif delta > tolerance:
            self.losses += 1
        else:
            self.ties += 1

    def to_dict(self) -> dict[str, Any]:
        count = len(self.scores)
        if not count:
            return {
                "count": 0,
                "avg_score": 0.0,
                "median_score": 0.0,
                "avg_delta": 0.0,
                "median_delta": 0.0,
                "avg_improvement_percent": 0.0,
                "avg_elapsed_seconds": 0.0,
                "p95_elapsed_seconds": 0.0,
                "wins": 0,
                "ties": 0,
                "losses": 0,
            }
        return {
            "count": count,
            "avg_score": statistics.fmean(self.scores),
            "median_score": statistics.median(self.scores),
            "min_score": min(self.scores),
            "max_score": max(self.scores),
            "avg_delta": statistics.fmean(self.deltas),
            "median_delta": statistics.median(self.deltas),
            "avg_improvement_percent": statistics.fmean(self.improvements_percent),
            "avg_elapsed_seconds": statistics.fmean(self.elapsed),
            "p95_elapsed_seconds": _percentile(self.elapsed, 0.95),
            "wins": self.wins,
            "ties": self.ties,
            "losses": self.losses,
        }


def _compact_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "run_id": row.get("run_id", ""),
        "profile_id": row.get("profile_id", ""),
        "profile_name": row.get("profile_name", ""),
        "profile_group": row.get("profile_group", ""),
        "phase": row.get("phase", ""),
        "portfolio_id": row.get("portfolio_id", ""),
        "omitted_fertilizer": row.get("omitted_fertilizer", ""),
        "experiment_id": row.get("experiment_id", ""),
        "config_id": row.get("config_id", ""),
        "config_name": row.get("config_name", ""),
        "solver_config": _loads(row.get("solver_config", ""), {}),
        "score": float(row["composite_score"]),
        "macro_score": float(row.get("macro_score") or 0.0),
        "n_form_score": float(row.get("n_form_score") or 0.0),
        "micro_score": float(row.get("micro_score") or 0.0),
        "other_score": float(row.get("other_score") or 0.0),
        "ignored_score": float(row.get("ignored_score") or 0.0),
        "max_error_key": row.get("max_error_key", ""),
        "max_error_score": float(row.get("max_error_score") or 0.0),
        "elapsed_seconds": float(row.get("elapsed_seconds") or 0.0),
        "total_grams": float(row.get("total_grams") or 0.0),
        "used_fertilizers": _loads(row.get("used_fertilizers", ""), []),
        "fertilizers_allowed": _loads(row.get("fertilizers_allowed", ""), []),
        "objective_elements": _loads(row.get("objective_elements", ""), []),
    }


def _ranked(stats: dict[Any, ComparisonStats]) -> list[tuple[Any, dict[str, Any]]]:
    rows = [(key, value.to_dict()) for key, value in stats.items()]
    rows.sort(
        key=lambda item: (
            -item[1]["avg_improvement_percent"],
            item[1]["avg_delta"],
            item[1]["avg_score"],
            str(item[0]),
        )
    )
    return rows


def analyze_run(run_dir: Path, *, top_limit: int = 30) -> dict[str, Any]:
    start = time.perf_counter()
    results_csv = run_dir / "results.csv"
    summary_path = run_dir / "summary.json"
    manifest_path = run_dir / "run_manifest.json"
    for path in (results_csv, summary_path, manifest_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing solver-matrix output: {path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if int(summary.get("schema_version") or 0) != 2:
        raise ValueError("Only solver-matrix schema_version 2 can be analyzed")

    _set_csv_field_limit()
    with results_csv.open("r", encoding="utf-8", newline="") as handle:
        raw_rows = list(csv.DictReader(handle))
    ok_rows = [row for row in raw_rows if row.get("status") == "ok"]

    counts = {
        "status": Counter(row.get("status", "") for row in raw_rows),
        "phase": Counter(row.get("phase", "") for row in raw_rows),
        "profile": Counter(row.get("profile_id", "") for row in raw_rows),
        "profile_group": Counter(row.get("profile_group", "") for row in raw_rows),
        "experiment": Counter(row.get("experiment_id", "") for row in raw_rows),
        "portfolio": Counter(row.get("portfolio_id", "") for row in raw_rows),
    }

    baseline_rows = {
        row["profile_id"]: row
        for row in ok_rows
        if row.get("phase") == "settings"
        and row.get("experiment_id") == "baseline"
        and row.get("config_id") == "canonical"
    }
    expected_profiles = set(summary.get("profiles") or [])
    missing_baselines = sorted(expected_profiles - set(baseline_rows))
    if missing_baselines:
        raise ValueError(f"Missing canonical baseline rows for: {', '.join(missing_baselines)}")
    baseline_scores = {
        profile_id: float(row["composite_score"])
        for profile_id, row in baseline_rows.items()
    }

    manifest_configs = {
        (str(item["experiment_id"]), str(item["config_id"])): item
        for item in manifest.get("solver_configs") or []
    }
    config_stats: dict[tuple[str, str], ComparisonStats] = defaultdict(ComparisonStats)
    parameter_stats: dict[str, dict[str, dict[str, dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    best_by_profile: dict[str, dict[str, Any]] = {}
    best_setting_by_profile: dict[str, dict[str, Any]] = {}

    for row in ok_rows:
        compact = _compact_row(row)
        profile_id = compact["profile_id"]
        current = best_by_profile.get(profile_id)
        if current is None or compact["score"] < current["score"]:
            best_by_profile[profile_id] = compact
        if compact["phase"] != "settings":
            continue
        current_setting = best_setting_by_profile.get(profile_id)
        if current_setting is None or compact["score"] < current_setting["score"]:
            best_setting_by_profile[profile_id] = compact
        baseline = baseline_scores[profile_id]
        key = (compact["experiment_id"], compact["config_id"])
        config_stats[key].add(compact["score"], baseline, compact["elapsed_seconds"])
        config_meta = manifest_configs.get(key) or {}
        for parameter in config_meta.get("varied_keys") or []:
            value = compact["solver_config"][parameter]
            value_key = _json(value)
            bucket = parameter_stats[compact["experiment_id"]][parameter].setdefault(
                value_key,
                {"value": value, "stats": ComparisonStats()},
            )
            bucket["stats"].add(compact["score"], baseline, compact["elapsed_seconds"])

    settings_by_experiment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    global_ranked = []
    for key, stats in _ranked(config_stats):
        experiment_id, config_id = key
        meta = manifest_configs.get(key) or {}
        item = {
            "experiment_id": experiment_id,
            "config_id": config_id,
            "config_name": meta.get("name", f"{experiment_id}:{config_id}"),
            "solver_config": meta.get("values", {}),
            "varied_keys": meta.get("varied_keys", []),
            **stats,
        }
        settings_by_experiment[experiment_id].append(item)
        global_ranked.append(item)

    setting_effects: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for experiment_id, parameters in sorted(parameter_stats.items()):
        setting_effects[experiment_id] = {}
        for parameter, buckets in sorted(parameters.items()):
            rows = [
                {"value": bucket["value"], **bucket["stats"].to_dict()}
                for bucket in buckets.values()
            ]
            rows.sort(
                key=lambda item: (
                    -item["avg_improvement_percent"],
                    item["avg_delta"],
                    _json(item["value"]),
                )
            )
            setting_effects[experiment_id][parameter] = rows

    mass_stats: dict[str, ComparisonStats] = defaultdict(ComparisonStats)
    mass_meta: dict[str, dict[str, Any]] = {}
    omission_stats: dict[str, ComparisonStats] = defaultdict(ComparisonStats)
    for row in ok_rows:
        if row.get("phase") != "mass_barrage":
            continue
        profile_id = row["profile_id"]
        portfolio_id = row["portfolio_id"]
        score = float(row["composite_score"])
        elapsed = float(row.get("elapsed_seconds") or 0.0)
        mass_stats[portfolio_id].add(score, baseline_scores[profile_id], elapsed)
        mass_meta[portfolio_id] = {
            "portfolio_source": row.get("portfolio_source", ""),
            "omitted_fertilizer": row.get("omitted_fertilizer", ""),
            "product_count": int(row.get("subset_size") or 0),
        }
        omitted = row.get("omitted_fertilizer", "")
        if omitted:
            omission_stats[omitted].add(score, baseline_scores[profile_id], elapsed)

    portfolio_comparison = [
        {"portfolio_id": key, **mass_meta[key], **stats}
        for key, stats in _ranked(mass_stats)
    ]
    omission_impact = [
        {"fertilizer": key, **stats}
        for key, stats in _ranked(omission_stats)
    ]
    # For omission results, positive delta means the removed product was useful.
    omission_impact.sort(key=lambda item: (-item["avg_delta"], item["fertilizer"]))

    baseline_by_profile = {
        profile_id: _compact_row(row)
        for profile_id, row in sorted(baseline_rows.items())
    }
    global_ranked.sort(
        key=lambda item: (
            -item["avg_improvement_percent"],
            item["avg_delta"],
            item["avg_score"],
            item["config_name"],
        )
    )
    return {
        "schema_version": 2,
        "meta": {
            "source_dir": str(run_dir.resolve()),
            "source_csv": str(results_csv.resolve()),
            "source_summary": str(summary_path.resolve()),
            "source_manifest": str(manifest_path.resolve()),
            "elapsed_analysis_seconds": time.perf_counter() - start,
            "summary_total_runs": summary.get("total_runs"),
            "summary_failed_runs": summary.get("failed_runs"),
            "planned_runs": summary.get("planned_runs"),
            "primary_portfolio": summary.get("primary_portfolio"),
            "allowed_fertilizers": summary.get("allowed_fertilizers", []),
            "profiles": summary.get("profiles", []),
            "unresolved_profiles": manifest.get("unresolved_profiles", []),
            "solver_baseline": manifest.get("solver_baseline", {}),
        },
        "counts": {key: dict(counter) for key, counter in counts.items()},
        "baseline_by_profile": baseline_by_profile,
        "best_setting_by_profile": dict(sorted(best_setting_by_profile.items())),
        "best_final_by_profile": dict(sorted(best_by_profile.items())),
        "settings_global_top": global_ranked[:top_limit],
        "settings_global_bottom": list(reversed(global_ranked[-top_limit:])),
        "settings_by_experiment": dict(sorted(settings_by_experiment.items())),
        "setting_effects": setting_effects,
        "mass_barrage_portfolios": portfolio_comparison,
        "fertilizer_omission_impact": omission_impact,
    }


def _fmt(value: float, digits: int = 3) -> str:
    if abs(value) < 0.5 * (10 ** -digits):
        return f"{0.0:.{digits}f}"
    return f"{value:.{digits}f}"


def write_markdown_report(analysis: dict[str, Any], path: Path) -> None:
    meta = analysis["meta"]
    lines = [
        "# Solver Matrix Analysis",
        "",
        "Status: generated benchmark report. Lower scores are better; deltas are paired against the canonical baseline for the same target profile.",
        "",
        "## Run Contract",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Completed rows | {int(meta.get('summary_total_runs') or 0):,} |",
        f"| Failed rows | {int(meta.get('summary_failed_runs') or 0):,} |",
        f"| Target profiles | {len(meta.get('profiles', []))} |",
        f"| Primary allowed fertilizers | {len(meta.get('allowed_fertilizers', []))} |",
        f"| Nitrogen objective | `{meta['solver_baseline'].get('nitrogen_objective_mode')}` |",
        f"| Elemental S objective | `{str(meta['solver_baseline'].get('s_objective_enabled')).lower()}` |",
        "",
    ]
    unresolved = meta.get("unresolved_profiles") or []
    if unresolved:
        lines.extend(["Unresolved requested profiles:", ""])
        for item in unresolved:
            lines.append(f"- `{item.get('id')}` — {item.get('reason')}")
        lines.append("")

    lines.extend(
        [
            "## Canonical Baseline",
            "",
            "| Profile | Group | Score | Macro | Micro | Worst target | Worst score |",
            "|---|---|---:|---:|---:|---|---:|",
        ]
    )
    for profile_id, row in analysis["baseline_by_profile"].items():
        lines.append(
            f"| `{profile_id}` | {row['profile_group']} | {_fmt(row['score'])} | "
            f"{_fmt(row['macro_score'])} | {_fmt(row['micro_score'])} | "
            f"`{row['max_error_key']}` | {_fmt(row['max_error_score'])} |"
        )

    lines.extend(
        [
            "",
            "## Best Setting By Profile",
            "",
            "| Profile | Score | Improvement from baseline | Experiment | Configuration |",
            "|---|---:|---:|---|---|",
        ]
    )
    for profile_id, row in analysis["best_setting_by_profile"].items():
        baseline = analysis["baseline_by_profile"][profile_id]["score"]
        improvement = ((baseline - row["score"]) / baseline * 100.0) if baseline else 0.0
        lines.append(
            f"| `{profile_id}` | {_fmt(row['score'])} | {_fmt(improvement)}% | "
            f"`{row['experiment_id']}` | `{row['config_name']}` |"
        )

    lines.extend(
        [
            "",
            "## Best Setting Configurations",
            "",
            "| Rank | Experiment | Average delta | Improvement | Wins / ties / losses | Runtime ms | Configuration |",
            "|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    for index, row in enumerate(analysis["settings_global_top"][:15], start=1):
        lines.append(
            f"| {index} | `{row['experiment_id']}` | {_fmt(row['avg_delta'])} | "
            f"{_fmt(row['avg_improvement_percent'])}% | {row['wins']} / {row['ties']} / {row['losses']} | "
            f"{_fmt(row['avg_elapsed_seconds'] * 1000.0, 2)} | `{row['config_name']}` |"
        )

    lines.extend(["", "## Controlled Setting Effects", ""])
    for experiment_id, parameters in analysis["setting_effects"].items():
        lines.extend([f"### `{experiment_id}`", ""])
        for parameter, rows in parameters.items():
            lines.extend(
                [
                    f"#### `{parameter}`",
                    "",
                    "| Value | Average delta | Improvement | Wins / ties / losses | Runtime ms |",
                    "|---|---:|---:|---:|---:|",
                ]
            )
            for row in rows:
                lines.append(
                    f"| `{_json(row['value'])}` | {_fmt(row['avg_delta'])} | "
                    f"{_fmt(row['avg_improvement_percent'])}% | {row['wins']} / {row['ties']} / {row['losses']} | "
                    f"{_fmt(row['avg_elapsed_seconds'] * 1000.0, 2)} |"
                )
            lines.append("")

    if analysis["mass_barrage_portfolios"]:
        lines.extend(
            [
                "## Nutrient-Portfolio Mass Barrage",
                "",
                "| Portfolio | Products | Average delta | Improvement | Wins / ties / losses |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for row in analysis["mass_barrage_portfolios"]:
            lines.append(
                f"| `{row['portfolio_id']}` | {row['product_count']} | {_fmt(row['avg_delta'])} | "
                f"{_fmt(row['avg_improvement_percent'])}% | {row['wins']} / {row['ties']} / {row['losses']} |"
            )

        lines.extend(
            [
                "",
                "### Leave-One-Out Fertilizer Impact",
                "",
                "Positive deltas mean removing the fertilizer worsened the solver score.",
                "",
                "| Fertilizer omitted | Average delta | Wins / ties / losses |",
                "|---|---:|---:|",
            ]
        )
        for row in analysis["fertilizer_omission_impact"]:
            lines.append(
                f"| `{row['fertilizer']}` | {_fmt(row['avg_delta'])} | "
                f"{row['wins']} / {row['ties']} / {row['losses']} |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze schema-v2 solver matrix output.")
    parser.add_argument("run_dir", type=Path, help="Directory containing results, summary, and manifest files.")
    parser.add_argument("--out-json", type=Path, default=None, help="Analysis JSON output path.")
    parser.add_argument("--out-md", type=Path, default=None, help="Markdown report output path.")
    parser.add_argument("--top", type=int, default=30, help="Number of ranked configurations to retain.")
    parser.add_argument("--no-markdown", action="store_true", help="Only write JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = args.run_dir
    out_json = args.out_json or run_dir / "analysis_summary.json"
    out_md = args.out_md or run_dir / "analysis_report.md"
    analysis = analyze_run(run_dir, top_limit=args.top)
    out_json.write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Analysis JSON: {out_json}")
    if not args.no_markdown:
        write_markdown_report(analysis, out_md)
        print(f"Analysis Markdown: {out_md}")
    print(f"Analyzed rows: {sum(analysis['counts']['status'].values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
