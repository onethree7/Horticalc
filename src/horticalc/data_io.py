from __future__ import annotations

import csv
import os
import re
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


FERTILIZER_NAME_FIELDS = ("Düngername", "Duengername")
FERTILIZER_BASE_FIELDS = ["NR", "Düngername", "Form", "Gewicht"]
REPLACED_ROW_PATTERN = re.compile(r'replace existing row\s+"([^"]+)"', re.IGNORECASE)


def fertilizer_name_key(name: str) -> str:
    return " ".join(str(name).split()).casefold()


def _fertilizer_key(fertilizer: Fertilizer) -> str:
    return fertilizer_name_key(fertilizer.name)


def _is_number_field(field: str | None) -> bool:
    if field is None:
        return False
    return field.strip().rstrip(".").casefold() == "nr"


def _is_base_fertilizer_field(field: str | None) -> bool:
    if field is None:
        return False
    return _is_number_field(field) or field in (*FERTILIZER_NAME_FIELDS, "Form", "Gewicht")


def _fertilizer_name_from_row(row: dict[str, str | None]) -> str:
    for field in FERTILIZER_NAME_FIELDS:
        value = row.get(field)
        if value and value.strip():
            return value.strip()
    return ""


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _float_mapping(data: dict) -> Dict[str, float]:
    return {str(k): float(v) for k, v in data.items()}


def _load_fertilizer_csv(csv_path: Path) -> Dict[str, Fertilizer]:
    ferts: Dict[str, Fertilizer] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = _fertilizer_name_from_row(row)
            if not name:
                continue
            form = (row.get("Form") or "").strip() or "fest"
            weight = float(row.get("Gewicht") or 1.0)

            comp: Dict[str, float] = {}
            for k, v in row.items():
                if _is_base_fertilizer_field(k):
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


def _shipped_fertilizer_catalog_keys(csv_path: Path) -> set[str]:
    keys: set[str] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = _fertilizer_name_from_row(row)
            if name:
                keys.add(fertilizer_name_key(name))
            for value in row.values():
                if not value:
                    continue
                keys.update(fertilizer_name_key(match) for match in REPLACED_ROW_PATTERN.findall(value))
    return keys


def _merge_fertilizer_maps(*maps: Dict[str, Fertilizer]) -> Dict[str, Fertilizer]:
    merged_by_key: dict[str, Fertilizer] = {}
    for fertilizers in maps:
        for fertilizer in fertilizers.values():
            merged_by_key[_fertilizer_key(fertilizer)] = fertilizer
    return {fertilizer.name: fertilizer for fertilizer in merged_by_key.values()}


