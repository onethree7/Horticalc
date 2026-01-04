from __future__ import annotations

from dataclasses import asdict, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from .core import CalcResult


OXIDE_TOTAL_KEYS = [
    "N_NH4",
    "N_NO3",
    "N_UREA",
    "P2O5",
    "K2O",
    "CaO",
    "MgO",
    "Na2O",
    "SO4",
    "Cl",
    "Fe",
    "Mn",
    "Cu",
    "Zn",
    "B",
    "Mo",
    "CO3",
    "SiO2",
]


def round0(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _get_sources(result: CalcResult | Mapping[str, object]) -> tuple[Mapping[str, float], Mapping[str, float]]:
    if is_dataclass(result):
        data = asdict(result)
    elif isinstance(result, Mapping):
        data = result
    else:
        data = result.__dict__

    elements = data.get("elements_mg_per_l") or data.get("elements_mg_l") or {}
    oxides = data.get("oxides_mg_per_l") or data.get("oxides_mg_l") or {}
    return elements, oxides


def _sum_keys(keys: list[str], elements: Mapping[str, float], oxides: Mapping[str, float]) -> float:
    total = 0.0
    for key in keys:
        if key.startswith("N_"):
            total += float(elements.get(key, 0.0) or 0.0)
        else:
            total += float(oxides.get(key, 0.0) or 0.0)
    return total


def format_npks(result: CalcResult | Mapping[str, object]) -> dict[str, str | dict[str, float]]:
    elements, oxides = _get_sources(result)

    n_nh4 = float(elements.get("N_NH4", 0.0) or 0.0)
    n_no3 = float(elements.get("N_NO3", 0.0) or 0.0)
    n_urea = float(elements.get("N_UREA", 0.0) or 0.0)
    n_total = n_nh4 + n_no3 + n_urea

    p2o5 = float(oxides.get("P2O5", 0.0) or 0.0)
    k2o = float(oxides.get("K2O", 0.0) or 0.0)
    cao = float(oxides.get("CaO", 0.0) or 0.0)
    mgo = float(oxides.get("MgO", 0.0) or 0.0)

    total_all = _sum_keys(OXIDE_TOTAL_KEYS, elements, oxides)
    if total_all <= 0.0:
        npk_all_pct = "0-0-0(+0CaO +0MgO)"
    else:
        n_pct = round0(n_total / total_all * 100.0)
        p_pct = round0(p2o5 / total_all * 100.0)
        k_pct = round0(k2o / total_all * 100.0)
        ca_pct = round0(cao / total_all * 100.0)
        mg_pct = round0(mgo / total_all * 100.0)
        npk_all_pct = f"{n_pct}-{p_pct}-{k_pct}(+{ca_pct}CaO +{mg_pct}MgO)"

    if p2o5 <= 0.0:
        npk_p_norm = "0-3-0"
    else:
        n_norm = round0(n_total / p2o5 * 3.0)
        k_norm = round0(k2o / p2o5 * 3.0)
        npk_p_norm = f"{n_norm}-3-{k_norm}"

    total_npk = n_total + p2o5 + k2o
    if total_npk <= 0.0:
        npk_npk_pct = "0-0-0"
    else:
        n_pct = round0(n_total / total_npk * 100.0)
        p_pct = round0(p2o5 / total_npk * 100.0)
        k_pct = round0(k2o / total_npk * 100.0)
        npk_npk_pct = f"{n_pct}-{p_pct}-{k_pct}"

    return {
        "npk_all_pct": npk_all_pct,
        "npk_p_norm": npk_p_norm,
        "npk_npk_pct": npk_npk_pct,
        "npk_values": {
            "n_total": n_total,
            "p2o5": p2o5,
            "k2o": k2o,
            "total_all": total_all,
            "total_npk": total_npk,
        },
    }
