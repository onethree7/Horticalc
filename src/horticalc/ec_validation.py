from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
from typing import Dict

from .ec import parse_ion_key


@dataclass(frozen=True)
class ECValidationConfig:
    enabled: bool = False
    engine: str = "pyeql"
    engine_variant: str = "native"
    temperature_c: float = 25.0
    ph: float = 7.0


def _load_pyeql() -> object | None:
    if importlib.util.find_spec("pyEQL") is None:
        return None
    return importlib.import_module("pyEQL")


def _ion_label_to_pyeql(label: str) -> str | None:
    try:
        canonical, _charge = parse_ion_key(label)
    except ValueError:
        return None

    if "^" in canonical:
        formula, rest = canonical.split("^")
        charge = rest[:-1]
        sign = rest[-1]
        return f"{formula}{sign}{charge}"

    sign = canonical[-1]
    if sign not in ("+", "-"):
        return canonical

    if canonical[-2].isdigit():
        charge = canonical[-2]
        formula = canonical[:-2]
        return f"{formula}{sign}{charge}"

    formula = canonical[:-1]
    return f"{formula}{sign}"


def validate_ec(
    ions_mmol_per_l: Dict[str, float],
    primary_ec: Dict[str, object],
    config: Dict[str, object] | None = None,
) -> Dict[str, object] | None:
    raw_config = config or {}
    cfg = ECValidationConfig(
        enabled=bool(raw_config.get("enabled", False)),
        engine=str(raw_config.get("engine", "pyeql")),
        engine_variant=str(raw_config.get("engine_variant", "native")),
        temperature_c=float(raw_config.get("temperature_c", 25.0)),
        ph=float(raw_config.get("ph", 7.0)),
    )

    if not cfg.enabled:
        return None

    if cfg.engine.lower() != "pyeql":
        return {
            "enabled": True,
            "status": "error",
            "engine": cfg.engine,
            "warnings": [f"Unbekannte EC-Validation-Engine: {cfg.engine}"],
        }

    pyeql = _load_pyeql()
    if pyeql is None:
        return {
            "enabled": True,
            "status": "error",
            "engine": cfg.engine,
            "warnings": ["Optionales Paket pyEQL ist nicht installiert."],
        }

    warnings: list[str] = []
    temp_key = f"{cfg.temperature_c:.1f}"
    temp_k = cfg.temperature_c + 273.15
    solution = pyeql.Solution(temperature=f"{temp_k} K", pH=cfg.ph, engine=cfg.engine_variant)

    for ion_label, mmol_per_l in ions_mmol_per_l.items():
        if mmol_per_l == 0:
            continue
        formula = _ion_label_to_pyeql(ion_label)
        if not formula:
            warnings.append(f"Ion '{ion_label}' konnte nicht für pyEQL übersetzt werden.")
            continue
        solution.add_solute(formula, f"{mmol_per_l} mmol/L")

    conductivity = solution.conductivity
    pyeql_ec_s_per_m = float(conductivity.to("S/m").magnitude)
    pyeql_ec_mS_per_cm = pyeql_ec_s_per_m * 10.0

    primary_ec_mS_per_cm = None
    ec_mS_per_cm = primary_ec.get("ec_mS_per_cm") if isinstance(primary_ec, dict) else None
    if isinstance(ec_mS_per_cm, dict) and temp_key in ec_mS_per_cm:
        primary_ec_mS_per_cm = float(ec_mS_per_cm[temp_key])
    elif isinstance(ec_mS_per_cm, dict) and ec_mS_per_cm:
        first_key = sorted(ec_mS_per_cm.keys())[0]
        primary_ec_mS_per_cm = float(ec_mS_per_cm[first_key])
        warnings.append(f"Temperatur {temp_key}°C nicht im EC; nutze {first_key}°C für Vergleich.")
    else:
        warnings.append("Kein primäres EC-Ergebnis zum Vergleich vorhanden.")

    delta_mS_per_cm = None
    if primary_ec_mS_per_cm is not None:
        delta_mS_per_cm = pyeql_ec_mS_per_cm - primary_ec_mS_per_cm

    return {
        "enabled": True,
        "status": "ok",
        "engine": cfg.engine,
        "engine_variant": cfg.engine_variant,
        "temperature_c": cfg.temperature_c,
        "ph": cfg.ph,
        "pyeql_ec_s_per_m": pyeql_ec_s_per_m,
        "pyeql_ec_mS_per_cm": pyeql_ec_mS_per_cm,
        "primary_ec_mS_per_cm": primary_ec_mS_per_cm,
        "delta_mS_per_cm": delta_mS_per_cm,
        "warnings": warnings,
    }
