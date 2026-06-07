from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from horticalc.solver_config import MATRIX_BOOLEAN_SOLVER_KEYS  # noqa: E402


@dataclass
class ScoreStats:
    count: int = 0
    total: float = 0.0
    minimum: float = math.inf
    maximum: float = -math.inf
    values: list[float] = field(default_factory=list)

    def add(self, value: float, *, keep_value: bool = False) -> None:
        if not math.isfinite(value):
            return
        self.count += 1
        self.total += value
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)
        if keep_value:
            self.values.append(value)

    @property
    def avg(self) -> float:
        return self.total / self.count if self.count else 0.0

    def percentile(self, fraction: float) -> float:
        if not self.values:
            return 0.0
        values = sorted(self.values)
        index = min(len(values) - 1, max(0, int(round((len(values) - 1) * fraction))))
        return values[index]

    def to_dict(self, *, percentiles: bool = False) -> dict[str, Any]:
        result = {
            "count": self.count,
            "avg": self.avg,
            "min": 0.0 if math.isinf(self.minimum) else self.minimum,
            "max": 0.0 if math.isinf(self.maximum) else self.maximum,
        }
        if percentiles:
            result.update(
                {
                    "p05": self.percentile(0.05),
                    "p50": self.percentile(0.50),
                    "p95": self.percentile(0.95),
                }
            )
        return result


def _set_csv_field_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = int(limit / 10)


