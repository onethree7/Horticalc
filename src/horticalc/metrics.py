from __future__ import annotations

from dataclasses import asdict, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING, Mapping

from .chemistry import OXIDE_TOTAL_KEYS

if TYPE_CHECKING:
    from .core import CalcResult


def round0(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def round1(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


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


def format_npks(result: CalcResult | Mapping[str, object]) -> dict[str, str | dict[str, float | int]]:
    elements, oxides = _get_sources(result)

    n_nh4 = float(elements.get("N_NH4", 0.0) or 0.0)
    n_no3 = float(elements.get("N_NO3", 0.0) or 0.0)
    n_urea = float(elements.get("N_UREA", 0.0) or 0.0)
    n_total = n_nh4 + n_no3 + n_urea
    n_form_pct = {"nh4": 0, "no3": 0, "urea": 0}
    if n_total > 0.0:
        n_form_pct = {
            "nh4": round0(n_nh4 / n_total * 100.0),
            "no3": round0(n_no3 / n_total * 100.0),
            "urea": round0(n_urea / n_total * 100.0),
        }

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

    def ratio_string(label: str, numerator: float, denominator: float) -> str:
        if numerator <= 0.0:
            return f"{label}=0:0"
        if denominator <= 0.0:
            return f"{label}=1:0"
        ratio = round1(denominator / numerator)
        ratio_str = f"{ratio:.1f}".rstrip("0").rstrip(".")
        return f"{label}=1:{ratio_str}"

    def element_mg_l(element_key: str) -> float:
        if element_key == "N":
            return n_total
        return float(elements.get(element_key, 0.0) or 0.0)

    def form_mg_l(form_key: str) -> float:
        return float(oxides.get(form_key, 0.0) or 0.0)

    oxide_ratio_pairs = [
        ("N:K", n_total, element_mg_l("K")),
        ("CaO:K2O", cao, k2o),
        ("MgO:CaO", mgo, cao),
        ("Na2O:MgO", form_mg_l("Na2O"), mgo),
        ("SO4:P2O5", form_mg_l("SO4"), p2o5),
        ("P2O5:K2O", p2o5, k2o),
        ("Fe:MgO", element_mg_l("Fe"), mgo),
        ("CO3:SiO2", form_mg_l("CO3"), form_mg_l("SiO2")),
    ]
    ion_ratio_pairs = [
        ("N:K", element_mg_l("N"), element_mg_l("K")),
        ("Ca:K", element_mg_l("Ca"), element_mg_l("K")),
        ("Ca:Mg", element_mg_l("Ca"), element_mg_l("Mg")),
        ("Na:Mg", element_mg_l("Na"), element_mg_l("Mg")),
        ("SO4:P", form_mg_l("SO4"), element_mg_l("P")),
        ("P:K", element_mg_l("P"), element_mg_l("K")),
        ("Fe:Mg", element_mg_l("Fe"), element_mg_l("Mg")),
        ("CO3:Si", form_mg_l("CO3"), element_mg_l("Si")),
    ]
    npk_ratios = {
        label: ratio_string(label, numerator, denominator)
        for label, numerator, denominator in oxide_ratio_pairs
    }
    npk_ratios_ion = {
        label: ratio_string(label, numerator, denominator)
        for label, numerator, denominator in ion_ratio_pairs
    }

    return {
        "npk_all_pct": npk_all_pct,
        "npk_p_norm": npk_p_norm,
        "npk_npk_pct": npk_npk_pct,
        "n_form_pct": n_form_pct,
        "npk_ratios": npk_ratios,
        "npk_ratios_ion": npk_ratios_ion,
        "npk_values": {
            "n_total": n_total,
            "p2o5": p2o5,
            "k2o": k2o,
            "total_all": total_all,
            "total_npk": total_npk,
        },
    }
