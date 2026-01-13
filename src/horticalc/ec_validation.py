from __future__ import annotations

import importlib.util
from typing import Dict


def compute_ec_validation(
    ions_mmol_per_l: Dict[str, float],
    temperature_c: float = 25.0,
    backend: str = "pyEQL",
) -> dict:
    result = {
        "enabled": True,
        "backend": backend,
        "status": "unavailable",
        "ec_mS_per_cm": None,
        "ec_uS_per_cm": None,
        "notes": [],
        "errors": [],
    }

    if backend != "pyEQL":
        result["errors"].append(f"Backend '{backend}' ist nicht unterstützt.")
        return result

    if importlib.util.find_spec("pyEQL") is None:
        result["errors"].append("pyEQL ist nicht installiert.")
        return result

    from pyEQL import Solution

    solutes = {}
    for ion, mmol_per_l in ions_mmol_per_l.items():
        if mmol_per_l == 0:
            continue
        mol_per_l = mmol_per_l / 1000.0
        solutes[ion] = f"{mol_per_l} mol/L"

    if not solutes:
        result["status"] = "skipped"
        result["notes"].append("Keine Ionen für EC-Validierung vorhanden.")
        return result

    try:
        solution = Solution(
            solutes=solutes,
            temperature=f"{temperature_c} degC",
        )
        conductivity = solution.conductivity()
        ec_mS_per_cm = conductivity.to("mS/cm").magnitude
    except Exception as exc:  # noqa: BLE001 - optional backend can fail
        result["status"] = "error"
        result["errors"].append(str(exc))
        return result

    result.update(
        {
            "status": "ok",
            "ec_mS_per_cm": ec_mS_per_cm,
            "ec_uS_per_cm": ec_mS_per_cm * 1000.0,
        }
    )

    return result