def _loads(value: str, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _score(row: dict[str, str]) -> float:
    try:
        return float(row.get("composite_score") or math.inf)
    except ValueError:
        return math.inf


def _stat_bucket(mapping: dict[str, ScoreStats], key: str, value: float, *, keep_value: bool = False) -> None:
    mapping.setdefault(key, ScoreStats()).add(value, keep_value=keep_value)


def _compact_best_row(row: dict[str, str]) -> dict[str, Any]:
    solver_config = _loads(row.get("solver_config", ""), {})
    fertilizers_allowed = _loads(row.get("fertilizers_allowed", ""), [])
    used_fertilizers = _loads(row.get("used_fertilizers", ""), [])
    ignored_targets = _loads(row.get("ignored_targets", ""), {})
    return {
        "profile_id": row.get("profile_id", ""),
        "profile_name": row.get("profile_name", ""),
        "score": _score(row),
        "mode": row.get("nitrogen_objective_mode", ""),
        "phase": row.get("phase", ""),
        "config_name": row.get("config_name", ""),
        "solver_config": solver_config,
        "subset_size": int(row.get("subset_size") or 0),
        "macro_score": float(row.get("macro_score") or 0.0),
        "n_form_score": float(row.get("n_form_score") or 0.0),
        "micro_score": float(row.get("micro_score") or 0.0),
        "other_score": float(row.get("other_score") or 0.0),
        "ignored_score": float(row.get("ignored_score") or 0.0),
        "max_error_key": row.get("max_error_key", ""),
        "max_error_score": float(row.get("max_error_score") or 0.0),
        "total_grams": float(row.get("total_grams") or 0.0),
        "used_fertilizer_count": int(row.get("used_fertilizer_count") or 0),
        "fertilizers_allowed": fertilizers_allowed,
        "used_fertilizers": used_fertilizers,
        "ignored_keys": sorted(ignored_targets),
    }


def _top_stats(stats_by_key: dict[str, ScoreStats], *, limit: int, reverse: bool = False) -> list[dict[str, Any]]:
    rows = [
        {"key": key, **stats.to_dict()}
        for key, stats in stats_by_key.items()
        if stats.count
    ]
    rows.sort(key=lambda item: item["avg"], reverse=reverse)
    return rows[:limit]


def _stats_dict(stats_by_key: dict[str, ScoreStats], *, percentiles: bool = False) -> dict[str, dict[str, Any]]:
    return {key: stats.to_dict(percentiles=percentiles) for key, stats in sorted(stats_by_key.items())}


def analyze_run(run_dir: Path, *, baseline_dir: Path | None = None, top_limit: int = 30) -> dict[str, Any]:
    start = time.perf_counter()
    summary_path = run_dir / "summary.json"
    results_csv = run_dir / "results.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary.json in {run_dir}")
    if not results_csv.exists():
        raise FileNotFoundError(f"Missing results.csv in {run_dir}")

    _set_csv_field_limit()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    allowed_fertilizers = list(summary.get("allowed_fertilizers") or [])

    counts: dict[str, Counter[str]] = {
        "status": Counter(),
        "mode": Counter(),
        "phase": Counter(),
        "profiles": Counter(),
    }
    score_by_mode: dict[str, ScoreStats] = {}
    score_by_phase_mode: dict[str, ScoreStats] = {}
    profile_mode_stats: dict[str, dict[str, ScoreStats]] = defaultdict(dict)
    base_flag_effects: dict[str, dict[str, dict[str, ScoreStats]]] = defaultdict(
        lambda: defaultdict(lambda: {"true": ScoreStats(), "false": ScoreStats()})
    )
    config_base_stats: dict[str, ScoreStats] = {}
    subset_base_stats: dict[str, dict[str, ScoreStats]] = defaultdict(dict)
    fertilizer_stats: dict[str, dict[str, dict[str, ScoreStats]]] = defaultdict(
        lambda: {
            name: {"present": ScoreStats(), "absent": ScoreStats()}
            for name in allowed_fertilizers
        }
    )
    max_error_counts: dict[str, Any] = {
        "all": Counter(),
        "by_mode": defaultdict(Counter),
        "by_profile": defaultdict(Counter),
    }
    refine_mutation_stats: dict[str, ScoreStats] = {}
    best_by_profile: dict[str, dict[str, Any]] = {}

    with results_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            status = row.get("status", "")
            mode = row.get("nitrogen_objective_mode", "")
            phase = row.get("phase", "")
            profile_id = row.get("profile_id", "")
            counts["status"][status] += 1
            counts["mode"][mode] += 1
            counts["phase"][phase] += 1
            counts["profiles"][profile_id] += 1
            if status != "ok":
                continue

            score = _score(row)
            _stat_bucket(score_by_mode, mode, score, keep_value=True)
            _stat_bucket(score_by_phase_mode, f"{phase}|{mode}", score, keep_value=True)
            profile_mode_stats[profile_id].setdefault(mode, ScoreStats()).add(score)

            current = best_by_profile.get(profile_id)
            if current is None or score < float(current["score"]):
                best_by_profile[profile_id] = _compact_best_row(row)

            max_key = row.get("max_error_key", "")
            if max_key:
                max_error_counts["all"][max_key] += 1
                max_error_counts["by_mode"][mode][max_key] += 1
                max_error_counts["by_profile"][profile_id][max_key] += 1

            if phase == "base":
                solver_config = _loads(row.get("solver_config", ""), {})
                for key in MATRIX_BOOLEAN_SOLVER_KEYS:
                    value = "true" if bool(solver_config.get(key)) else "false"
                    base_flag_effects[mode][key][value].add(score)
                _stat_bucket(config_base_stats, row.get("config_name", ""), score)
                subset_size = row.get("subset_size", "0")
                subset_base_stats[mode].setdefault(subset_size, ScoreStats()).add(score)
                subset = set(_loads(row.get("fertilizers_allowed", ""), []))
                for fertilizer in allowed_fertilizers:
                    bucket = "present" if fertilizer in subset else "absent"
                    fertilizer_stats[mode][fertilizer][bucket].add(score)
            elif phase == "refine":
                config_name = row.get("config_name", "")
                mutation = config_name.split(";", 1)[1] if ";" in config_name else "(no mutation label)"
                _stat_bucket(refine_mutation_stats, mutation, score)

    best_counts = {
        "mode": Counter(row["mode"] for row in best_by_profile.values()),
        "phase": Counter(row["phase"] for row in best_by_profile.values()),
        "subset_size": Counter(str(row["subset_size"]) for row in best_by_profile.values()),
        "fertilizer": Counter(
            fertilizer
            for row in best_by_profile.values()
            for fertilizer in row["fertilizers_allowed"]
        ),
    }

    fertilizer_effect = {}
    for mode, by_fertilizer in fertilizer_stats.items():
        rows = []
        for fertilizer, buckets in by_fertilizer.items():
            present = buckets["present"]
            absent = buckets["absent"]
            rows.append(
                {
                    "fertilizer": fertilizer,
                    "present": present.to_dict(),
                    "absent": absent.to_dict(),
                    "omission_delta": absent.avg - present.avg if present.count and absent.count else None,
                }
            )
        rows.sort(key=lambda item: float("-inf") if item["omission_delta"] is None else -item["omission_delta"])
        fertilizer_effect[mode] = rows

    baseline_comparison = None
    if baseline_dir is not None:
        baseline_comparison = compare_best_profiles(
            baseline_dir / "summary.json",
            best_by_profile,
        )

    return {
        "meta": {
            "source_dir": str(run_dir),
            "source_csv": str(results_csv),
            "source_summary": str(summary_path),
            "elapsed_analysis_seconds": time.perf_counter() - start,
            "file_sizes": {
                "results.csv": results_csv.stat().st_size,
                "summary.json": summary_path.stat().st_size,
            },
            "summary_total_runs": summary.get("total_runs"),
            "summary_failed_runs": summary.get("failed_runs"),
            "allowed_fertilizers": allowed_fertilizers,
            "profiles": summary.get("profiles", []),
            "nitrogen_objective_modes": summary.get("nitrogen_objective_modes", []),
        },
        "counts": {key: dict(counter) for key, counter in counts.items()},
        "distributions": {
            "score_by_mode": _stats_dict(score_by_mode, percentiles=True),
            "score_by_phase_mode": _stats_dict(score_by_phase_mode, percentiles=True),
        },
        "profile_mode_stats": {
            profile: _stats_dict(stats)
            for profile, stats in sorted(profile_mode_stats.items())
        },
        "best_final_by_profile": dict(sorted(best_by_profile.items())),
        "best_counts": {
            key: dict(counter)
            for key, counter in best_counts.items()
        },
        "base_flag_effects_by_mode": {
            mode: {
                key: {state: stats.to_dict() for state, stats in states.items()}
                for key, states in by_key.items()
            }
            for mode, by_key in sorted(base_flag_effects.items())
        },
        "fair_base_config_top": _top_stats(config_base_stats, limit=top_limit),
        "fair_base_config_bottom": _top_stats(config_base_stats, limit=top_limit, reverse=True),
        "fertilizer_effect_base_by_mode": fertilizer_effect,
        "max_error_key": {
            "all": max_error_counts["all"].most_common(),
            "by_mode": {
                mode: counter.most_common()
                for mode, counter in sorted(max_error_counts["by_mode"].items())
            },
            "by_profile": {
                profile: counter.most_common()
                for profile, counter in sorted(max_error_counts["by_profile"].items())
            },
        },
        "subset_size_base_by_mode": {
            mode: _stats_dict(stats)
            for mode, stats in sorted(subset_base_stats.items())
        },
        "refine_mutation_top": _top_stats(refine_mutation_stats, limit=top_limit),
        "baseline_comparison": baseline_comparison,
    }


