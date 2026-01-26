from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import yaml

from . import paths

@dataclass(frozen=True)
class Fertilizer:
    name: str
    form: str
    weight_factor: float
    # composition fractions (mass fraction, e.g. 0.14 = 14%)
    comp: Dict[str, float]


def _is_number_field(field: str) -> bool:
    return field.strip().rstrip(".").casefold() == "nr"


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _float_mapping(data: dict) -> Dict[str, float]:
    return {str(k): float(v) for k, v in data.items()}


def load_fertilizers(csv_path: Path | None = None) -> Dict[str, Fertilizer]:
    if csv_path is None:
        csv_path = paths.ensure_portable_layout().fertilizers

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
                if _is_number_field(k) or k in ("Düngername", "Form", "Gewicht"):
                    continue
                if v is None or str(v).strip() == "":
                    continue
                try:
                    value = float(v)
                except ValueError:
                    # ignore text columns
                    continue
                if value == 0:
                    continue
                comp[k] = value

            ferts[name] = Fertilizer(name=name, form=form, weight_factor=weight, comp=comp)

    return ferts


def save_fertilizers(
    fertilizers: Dict[str, Fertilizer],
    csv_path: Path | None = None,
) -> None:
    if csv_path is None:
        csv_path = paths.user_fertilizers_path()
        csv_path.parent.mkdir(parents=True, exist_ok=True)

    header: list[str] | None = None
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                header = list(reader.fieldnames)

    if header is None:
        comp_keys = set()
        for fert in fertilizers.values():
            comp_keys.update(fert.comp.keys())
        header = ["NR", "Düngername", "Form", "Gewicht"] + sorted(comp_keys)
    number_field = next((field for field in header if _is_number_field(field)), None)

    sorted_ferts = sorted(fertilizers.values(), key=lambda fert: fert.name.casefold())

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for index, fert in enumerate(sorted_ferts, start=1):
            row = {key: "" for key in header}
            if number_field:
                row[number_field] = str(index)
            row["Düngername"] = fert.name
            row["Form"] = fert.form or "fest"
            row["Gewicht"] = format(fert.weight_factor or 1.0, ".10g")
            for key in header:
                if _is_number_field(key) or key in ("Düngername", "Form", "Gewicht"):
                    continue
                value = fert.comp.get(key)
                if value is None:
                    continue
                row[key] = format(value, ".10g")
            writer.writerow(row)


def load_molar_masses(path: Path | None = None) -> Dict[str, float]:
    if path is None:
        path = paths.app_root() / "data" / "molar_masses.yml"
    data = _load_yaml(path)
    return _float_mapping(data)


def load_water_profile(path: Path) -> Dict[str, float]:
    data = _load_yaml(path)
    # schema: {name, source, mg_per_l:{...}}
    mp = data.get("mg_per_l") or {}
    return _float_mapping(mp)


def load_water_profile_data(path: Path) -> dict:
    data = _load_yaml(path)
    mp = _float_mapping(data.get("mg_per_l") or {})
    return {
        "name": data.get("name") or path.stem,
        "source": data.get("source") or "",
        "mg_per_l": mp,
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
    return _load_yaml(path)


def load_nutrient_solution_data(path: Path) -> dict:
    data = _load_yaml(path)
    targets = _float_mapping(data.get("targets_mg_per_l") or {})
    return {
        "name": data.get("name") or path.stem,
        "source": data.get("source") or "",
        "targets_mg_per_l": targets,
    }


def save_nutrient_solution(
    path: Path,
    name: str,
    source: str,
    targets_mg_per_l: Dict[str, float],
) -> None:
    payload = {
        "name": name,
        "source": source,
        "targets_mg_per_l": {str(k): float(v) for k, v in targets_mg_per_l.items()},
    }
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=True, allow_unicode=True)


def save_recipe(path: Path, data: dict) -> None:
    payload = dict(data)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=True, allow_unicode=True)