def _disabled_fertilizer_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        fertilizer_name_key(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _fertilizers_equal(left: Fertilizer, right: Fertilizer) -> bool:
    if left.form != right.form:
        return False
    if abs(float(left.weight_factor) - float(right.weight_factor)) > 1e-12:
        return False
    if set(left.comp) != set(right.comp):
        return False
    return all(abs(float(left.comp[key]) - float(right.comp[key])) <= 1e-12 for key in left.comp)


def _backup_path(path: Path) -> Path:
    candidate = path.with_suffix(f"{path.suffix}.legacy-backup")
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = path.with_suffix(f"{path.suffix}.legacy-backup-{index}")
        if not candidate.exists():
            return candidate
        index += 1


def _write_disabled_fertilizers(names: list[str], path: Path) -> None:
    if not names:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text("\n".join(sorted(names, key=str.casefold)) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def _migrate_legacy_user_fertilizers(root: Path) -> None:
    legacy_path = paths.user_fertilizers_path(root)
    overrides_path = paths.user_fertilizer_overrides_path(root)
    disabled_path = paths.user_disabled_fertilizers_path(root)
    if not legacy_path.exists() or overrides_path.exists() or disabled_path.exists():
        return

    legacy_fertilizers = _load_fertilizer_csv(legacy_path)
    shipped_path = paths.shipped_fertilizers_path(root)
    shipped_keys = _shipped_fertilizer_catalog_keys(shipped_path) if shipped_path.exists() else set()
    custom_fertilizers = {
        name: fertilizer
        for name, fertilizer in legacy_fertilizers.items()
        if fertilizer_name_key(name) not in shipped_keys
    }
    if custom_fertilizers:
        _write_fertilizer_csv(custom_fertilizers, overrides_path)
    legacy_path.replace(_backup_path(legacy_path))


def load_fertilizers(csv_path: Path | None = None) -> Dict[str, Fertilizer]:
    if csv_path is not None:
        return _load_fertilizer_csv(csv_path)

    layout = paths.ensure_portable_layout()
    _migrate_legacy_user_fertilizers(layout.root)

    shipped_path = paths.shipped_fertilizers_path(layout.root)
    shipped = _load_fertilizer_csv(shipped_path) if shipped_path.exists() else {}
    overrides_path = paths.user_fertilizer_overrides_path(layout.root)
    overrides = _load_fertilizer_csv(overrides_path) if overrides_path.exists() else {}
    merged = _merge_fertilizer_maps(shipped, overrides)

    disabled_keys = _disabled_fertilizer_keys(paths.user_disabled_fertilizers_path(layout.root))
    if disabled_keys:
        merged = {name: fert for name, fert in merged.items() if _fertilizer_key(fert) not in disabled_keys}
    return merged


def _header_for_fertilizers(fertilizers: Dict[str, Fertilizer], existing_header: list[str] | None = None) -> list[str]:
    header = list(existing_header) if existing_header else None
    comp_keys = set()
    for fert in fertilizers.values():
        comp_keys.update(fert.comp.keys())
    if header is None:
        header = FERTILIZER_BASE_FIELDS + sorted(comp_keys)
    else:
        for key in sorted(comp_keys):
            if key not in header:
                header.append(key)
    if not any(field in header for field in FERTILIZER_NAME_FIELDS):
        header.insert(1, "Düngername")
    return header


def _write_fertilizer_csv(
    fertilizers: Dict[str, Fertilizer],
    csv_path: Path,
    existing_header: list[str] | None = None,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    header = _header_for_fertilizers(fertilizers, existing_header)
    number_field = next((field for field in header if _is_number_field(field)), None)
    name_field = next((field for field in header if field in FERTILIZER_NAME_FIELDS), "Düngername")

    sorted_ferts = sorted(fertilizers.values(), key=lambda fert: fertilizer_name_key(fert.name))

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for index, fert in enumerate(sorted_ferts, start=1):
            row = {key: "" for key in header}
            if number_field:
                row[number_field] = str(index)
            row[name_field] = fert.name
            row["Form"] = fert.form or "fest"
            row["Gewicht"] = format(fert.weight_factor or 1.0, ".10g")
            for key in header:
                if _is_base_fertilizer_field(key):
                    continue
                value = fert.comp.get(key)
                if value is None:
                    continue
                row[key] = format(value, ".10g")
            writer.writerow(row)


def save_fertilizers(
    fertilizers: Dict[str, Fertilizer],
    csv_path: Path | None = None,
) -> None:
    header: list[str] | None = None
    if csv_path is None:
        layout = paths.ensure_portable_layout()
        _migrate_legacy_user_fertilizers(layout.root)
        shipped_path = paths.shipped_fertilizers_path(layout.root)
        shipped = _load_fertilizer_csv(shipped_path) if shipped_path.exists() else {}
        shipped_by_key = {_fertilizer_key(fert): fert for fert in shipped.values()}
        incoming_by_key = {_fertilizer_key(fert): fert for fert in fertilizers.values()}

        overrides = {
            fert.name: fert
            for key, fert in incoming_by_key.items()
            if key not in shipped_by_key or not _fertilizers_equal(fert, shipped_by_key[key])
        }
        disabled = [
            shipped_fert.name
            for key, shipped_fert in shipped_by_key.items()
            if key not in incoming_by_key
        ]

        overrides_path = paths.user_fertilizer_overrides_path(layout.root)
        if overrides:
            if overrides_path.exists():
                with overrides_path.open("r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        header = list(reader.fieldnames)
            _write_fertilizer_csv(overrides, overrides_path, header)
        else:
            overrides_path.unlink(missing_ok=True)
        _write_disabled_fertilizers(disabled, paths.user_disabled_fertilizers_path(layout.root))
        return

    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                header = list(reader.fieldnames)

    _write_fertilizer_csv(fertilizers, csv_path, header)


def load_molar_masses(path: Path | None = None) -> Dict[str, float]:
    if path is None:
        path = paths.app_root() / "data" / "molar_masses.yml"
    data = _load_yaml(path)
    return _float_mapping(data)


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