def compare_best_profiles(
    baseline_summary_path: Path,
    current_best_by_profile: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not baseline_summary_path.exists():
        raise FileNotFoundError(f"Missing baseline summary: {baseline_summary_path}")
    baseline = json.loads(baseline_summary_path.read_text(encoding="utf-8"))
    rows = []
    for profile_id, current in sorted(current_best_by_profile.items()):
        old = (baseline.get("best_by_profile") or {}).get(profile_id)
        if not old:
            continue
        old_score = float(old.get("composite_score", old.get("score", math.inf)))
        new_score = float(current["score"])
        improvement_percent = ((old_score - new_score) / old_score * 100.0) if old_score else 0.0
        rows.append(
            {
                "profile_id": profile_id,
                "baseline_score": old_score,
                "current_score": new_score,
                "improvement_percent": improvement_percent,
            }
        )
    avg_improvement = sum(row["improvement_percent"] for row in rows) / len(rows) if rows else 0.0
    return {
        "baseline_summary": str(baseline_summary_path),
        "rows": rows,
        "avg_improvement_percent": avg_improvement,
    }


def _fmt(value: float, digits: int = 3) -> str:
    if abs(value) < 1e-9:
        return "0.000"
    return f"{value:.{digits}f}"


def write_markdown_report(analysis: dict[str, Any], path: Path) -> None:
    mode_stats = analysis["distributions"]["score_by_mode"]
    best_by_profile = analysis["best_final_by_profile"]
    lines = [
        "# Solver Matrix Analysis",
        "",
        "Generated from solver-matrix output files. Lower scores are better.",
        "",
        "## Source",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Total rows | {analysis['meta'].get('summary_total_runs', 0):,} |",
        f"| Failed rows | {analysis['meta'].get('summary_failed_runs', 0):,} |",
        f"| Profiles | {len(analysis['meta'].get('profiles', []))} |",
        f"| Fertilizers | {len(analysis['meta'].get('allowed_fertilizers', []))} |",
        f"| Analysis seconds | {_fmt(float(analysis['meta'].get('elapsed_analysis_seconds', 0.0)), 1)} |",
        "",
        "## Nitrogen Modes",
        "",
        "| Mode | Rows | Avg | Median | P95 | Best |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode, stats in sorted(mode_stats.items()):
        lines.append(
            f"| `{mode}` | {stats['count']:,} | {_fmt(stats['avg'])} | "
            f"{_fmt(stats.get('p50', 0.0))} | {_fmt(stats.get('p95', 0.0))} | {_fmt(stats['min'])} |"
        )

    lines.extend(
        [
            "",
            "## Best Rows By Profile",
            "",
            "| Profile | Score | Mode | Phase | Subset | Macro | Micro | Worst key | Worst score |",
            "|---|---:|---|---|---:|---:|---:|---|---:|",
        ]
    )
    for profile_id, row in best_by_profile.items():
        lines.append(
            f"| `{profile_id}` | {_fmt(row['score'])} | `{row['mode']}` | `{row['phase']}` | "
            f"{row['subset_size']} | {_fmt(row['macro_score'])} | {_fmt(row['micro_score'])} | "
            f"`{row['max_error_key']}` | {_fmt(row['max_error_score'])} |"
        )

    lines.extend(
        [
            "",
            "## Top Fair Base Configurations",
            "",
            "| Rank | Avg score | Config |",
            "|---:|---:|---|",
        ]
    )
    for index, row in enumerate(analysis["fair_base_config_top"][:10], start=1):
        lines.append(f"| {index} | {_fmt(row['avg'])} | `{row['key']}` |")

    lines.extend(
        [
            "",
            "## Boolean Feature Effects",
            "",
        ]
    )
    for mode, features in analysis["base_flag_effects_by_mode"].items():
        lines.extend(
            [
                f"### `{mode}`",
                "",
                "| Feature | False avg | True avg | Better |",
                "|---|---:|---:|---|",
            ]
        )
        for feature, states in features.items():
            false_avg = float(states["false"]["avg"])
            true_avg = float(states["true"]["avg"])
            better = "true" if true_avg < false_avg else "false"
            lines.append(f"| `{feature}` | {_fmt(false_avg)} | {_fmt(true_avg)} | `{better}` |")
        lines.append("")

    lines.extend(
        [
            "## Fertilizer Omission Impact",
            "",
            "Positive omission delta means the score got worse when the fertilizer was absent.",
            "",
        ]
    )
    for mode, rows in analysis["fertilizer_effect_base_by_mode"].items():
        lines.extend(
            [
                f"### `{mode}`",
                "",
                "| Fertilizer | Omission delta | Present avg | Absent avg |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in rows:
            delta = row["omission_delta"]
            lines.append(
                f"| `{row['fertilizer']}` | {_fmt(float(delta or 0.0))} | "
                f"{_fmt(row['present']['avg'])} | {_fmt(row['absent']['avg'])} |"
            )
        lines.append("")

    comparison = analysis.get("baseline_comparison")
    if comparison:
        lines.extend(
            [
                "## Baseline Comparison",
                "",
                f"Baseline: `{comparison['baseline_summary']}`",
                "",
                "| Profile | Baseline | Current | Improvement |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in comparison["rows"]:
            lines.append(
                f"| `{row['profile_id']}` | {_fmt(row['baseline_score'])} | "
                f"{_fmt(row['current_score'])} | {row['improvement_percent']:.1f}% |"
            )
        lines.append("")
        lines.append(f"Average improvement: {comparison['avg_improvement_percent']:.1f}%")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze solver_matrix.py output directories.")
    parser.add_argument("run_dir", type=Path, help="Directory containing results.csv and summary.json.")
    parser.add_argument("--baseline-dir", type=Path, default=None, help="Optional prior run directory for comparison.")
    parser.add_argument("--out-json", type=Path, default=None, help="Analysis JSON output path.")
    parser.add_argument("--out-md", type=Path, default=None, help="Markdown report output path.")
    parser.add_argument("--top", type=int, default=30, help="Number of ranked rows to keep in top/bottom sections.")
    parser.add_argument("--no-markdown", action="store_true", help="Only write JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = args.run_dir
    out_json = args.out_json or run_dir / "analysis_summary.json"
    out_md = args.out_md or run_dir / "analysis_report.md"
    analysis = analyze_run(run_dir, baseline_dir=args.baseline_dir, top_limit=args.top)
    out_json.write_text(json.dumps(analysis, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Analysis JSON: {out_json}")
    if not args.no_markdown:
        write_markdown_report(analysis, out_md)
        print(f"Analysis Markdown: {out_md}")
    print(f"Analyzed rows: {sum(analysis['counts']['status'].values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
