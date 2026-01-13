from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
import math
import sys
import types
from pathlib import Path
from typing import Dict, Iterable


SUPPORTED_PYEQUION_ACTIVITY_MODELS = {"IDEAL", "DEBYE", "EXTENDED_DEBYE", "PITZER"}


@dataclass(frozen=True)
class SpeciationConfig:
    backend: str = "pyequion2"
    activity_model: str = "PITZER"
    temperature_c: float = 25.0
    include_gas_phases: bool = False


def _load_pyequion2_modules() -> tuple[object, object]:
    spec = importlib.util.find_spec("pyequion2")
    if spec is None or not spec.submodule_search_locations:
        raise ImportError("pyequion2 ist nicht installiert.")

    package_path = Path(spec.submodule_search_locations[0])
    if not package_path.exists():
        raise ImportError("pyequion2 Paketpfad ist ungültig.")

    if "pyequion2" not in sys.modules:
        pkg = types.ModuleType("pyequion2")
        pkg.__path__ = [str(package_path)]
        sys.modules["pyequion2"] = pkg

    equilibrium_system = importlib.import_module("pyequion2.equilibrium_system")
    builder = importlib.import_module("pyequion2.builder")
    return equilibrium_system.EquilibriumSystem, builder


def _mg_l_to_mol_per_l(mg_l: float, molar_mass: float) -> float:
    if mg_l == 0.0:
        return 0.0
    return mg_l / 1000.0 / molar_mass


def _build_element_balance(
    molar_masses: Dict[str, float],
    elements_mg_l: Dict[str, float],
    supported_elements: Iterable[str],
) -> tuple[Dict[str, float], list[str]]:
    element_balance: Dict[str, float] = {}
    skipped: list[str] = []

    def add_element(element_key: str, mg_l: float, molar_key: str) -> None:
        if mg_l == 0.0:
            return
        mol_per_l = _mg_l_to_mol_per_l(mg_l, molar_masses[molar_key])
        element_balance[element_key] = element_balance.get(element_key, 0.0) + mol_per_l

    direct_map = {
        "Ca": ("Ca", "Ca"),
        "Mg": ("Mg", "Mg"),
        "K": ("K", "K"),
        "Na": ("Na", "Na"),
        "Cl": ("Cl", "Cl"),
        "S": ("S", "S"),
        "P": ("P", "P"),
        "Fe": ("Fe", "Fe"),
        "Mn": ("Mn", "Mn"),
        "Cu": ("Cu", "Cu"),
        "Zn": ("Zn", "Zn"),
        "C": ("C", "C"),
    }

    for source_key, (element_key, molar_key) in direct_map.items():
        if element_key not in supported_elements:
            continue
        add_element(element_key, elements_mg_l.get(source_key, 0.0), molar_key)

    if "N" in supported_elements:
        add_element("N", elements_mg_l.get("N_total", 0.0), "N")

    if "C" in supported_elements and elements_mg_l.get("HCO3", 0.0) != 0.0:
        add_element("C", elements_mg_l.get("HCO3", 0.0), "HCO3")

    for key in elements_mg_l:
        if key in ("N_total", "N_NH4", "N_NO3", "N_UREA", "HCO3"):
            continue
        mapped = key in direct_map
        if mapped:
            continue
        skipped.append(key)

    return element_balance, skipped


def compute_speciation(
    molar_masses: Dict[str, float],
    elements_mg_l: Dict[str, float],
    config: SpeciationConfig,
) -> dict:
    result = {
        "enabled": True,
        "backend": config.backend,
        "status": "unavailable",
        "activity_model": config.activity_model,
        "temperature_c": config.temperature_c,
        "include_gas_phases": config.include_gas_phases,
        "ph": None,
        "ionic_strength_mol_per_kg": None,
        "activity_coefficients": {},
        "saturation_indexes": {},
        "precipitation_warnings": [],
        "skipped_elements": [],
        "notes": [],
        "errors": [],
    }

    if config.backend != "pyequion2":
        result["errors"].append(f"Backend '{config.backend}' ist nicht unterstützt.")
        return result

    try:
        EquilibriumSystem, builder = _load_pyequion2_modules()
    except ImportError as exc:
        result["errors"].append(str(exc))
        return result

    supported_elements = set(builder.ELEMENT_SPECIES_MAP.keys())
    element_balance, skipped = _build_element_balance(molar_masses, elements_mg_l, supported_elements)
    result["skipped_elements"] = sorted(set(skipped))

    if not element_balance:
        result["status"] = "skipped"
        result["notes"].append("Keine unterstützten Elemente für Speciation gefunden.")
        return result

    activity_model = config.activity_model.upper()
    if activity_model not in SUPPORTED_PYEQUION_ACTIVITY_MODELS:
        result["errors"].append(
            f"Activity model '{config.activity_model}' ist ungültig. "
            f"Erlaubt: {', '.join(sorted(SUPPORTED_PYEQUION_ACTIVITY_MODELS))}."
        )
        return result

    try:
        eqsys = EquilibriumSystem(
            list(element_balance.keys()),
            from_elements=True,
            activity_model=activity_model,
        )
        solution, _stats = eqsys.solve_equilibrium_elements_balance_phases(
            config.temperature_c + 273.15,
            element_balance,
            has_gas_phases=config.include_gas_phases,
        )
    except Exception as exc:  # noqa: BLE001 - external library raises many types
        result["status"] = "error"
        result["errors"].append(str(exc))
        return result

    solute_molals = solution.solute_molals
    activity_coeffs: Dict[str, float] = {}
    for species, activity in solution.activities.items():
        molal = solute_molals.get(species)
        if molal is None or molal <= 0:
            continue
        activity_coeffs[species] = float(activity / molal)

    saturation_indexes = {phase: float(value) for phase, value in solution.saturation_indexes.items()}
    precipitation_warnings = []
    for phase, log_si in saturation_indexes.items():
        if log_si > 0:
            precipitation_warnings.append(
                {
                    "phase": phase,
                    "saturation_index": float(log_si),
                    "saturation_ratio": float(math.pow(10, log_si)),
                }
            )

    result.update(
        {
            "status": "ok",
            "ph": float(solution.ph),
            "ionic_strength_mol_per_kg": float(solution.ionic_strength),
            "activity_coefficients": activity_coeffs,
            "saturation_indexes": saturation_indexes,
            "precipitation_warnings": precipitation_warnings,
        }
    )

    return result
