from __future__ import annotations

import csv
import io
import json
import logging
import math
import os
import re
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

import yaml

from . import paths
from .nutrient_profiles import normalize_nutrient_solution_data
from .validation import finite_float as _finite_float
from .validation import non_negative_float as _non_negative_float
from .validation import percentage_float as _percentage_float
from .validation import positive_float as _positive_float

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Fertilizer:
    name: str
    liquid: bool
    weight_factor: float
    # composition fractions (mass fraction, e.g. 0.14 = 14%)
    comp: Dict[str, float]
    solver_max_dose_per_l: float | None = None


FERTILIZER_NAME_FIELDS = ("Düngername", "Duengername")
FERTILIZER_BASE_FIELDS = ["Düngername", "Liquid", "Gewicht"]
FERTILIZER_SOLVER_MAX_FIELD = "SolverMaxDosePerL"
# Removed catalog metadata is discarded when an older user CSV is saved.
OBSOLETE_FERTILIZER_FIELDS = {"SolverRole"}
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
    return _is_number_field(field) or field in (
        *FERTILIZER_NAME_FIELDS,
        "Form",
        "Liquid",
        "Gewicht",
        FERTILIZER_SOLVER_MAX_FIELD,
        *OBSOLETE_FERTILIZER_FIELDS,
    )


def _fertilizer_is_liquid(row: dict[str, str | None]) -> bool:
    liquid = str(row.get("Liquid") or "").strip().casefold()
    if liquid == "1":
        return True
    if liquid == "0":
        return False
    raise ValueError(f"Liquid must be 0 or 1: {row.get('Liquid')}")


def _legacy_fertilizer_is_liquid(row: dict[str, str | None]) -> bool:
    if "Liquid" in row:
        return _fertilizer_is_liquid(row)
    form = str(row.get("Form") or "").strip().casefold()
    return form in {"flüssig", "fluessig", "liquid"}


def _fertilizer_name_from_row(row: dict[str, str | None]) -> str:
    for field in FERTILIZER_NAME_FIELDS:
        value = row.get(field)
        if value and value.strip():
            return value.strip()
    return ""


