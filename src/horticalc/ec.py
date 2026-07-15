from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, Iterable

from .validation import finite_float, non_negative_float, positive_float


@dataclass(frozen=True)
class McCleskeyParams:
    k0: tuple[float, float, float]
    A: tuple[float, float, float]
    B: float
    z: int


MCCLESKEY_PARAMS: dict[str, McCleskeyParams] = {
    "K+": McCleskeyParams(k0=(0.003046, 1.261, 40.70), A=(0.00535, 0.9316, 22.59), B=1.5, z=+1),
    "Na+": McCleskeyParams(k0=(0.003763, 0.8770, 26.23), A=(0.00027, 1.141, 32.07), B=1.7, z=+1),
    "NH4+": McCleskeyParams(k0=(0.003341, 1.285, 39.04), A=(0.00132, 0.6070, 11.19), B=0.3, z=+1),
    "Ca2+": McCleskeyParams(k0=(0.009645, 1.984, 62.28), A=(0.03174, 2.334, 132.3), B=2.8, z=+2),
    "Mg2+": McCleskeyParams(k0=(0.01068, 1.695, 57.16), A=(0.02453, 1.915, 80.50), B=2.1, z=+2),
    "Cl-": McCleskeyParams(k0=(0.003817, 1.337, 40.99), A=(0.00613, 0.9469, 22.01), B=1.5, z=-1),
    "SO4^2-": McCleskeyParams(k0=(0.01037, 2.838, 82.37), A=(0.03324, 5.889, 193.5), B=2.6, z=-2),
    "NO3-": McCleskeyParams(k0=(0.001925, 1.214, 39.90), A=(0.00118, 0.5045, 23.31), B=0.1, z=-1),
    "HCO3-": McCleskeyParams(k0=(0.000614, 0.9048, 21.14), A=(-0.00503, 0.8957, 10.97), B=0.1, z=-1),
    "CO3^2-": McCleskeyParams(k0=(-0.000326, 2.998, 64.03), A=(-0.00181, 5.542, 120.2), B=2.3, z=-2),
}

FALLBACK_LAMBDA_25: dict[str, float] = {
    "H2PO4-": 36.0,
}

ION_CARET_RE = re.compile(r"^(?P<formula>[A-Za-z0-9]+)\^(?P<charge>\d+)(?P<sign>[+-])$")
ION_SIMPLE_RE = re.compile(r"^(?P<formula>[A-Za-z0-9]+)(?P<sign>[+-])(?P<charge>\d*)$")


def parse_ion_key(label: str) -> tuple[str, int]:
    match = ION_CARET_RE.match(label)
    if match:
        formula = match.group("formula")
        charge = int(match.group("charge"))
        sign = match.group("sign")
    else:
        match = ION_SIMPLE_RE.match(label)
        if not match:
            raise ValueError(f"Unknown ion format: {label}")
        formula = match.group("formula")
        charge = int(match.group("charge") or "1")
        sign = match.group("sign")

    signed_charge = charge if sign == "+" else -charge

    if charge == 1:
        canonical = f"{formula}{sign}"
    else:
        canonical = f"{formula}{charge}{sign}" if sign == "+" else f"{formula}^{charge}{sign}"

    return canonical, signed_charge


def _poly_value(coeffs: Iterable[float], temp_c: float) -> float:
    a2, a1, a0 = coeffs
    return a2 * temp_c * temp_c + a1 * temp_c + a0


def _mccleskey_k(params: McCleskeyParams, temp_c: float, ionic_strength: float) -> float:
    k0 = _poly_value(params.k0, temp_c)
    if ionic_strength == 0:
        return k0
    sqrt_i = math.sqrt(ionic_strength)
    A = _poly_value(params.A, temp_c)
    return k0 - (A * sqrt_i) / (1 + params.B * sqrt_i)


def _ionic_strength(molalities: Dict[str, float], charges: Dict[str, int]) -> float:
    strength = 0.0
    for ion, molality in molalities.items():
        charge = charges[ion]
        strength += 0.5 * molality * (charge * charge)
    return strength


def _temp_key(temp_c: float) -> str:
    return f"{temp_c:.1f}"


