from __future__ import annotations

from typing import Mapping

SO3_FROM_SO4 = 80.063 / 96.06
SO3_FROM_S = 80.063 / 32.065


def _to_float(value: object | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _normalize_mode(mode: object | None) -> str:
    if mode is None:
        return "arable"
    mode_str = str(mode).strip().lower()
    if mode_str in {"grassland", "gruenland", "grünland", "pasture"}:
        return "grassland"
    if mode_str in {"arable", "ackerland"}:
        return "arable"
    return mode_str or "arable"


def _default_n_for_mode(mode: str) -> float:
    if mode == "grassland":
        return 0.8
    return 1.0


def _get(mapping: Mapping[str, float], key: str) -> float:
    return _to_float(mapping.get(key))


def _resolve_so3(oxides_mg_l: Mapping[str, float], elements_mg_l: Mapping[str, float]) -> float:
    if "SO3" in oxides_mg_l:
        return _get(oxides_mg_l, "SO3")
    so4 = _get(oxides_mg_l, "SO4")
    if so4:
        return so4 * SO3_FROM_SO4
    s_val = _get(elements_mg_l, "S")
    if s_val:
        return s_val * SO3_FROM_S
    return 0.0


def compute_sluijsmann(
    *,
    liters: float,
    oxides_mg_l: Mapping[str, float],
    elements_mg_l: Mapping[str, float],
    config: object | None = None,
) -> dict:
    cfg = config if isinstance(config, Mapping) else {}
    mode = _normalize_mode(cfg.get("mode") if isinstance(cfg, Mapping) else None)
    n_override = cfg.get("n") if isinstance(cfg, Mapping) else None
    n = _to_float(n_override) if n_override is not None else _default_n_for_mode(mode)

    ca_o = _get(oxides_mg_l, "CaO")
    mg_o = _get(oxides_mg_l, "MgO")
    k2o = _get(oxides_mg_l, "K2O")
    na2o = _get(oxides_mg_l, "Na2O")
    p2o5 = _get(oxides_mg_l, "P2O5")
    cl = _get(oxides_mg_l, "Cl") or _get(elements_mg_l, "Cl")
    so3 = _resolve_so3(oxides_mg_l, elements_mg_l)
    n_total = _get(elements_mg_l, "N_total")

    terms = {
        "+CaO": ca_o,
        "+1.4*MgO": 1.4 * mg_o,
        "+0.6*K2O": 0.6 * k2o,
        "+0.9*Na2O": 0.9 * na2o,
        "-0.4*P2O5": -0.4 * p2o5,
        "-0.7*SO3": -0.7 * so3,
        "-0.8*Cl": -0.8 * cl,
        "-n*N": -n * n_total,
    }

    e_mg_per_l = sum(terms.values())

    return {
        "mode": mode,
        "n": n,
        "E_mg_CaOeq_per_l": e_mg_per_l,
        "E_kg_CaOeq_per_m3": e_mg_per_l / 1000.0,
        "E_g_CaOeq_for_batch": e_mg_per_l * liters / 1000.0,
        "inputs_mg_per_l": {
            "CaO": ca_o,
            "MgO": mg_o,
            "K2O": k2o,
            "Na2O": na2o,
            "P2O5": p2o5,
            "SO3": so3,
            "Cl": cl,
            "N": n_total,
        },
        "terms_mg_per_l": terms,
    }