def _require_finite_numbers(value: Any, location: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{location} must contain only finite numbers")
    if isinstance(value, dict):
        for key, item in value.items():
            _require_finite_numbers(item, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _require_finite_numbers(item, f"{location}[{index}]")


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    _require_finite_numbers(payload, str(path))
    return payload


def _atomic_write_text(path: Path, content: str, *, newline: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline=newline,
            delete=False,
            dir=path.parent,
            prefix=f".{path.name}.tmp-",
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            with suppress(OSError):
                temp_path.unlink(missing_ok=True)


def _save_yaml(path: Path, payload: dict) -> None:
    _require_finite_numbers(payload, str(path))
    content = yaml.safe_dump(payload, sort_keys=True, allow_unicode=True)
    _atomic_write_text(path, content)


def load_user_preferences() -> dict[str, Any]:
    preference_path = paths.user_preferences_path()
    if not preference_path.exists():
        return {}
    try:
        payload = json.loads(preference_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Ignoring invalid preferences file %s: %s", preference_path, exc)
        return {}
    if not isinstance(payload, dict):
        logger.warning("Ignoring invalid preferences file %s: expected a JSON object", preference_path)
        return {}
    try:
        _require_finite_numbers(payload, str(preference_path))
    except ValueError as exc:
        logger.warning("Ignoring invalid preferences file %s: %s", preference_path, exc)
        return {}
    return {str(key): value for key, value in payload.items()}


def save_user_preferences(payload: dict[str, Any]) -> None:
    preference_path = paths.user_preferences_path()
    if not isinstance(payload, dict):
        raise ValueError("Preferences must be a JSON object")
    _require_finite_numbers(payload, str(preference_path))
    _atomic_write_text(
        preference_path,
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    )


def _float_mapping(
    data: dict,
    location: str,
    validate_value: Callable[[Any, str], float] = _finite_float,
) -> Dict[str, float]:
    if not isinstance(data, dict):
        raise ValueError(f"{location} must be a mapping")
    return {str(key): validate_value(value, f"{location}.{key}") for key, value in data.items()}


def _load_fertilizer_csv(
    csv_path: Path,
    *,
    allow_legacy_schema: bool = False,
) -> Dict[str, Fertilizer]:
    ferts: Dict[str, Fertilizer] = {}
    seen_names: set[str] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        if not fields.intersection(FERTILIZER_NAME_FIELDS):
            raise ValueError("Fertilizer CSV requires Düngername or Duengername")
        required_fields = ("Gewicht",) if allow_legacy_schema else ("Liquid", "Gewicht")
        for required_field in required_fields:
            if required_field not in fields:
                raise ValueError(f"Fertilizer CSV requires {required_field}")
        for row in reader:
            name = _fertilizer_name_from_row(row)
            if not name:
                continue
            name_key = fertilizer_name_key(name)
            if name_key in seen_names:
                raise ValueError(f"{csv_path}: duplicate fertilizer name: {name}")
            seen_names.add(name_key)
            liquid = _legacy_fertilizer_is_liquid(row) if allow_legacy_schema else _fertilizer_is_liquid(row)
            weight = _positive_float(
                row.get("Gewicht") or 1.0,
                f"{csv_path}: Gewicht for {name}",
            )
            raw_solver_max = row.get(FERTILIZER_SOLVER_MAX_FIELD)
            solver_max = None
            if raw_solver_max is not None and str(raw_solver_max).strip() != "":
                solver_max = _finite_float(
                    raw_solver_max,
                    f"{csv_path}: {FERTILIZER_SOLVER_MAX_FIELD} for {name}",
                )
                if solver_max < 0.0:
                    raise ValueError(f"{csv_path}: {FERTILIZER_SOLVER_MAX_FIELD} for {name} must be >= 0")
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
                if not math.isfinite(value):
                    raise ValueError(f"{csv_path}: {k} for {name} must be finite")
                if value == 0:
                    continue
                comp[k] = value

            ferts[name] = Fertilizer(
                name=name,
                liquid=liquid,
                weight_factor=weight,
                comp=comp,
                solver_max_dose_per_l=solver_max,
            )

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


def _sorted_fertilizer_map(fertilizers: Dict[str, Fertilizer]) -> Dict[str, Fertilizer]:
    return dict(sorted(fertilizers.items(), key=lambda item: fertilizer_name_key(item[0])))


def _disabled_fertilizer_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        fertilizer_name_key(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _fertilizers_equal(left: Fertilizer, right: Fertilizer) -> bool:
    if left.liquid != right.liquid:
        return False
    if abs(float(left.weight_factor) - float(right.weight_factor)) > 1e-12:
        return False
    if left.solver_max_dose_per_l != right.solver_max_dose_per_l:
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
    content = "\n".join(sorted(names, key=str.casefold)) + "\n"
    _atomic_write_text(path, content)


def _restore_text_file(path: Path, previous_content: str | None) -> None:
    if previous_content is None:
        path.unlink(missing_ok=True)
    else:
        _atomic_write_text(path, previous_content, newline="")


def _migrate_legacy_user_fertilizers(root: Path) -> None:
    legacy_path = paths.user_fertilizers_path(root)
    overrides_path = paths.user_fertilizer_overrides_path(root)
    disabled_path = paths.user_disabled_fertilizers_path(root)
    if not legacy_path.exists() or overrides_path.exists() or disabled_path.exists():
        return

    legacy_fertilizers = _load_fertilizer_csv(legacy_path, allow_legacy_schema=True)
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
        return _sorted_fertilizer_map(_load_fertilizer_csv(csv_path))

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
    return _sorted_fertilizer_map(merged)


def _header_for_fertilizers(fertilizers: Dict[str, Fertilizer], existing_header: list[str] | None = None) -> list[str]:
    header = [field for field in existing_header if not _is_number_field(field)] if existing_header else None
    if header is not None:
        header = [field for field in header if field != "Form" and field not in OBSOLETE_FERTILIZER_FIELDS]
    if header is not None and "Liquid" not in header:
        weight_index = header.index("Gewicht") if "Gewicht" in header else len(header)
        header.insert(weight_index, "Liquid")
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
    if FERTILIZER_SOLVER_MAX_FIELD in header:
        header.remove(FERTILIZER_SOLVER_MAX_FIELD)
    header.append(FERTILIZER_SOLVER_MAX_FIELD)
    return header


def _validate_fertilizer(fertilizer: Fertilizer) -> None:
    _positive_float(fertilizer.weight_factor, f"Weight for {fertilizer.name}")
    for key, value in fertilizer.comp.items():
        _finite_float(value, f"Composition {key} for {fertilizer.name}")
    if fertilizer.solver_max_dose_per_l is not None:
        maximum = _finite_float(
            fertilizer.solver_max_dose_per_l,
            f"Solver maximum for {fertilizer.name}",
        )
        if maximum < 0.0:
            raise ValueError(f"Solver maximum for {fertilizer.name} must be >= 0")


def _write_fertilizer_csv(
    fertilizers: Dict[str, Fertilizer],
    csv_path: Path,
    existing_header: list[str] | None = None,
) -> None:
    header = _header_for_fertilizers(fertilizers, existing_header)
    name_field = next((field for field in header if field in FERTILIZER_NAME_FIELDS), "Düngername")

    sorted_ferts = sorted(fertilizers.values(), key=lambda fert: fertilizer_name_key(fert.name))

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=header)
    writer.writeheader()
    for fert in sorted_ferts:
        _validate_fertilizer(fert)
        weight = float(fert.weight_factor)
        row = dict.fromkeys(header, "")
        row[name_field] = fert.name
        row["Liquid"] = "1" if fert.liquid else "0"
        row["Gewicht"] = format(weight, ".10g")
        if fert.solver_max_dose_per_l is not None:
            row[FERTILIZER_SOLVER_MAX_FIELD] = format(float(fert.solver_max_dose_per_l), ".10g")
        for key in header:
            if _is_base_fertilizer_field(key):
                continue
            value = fert.comp.get(key)
            if value is None:
                continue
            row[key] = format(value, ".10g")
        writer.writerow(row)
    _atomic_write_text(csv_path, output.getvalue(), newline="")


def _read_csv_header(csv_path: Path) -> list[str] | None:
    if not csv_path.exists():
        return None
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames) if reader.fieldnames else None


def _fertilizer_overlay_changes(
    shipped: Dict[str, Fertilizer],
    incoming: Dict[str, Fertilizer],
) -> tuple[Dict[str, Fertilizer], list[str]]:
    shipped_by_key = {_fertilizer_key(fert): fert for fert in shipped.values()}
    incoming_by_key = {_fertilizer_key(fert): fert for fert in incoming.values()}
    overrides = {
        fert.name: fert
        for key, fert in incoming_by_key.items()
        if key not in shipped_by_key or not _fertilizers_equal(fert, shipped_by_key[key])
    }
    disabled = [shipped_fert.name for key, shipped_fert in shipped_by_key.items() if key not in incoming_by_key]
    return overrides, disabled


def save_fertilizers(
    fertilizers: Dict[str, Fertilizer],
    csv_path: Path | None = None,
) -> None:
    for fertilizer in fertilizers.values():
        _validate_fertilizer(fertilizer)

    header: list[str] | None = None
    if csv_path is None:
        layout = paths.ensure_portable_layout()
        _migrate_legacy_user_fertilizers(layout.root)
        shipped_path = paths.shipped_fertilizers_path(layout.root)
        shipped = _load_fertilizer_csv(shipped_path) if shipped_path.exists() else {}
        overrides, disabled = _fertilizer_overlay_changes(shipped, fertilizers)

        overrides_path = paths.user_fertilizer_overrides_path(layout.root)
        previous_overrides = overrides_path.read_text(encoding="utf-8") if overrides_path.exists() else None
        if overrides:
            header = _read_csv_header(shipped_path)
            existing_header = _read_csv_header(overrides_path)
            if header is None:
                header = existing_header
            elif existing_header:
                header.extend(field for field in existing_header if field not in header)
            _write_fertilizer_csv(overrides, overrides_path, header)
        else:
            overrides_path.unlink(missing_ok=True)
        try:
            _write_disabled_fertilizers(
                disabled,
                paths.user_disabled_fertilizers_path(layout.root),
            )
        except Exception:
            try:
                _restore_text_file(overrides_path, previous_overrides)
            except OSError:
                logger.exception("Failed to restore fertilizer overrides after overlay save failure")
            raise
        return

    header = _read_csv_header(csv_path)

    _write_fertilizer_csv(fertilizers, csv_path, header)


def load_molar_masses(path: Path | None = None) -> Dict[str, float]:
    if path is None:
        path = paths.app_root() / "data" / "molar_masses.yml"
    data = _load_yaml(path)
    return _float_mapping(data, f"{path}: molar masses", _positive_float)


def load_water_profile_data(path: Path) -> dict:
    data = _load_yaml(path)
    raw_mg_per_l = data.get("mg_per_l")
    mp = _float_mapping(
        {} if raw_mg_per_l is None else raw_mg_per_l,
        f"{path}: mg_per_l",
        _non_negative_float,
    )
    raw_osmosis_percent = data.get("osmosis_percent")
    return {
        "name": data.get("name") or path.stem,
        "source": data.get("source") or "",
        "mg_per_l": mp,
        "osmosis_percent": _percentage_float(
            0 if raw_osmosis_percent is None else raw_osmosis_percent,
            f"{path}: osmosis_percent",
        ),
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
        "mg_per_l": _float_mapping(mg_per_l, f"{path}: mg_per_l", _non_negative_float),
        "osmosis_percent": _percentage_float(osmosis_percent, f"{path}: osmosis_percent"),
    }
    _save_yaml(path, payload)


def load_recipe(path: Path) -> dict:
    return _load_yaml(path)


def load_nutrient_solution_data(path: Path) -> dict:
    return normalize_nutrient_solution_data(
        _load_yaml(path),
        location=str(path),
        fallback_name=path.stem,
    )


def save_nutrient_solution(
    path: Path,
    name: str,
    source: str,
    targets_mg_per_l: Dict[str, float],
    liters: float | None = None,
    water_profile: str | None = None,
    osmosis_percent: float | None = None,
    fertilizers_allowed: list[str] | None = None,
    fixed_grams: Dict[str, float] | None = None,
    urea_as_nh4: bool | None = None,
    solver_config: Dict[str, object] | None = None,
) -> None:
    raw_payload = {
        "name": name,
        "source": source,
        "targets_mg_per_l": targets_mg_per_l,
    }
    if liters is not None:
        raw_payload["liters"] = liters
    if water_profile is not None:
        raw_payload["water_profile"] = water_profile
    if osmosis_percent is not None:
        raw_payload["osmosis_percent"] = osmosis_percent
    if fertilizers_allowed is not None:
        raw_payload["fertilizers_allowed"] = fertilizers_allowed
    if fixed_grams is not None:
        raw_payload["fixed_grams"] = fixed_grams
    if urea_as_nh4 is not None:
        raw_payload["urea_as_nh4"] = urea_as_nh4
    if solver_config is not None:
        raw_payload["solver_config"] = solver_config
    payload = normalize_nutrient_solution_data(raw_payload, location=str(path))
    _save_yaml(path, payload)


def save_recipe(path: Path, data: dict) -> None:
    _save_yaml(path, dict(data))
