from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import yaml


@dataclass(frozen=True)
class Fertilizer:
    name: str
    form: str
    weight_factor: float
    # composition fractions (mass fraction, e.g. 0.14 = 14%)
    comp: Dict[str, float]


def repo_root() -> Path:
    # this file lives in .../src/horticalc/data_io.py
    return Path(__file__).resolve().parents[2]


def load_fertilizers(csv_path: Path | None = None) -> Dict[str, Fertilizer]:
    if csv_path is None:
        csv_path = repo_root() / "data" / "fertilizers.csv"

    ferts: Dict[str, Fertilizer] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Düngername") or "").strip()
            if not name:
                continue
            form = (row.get("Form") or "").strip() or "fest"
            weight = float(row.get("Gewicht") or 1.0)

            comp: Dict[str, float] = {}
            for k, v in row.items():
                if k in ("NR", "Düngername", "Form", "Gewicht"):
                    continue
                if v is None or str(v).strip() == "":
                    continue
                try:
                    comp[k] = float(v)
                except ValueError:
                    # ignore text columns
                    continue

            ferts[name] = Fertilizer(name=name, form=form, weight_factor=weight, comp=comp)

    return ferts


def load_molar_masses(path: Path | None = None) -> Dict[str, float]:
    if path is None:
        path = repo_root() / "data" / "molar_masses.yml"
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): float(v) for k, v in data.items()}


def load_water_profile(path: Path) -> Dict[str, float]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # schema: {name, source, mg_per_l:{...}}
    mp = data.get("mg_per_l") or {}
    return {str(k): float(v) for k, v in mp.items()}


def load_water_profile_data(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    mp = data.get("mg_per_l") or {}
    return {
        "name": data.get("name") or path.stem,
        "source": data.get("source") or "",
        "mg_per_l": {str(k): float(v) for k, v in mp.items()},
        "osmosis_percent": float(data.get("osmosis_percent") or 0),
    }


def save_water_profile(
    path: Path,
    name: str,
    source: str,
    mg_per_l: Dict[str, float],
    osmosis_percent: float = 0,
) -> None:
    payload = {
        "name": name,
        "source": source,
        "mg_per_l": {str(k): float(v) for k, v in mg_per_l.items()},
        "osmosis_percent": float(osmosis_percent),
    }
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=True, allow_unicode=True)


def load_recipe(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def load_nutrient_solution_data(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    targets = data.get("targets_mg_per_l") or {}
    target_weights = data.get("target_weights") or {}
    return {
        "name": data.get("name") or path.stem,
        "source": data.get("source") or "",
        "targets_mg_per_l": {str(k): float(v) for k, v in targets.items()},
        "target_weights": {str(k): float(v) for k, v in target_weights.items()},
    }


def save_nutrient_solution(
    path: Path,
    name: str,
    source: str,
    targets_mg_per_l: Dict[str, float],
    target_weights: Dict[str, float] | None = None,
) -> None:
    payload = {
        "name": name,
        "source": source,
        "targets_mg_per_l": {str(k): float(v) for k, v in targets_mg_per_l.items()},
    }
    if target_weights:
        payload["target_weights"] = {str(k): float(v) for k, v in target_weights.items()}
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=True, allow_unicode=True)


def save_recipe(path: Path, data: dict) -> None:
    payload = dict(data)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=True, allow_unicode=True)