def compute_ec(
    ions_mmol_per_l: dict[str, float],
    temps_c: tuple[float, ...] = (18.0, 25.0),
    density_kg_per_l: float = 1.0,
    fallback_temp_beta_per_c: float = 0.022,
    include_breakdown: bool = True,
    include_transport_numbers: bool = True,
    include_atc_to_25: bool = True,
    atc_alpha_per_c: float = 0.019,
) -> dict:
    density_kg_per_l = positive_float(density_kg_per_l, "density_kg_per_l")
    normalized_temps = tuple(finite_float(temp_c, "temperature") for temp_c in temps_c)
    fallback_temp_beta_per_c = finite_float(fallback_temp_beta_per_c, "fallback_temp_beta_per_c")
    atc_alpha_per_c = finite_float(atc_alpha_per_c, "atc_alpha_per_c")

    molalities: Dict[str, float] = {}
    charges: Dict[str, int] = {}
    warnings: list[str] = []
    mccleskey_ions: set[str] = set()
    fallback_ions: set[str] = set()
    ignored_ions: set[str] = set()

    for raw_ion, mmol_per_l in ions_mmol_per_l.items():
        mmol_per_l = non_negative_float(mmol_per_l, f"ions_mmol_per_l.{raw_ion}")
        if mmol_per_l == 0:
            continue
        try:
            canonical, charge = parse_ion_key(raw_ion)
        except ValueError:
            ignored_ions.add(raw_ion)
            warnings.append(f"Ion '{raw_ion}' could not be parsed and was ignored.")
            continue
        mol_per_l = mmol_per_l / 1000.0
        molality = mol_per_l / density_kg_per_l
        molalities[canonical] = molalities.get(canonical, 0.0) + molality
        charges[canonical] = charge

    for ion in molalities:
        if ion in MCCLESKEY_PARAMS:
            mccleskey_ions.add(ion)
            expected_charge = MCCLESKEY_PARAMS[ion].z
            if charges[ion] != expected_charge:
                warnings.append(
                    f"Ion '{ion}' has charge {charges[ion]}, expected {expected_charge}; using tabulated charge."
                )
        elif ion in FALLBACK_LAMBDA_25:
            fallback_ions.add(ion)
        else:
            ignored_ions.add(ion)
            warnings.append(f"Ion '{ion}' has no McCleskey or fallback parameters and was ignored.")

    ionic_strength = _ionic_strength(molalities, charges) if molalities else 0.0

    contrib_mS_per_cm: Dict[str, Dict[str, float]] = {}
    transport_numbers: Dict[str, Dict[str, float]] = {}
    ec_mS_per_cm: Dict[str, float] = {}
    ec_uS_per_cm: Dict[str, float] = {}

    for temp_c in normalized_temps:
        temp_key = _temp_key(temp_c)
        total = 0.0
        contributions: Dict[str, float] = {}

        for ion, molality in molalities.items():
            if ion in mccleskey_ions:
                params = MCCLESKEY_PARAMS[ion]
                k_val = _mccleskey_k(params, temp_c, ionic_strength)
                contrib = k_val * molality
            elif ion in fallback_ions:
                lambda_25 = FALLBACK_LAMBDA_25[ion]
                if fallback_temp_beta_per_c == 0.0:
                    lambda_t = lambda_25
                else:
                    lambda_t = lambda_25 * (1 + fallback_temp_beta_per_c * (temp_c - 25.0))
                mol_per_l = molality * density_kg_per_l
                contrib = lambda_t * mol_per_l
            else:
                continue
            if contrib < 0:
                warnings.append(f"Negative EC contribution for '{ion}' at {temp_key}°C ({contrib:.6g} mS/cm).")
            contributions[ion] = contrib
            total += contrib

        ec_mS_per_cm[temp_key] = total
        ec_uS_per_cm[temp_key] = total * 1000.0
        if include_breakdown:
            contrib_mS_per_cm[temp_key] = contributions

        if include_transport_numbers:
            if total == 0.0:
                warnings.append(f"Total EC at {temp_key}°C is 0; transport numbers = 0.")
                transport_numbers[temp_key] = dict.fromkeys(contributions, 0.0)
            else:
                transport_numbers[temp_key] = {ion: value / total for ion, value in contributions.items()}

    atc: Dict[str, float] = {}
    if include_atc_to_25:
        temp_key_18 = _temp_key(18.0)
        if temp_key_18 in ec_mS_per_cm:
            ec18 = ec_mS_per_cm[temp_key_18]
            denom = 1 + atc_alpha_per_c * (18.0 - 25.0)
            if denom == 0:
                warnings.append("ATC correction for 18°C is undefined (denom=0).")
            else:
                ec25 = ec18 / denom
                atc["ec25_from_18_mS_per_cm"] = ec25
                atc["ec25_from_18_uS_per_cm"] = ec25 * 1000.0

    coverage = {
        "mccleskey_ions_used": sorted(mccleskey_ions),
        "fallback_ions_used": sorted(fallback_ions),
        "ignored_ions": sorted(ignored_ions),
    }

    return {
        "method": "McCleskey2012(Eq7-9,Table1) + VanysekCRC93(fallback)",
        "inputs": {
            "temps_c": list(normalized_temps),
            "density_kg_per_l": density_kg_per_l,
            "fallback_temp_beta_per_c": fallback_temp_beta_per_c,
            "atc_alpha_per_c": atc_alpha_per_c,
        },
        "ionic_strength_mol_per_kg": ionic_strength,
        "ec_mS_per_cm": ec_mS_per_cm,
        "ec_uS_per_cm": ec_uS_per_cm,
        "contrib_mS_per_cm": contrib_mS_per_cm if include_breakdown else {},
        "transport_numbers": transport_numbers if include_transport_numbers else {},
        "warnings": warnings,
        "coverage": coverage,
        "atc": atc,
    }
