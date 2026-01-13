from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
from typing import Dict, Iterable


SUPPORTED_PYEQUION_ELEMENTS = {
    "C",
    "Ca",
    "Cl",
    "Na",
    "S",
    "Mg",
    "K",
    "N",
    "P",
    "Fe",
    "Mn",
    "Cu",
    "Zn",
}


@dataclass(frozen=True)
class SpeciationConfig:
    enabled: bool = False
    engine: str = "pyequion2"
    temperature_c: float = 25.0
    activity_model: str = "PITZER"
    precipitation_si_threshold: float = 0.0


def _build_element_balance(
    elements_mg_l: Dict[str, float],
    molar_masses: Dict[str, float],
) -> tuple[Dict[str, float], list[str]]:
    warnings: list[str] = []
    balance: Dict[str, float] = {}

    def add_element(element: str, mg_l: float) -> None:
        if mg_l <= 0:
            return
        if element not in molar_masses:
            warnings.append(f"Molmasse fehlt für Element '{element}'.")
            return
        molar_mass = float(molar_masses[element])
        if molar_mass <= 0:
            warnings.append(f"Molmasse für Element '{element}' ist ungültig ({molar_mass}).")
            return
        mol_per_l = mg_l / 1000.0 / molar_mass
        balance[element] = balance.get(element, 0.0) + mol_per_l

    for element in ("Ca", "Mg", "K", "Na", "Cl", "S", "P", "Fe", "Mn", "Cu", "Zn"):
        add_element(element, float(elements_mg_l.get(element, 0.0)))

    n_total = float(elements_mg_l.get("N_total", 0.0))
    if n_total:
        add_element("N", n_total)

    c_total = float(elements_mg_l.get("C", 0.0))
    hco3_mg_l = float(elements_mg_l.get("HCO3", 0.0))
    if hco3_mg_l:
        if "HCO3" in molar_masses:
            c_total += hco3_mg_l * float(molar_masses["C"]) / float(molar_masses["HCO3"])
        else:
            warnings.append("Molmasse für HCO3 fehlt; C aus HCO3 kann nicht berechnet werden.")
    if c_total:
        add_element("C", c_total)

    return balance, warnings


def _format_activity_coefficients(solutes: Iterable[str], activities: Dict[str, float], molals: Dict[str, float]) -> Dict[str, float]:
    coeffs: Dict[str, float] = {}
    for solute in solutes:
        molal = molals.get(solute)
        activity = activities.get(solute)
        if molal is None or activity is None or molal <= 0:
            continue
        coeffs[solute] = activity / molal
    return coeffs


def _load_pyequion2() -> object | None:
    if importlib.util.find_spec("pyequion2") is None:
        return None

    import sys
    import types

    if "pyequion2.gui" not in sys.modules:
        gui_stub = types.ModuleType("pyequion2.gui")

        def _no_gui(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("pyequion2 GUI ist in dieser Umgebung nicht verfügbar.")

        gui_stub.run = _no_gui
        sys.modules["pyequion2.gui"] = gui_stub

    return importlib.import_module("pyequion2")


def compute_speciation(
    ions_mmol_per_l: Dict[str, float],
    elements_mg_l: Dict[str, float],
    molar_masses: Dict[str, float],
    config: Dict[str, object] | None = None,
) -> Dict[str, object] | None:
    raw_config = config or {}
    cfg = SpeciationConfig(
        enabled=bool(raw_config.get("enabled", False)),
        engine=str(raw_config.get("engine", "pyequion2")),
        temperature_c=float(raw_config.get("temperature_c", 25.0)),
        activity_model=str(raw_config.get("activity_model", "PITZER")).upper(),
        precipitation_si_threshold=float(raw_config.get("precipitation_si_threshold", 0.0)),
    )

    if not cfg.enabled:
        return None

    warnings: list[str] = []
    if cfg.engine.lower() != "pyequion2":
        return {
            "enabled": True,
            "status": "error",
            "engine": cfg.engine,
            "warnings": [f"Unbekannte Speciation-Engine: {cfg.engine}"],
        }

    pyequion2 = _load_pyequion2()
    if pyequion2 is None:
        return {
            "enabled": True,
            "status": "error",
            "engine": cfg.engine,
            "warnings": ["Optionales Paket pyequion2 ist nicht installiert."],
        }

    element_balance, balance_warnings = _build_element_balance(elements_mg_l, molar_masses)
    warnings.extend(balance_warnings)

    filtered_balance = {k: v for k, v in element_balance.items() if k in SUPPORTED_PYEQUION_ELEMENTS and v > 0.0}
    ignored = sorted(set(element_balance) - set(filtered_balance))
    if ignored:
        warnings.append(f"Ignoriere nicht unterstützte Elemente: {', '.join(ignored)}.")

    if not filtered_balance:
        return {
            "enabled": True,
            "status": "error",
            "engine": cfg.engine,
            "warnings": warnings + ["Keine unterstützten Elemente für Speciation gefunden."],
        }

    temperature_k = cfg.temperature_c + 273.15
    eqsys = pyequion2.EquilibriumSystem(
        list(filtered_balance.keys()),
        from_elements=True,
        activity_model=cfg.activity_model,
    )

    try:
        solution, stats = eqsys.solve_equilibrium_elements_balance(temperature_k, filtered_balance)
    except Exception as exc:  # noqa: BLE001
        return {
            "enabled": True,
            "status": "error",
            "engine": cfg.engine,
            "warnings": warnings + [f"Speciation fehlgeschlagen: {exc}"],
        }

    activities = solution.activities
    molals = solution.solute_molals
    activity_coefficients = _format_activity_coefficients(solution.solutes, activities, molals)

    saturation_indexes = solution.saturation_indexes
    precipitation_risks = [
        {
            "phase": phase,
            "saturation_index": si,
            "saturation_ratio": 10 ** si,
        }
        for phase, si in saturation_indexes.items()
        if si > cfg.precipitation_si_threshold
    ]

    return {
        "enabled": True,
        "status": "ok",
        "engine": cfg.engine,
        "activity_model": cfg.activity_model,
        "temperature_c": cfg.temperature_c,
        "ph": float(solution.ph),
        "ionic_strength_molal": float(solution.ionic_strength),
        "activity_coefficients": activity_coefficients,
        "activities": activities,
        "solute_molals": molals,
        "saturation_indexes": saturation_indexes,
        "precipitation_risks": precipitation_risks,
        "warnings": warnings,
        "solver": {
            "type": solution.solvertype,
            "stats": stats,
        },
        "inputs": {
            "elements_molal": filtered_balance,
            "ions_mmol_per_l": {k: v for k, v in ions_mmol_per_l.items() if v},
        },
    }
