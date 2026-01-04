from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Any

from .data_io import Fertilizer, load_fertilizers, load_molar_masses, load_recipe, load_water_profile, repo_root


COMP_COLS: List[str] = [
    # N forms (as element N fraction in fertilizers)
    "NH4", "NO3", "Ur-N",
    # oxides
    "P2O5", "K2O", "CaO", "MgO", "Na2O",
    # anions / other
    "SO4", "Cl", "CO3", "SiO2",
    # trace elements
    "Fe", "Mn", "Cu", "Zn", "B", "Mo",
]

OXIDE_FORM_COLS: List[str] = [
    "P2O5",
    "K2O",
    "CaO",
    "MgO",
    "Na2O",
    "SO4",
    "Fe",
    "Mn",
    "Cu",
    "Zn",
    "B",
    "Mo",
    "Cl",
    "CO3",
    "SiO2",
]

SLUIJSMANN_DEFAULTS = {
    "arable": 1.0,
    "grassland": 0.8,
}

SO3_FROM_SO4_FACTOR = 80.063 / 96.06
SO3_FROM_S_FACTOR = 80.063 / 32.065


def _mm(mm: Dict[str, float], key: str) -> float:
    if key not in mm:
        raise KeyError(f"Molmasse fehlt für '{key}' (data/molar_masses.yml)")
    return float(mm[key])


def _oxide_to_element(mg_l_oxide: float, mm: Dict[str, float], oxide: str) -> Tuple[str, float]:
    # returns (element_symbol, mg/L element)
    if oxide == "P2O5":
        # P2O5 -> 2P
        return "P", mg_l_oxide * (2 * _mm(mm, "P")) / _mm(mm, "P2O5")
    if oxide == "K2O":
        return "K", mg_l_oxide * (2 * _mm(mm, "K")) / _mm(mm, "K2O")
    if oxide == "CaO":
        return "Ca", mg_l_oxide * _mm(mm, "Ca") / _mm(mm, "CaO")
    if oxide == "MgO":
        return "Mg", mg_l_oxide * _mm(mm, "Mg") / _mm(mm, "MgO")
    if oxide == "Na2O":
        return "Na", mg_l_oxide * (2 * _mm(mm, "Na")) / _mm(mm, "Na2O")
    raise ValueError(f"Unsupported oxide: {oxide}")


def _form_to_element(mg_l: float, mm: Dict[str, float], form: str) -> Tuple[str, float]:
    if form in ("Fe", "Mn", "Cu", "Zn", "B", "Mo", "Cl"):
        return form, mg_l
    if form == "SO4":
        return "S", mg_l * _mm(mm, "S") / _mm(mm, "SO4")
    if form == "CO3":
        return "C", mg_l * _mm(mm, "C") / _mm(mm, "CO3")
    if form == "SiO2":
        return "Si", mg_l * _mm(mm, "Si") / _mm(mm, "SiO2")
    raise ValueError(f"Unsupported form: {form}")


def _n_molecule_to_n_element(mg_l_molecule: float, mm: Dict[str, float], molecule: str) -> float:
    # molecule is NH4 or NO3
    if molecule == "NH4":
        return mg_l_molecule * _mm(mm, "N") / _mm(mm, "NH4")
    if molecule == "NO3":
        return mg_l_molecule * _mm(mm, "N") / _mm(mm, "NO3")
    raise ValueError(molecule)


def _n_element_to_molecule(mg_l_n: float, mm: Dict[str, float], molecule: str) -> float:
    if molecule == "NH4":
        return mg_l_n * _mm(mm, "NH4") / _mm(mm, "N")
    if molecule == "NO3":
        return mg_l_n * _mm(mm, "NO3") / _mm(mm, "N")
    raise ValueError(molecule)


def _urea_element_to_molecule(mg_l_n: float, mm: Dict[str, float]) -> float:
    return mg_l_n * _mm(mm, "UREA") / (2 * _mm(mm, "N"))


def _urea_molecule_to_element(mg_l_urea: float, mm: Dict[str, float]) -> float:
    return mg_l_urea * (2 * _mm(mm, "N")) / _mm(mm, "UREA")


def _normalize_mg_l(values: Dict[str, float]) -> Dict[str, float]:
    return {str(k): float(v) for k, v in values.items()}


def _compute_nitrogen(
    mm: Dict[str, float],
    forms_mg_l: Dict[str, float],
    water_forms: Dict[str, float],
    urea_as_nh4: bool,
) -> tuple[Dict[str, float], float, float]:
    elements: Dict[str, float] = {}

    n_fert_from_nh4 = forms_mg_l.get("NH4", 0.0)
    n_fert_from_no3 = forms_mg_l.get("NO3", 0.0)
    n_fert_from_urea = forms_mg_l.get("Ur-N", 0.0)

    water_nh4_mg_l = water_forms.get("NH4", 0.0)
    water_no3_mg_l = water_forms.get("NO3", 0.0)

    fert_nh4_mg_l_as_nh4 = _n_element_to_molecule(n_fert_from_nh4, mm, "NH4") if n_fert_from_nh4 else 0.0
    fert_no3_mg_l_as_no3 = _n_element_to_molecule(n_fert_from_no3, mm, "NO3") if n_fert_from_no3 else 0.0
    urea_mg_l = _urea_element_to_molecule(n_fert_from_urea, mm) if n_fert_from_urea else 0.0
    urea_as_nh4_mg_l = _n_element_to_molecule(n_fert_from_urea, mm, "NH4") if (urea_as_nh4 and n_fert_from_urea) else 0.0

    nh4_mg_l_raw = water_nh4_mg_l + fert_nh4_mg_l_as_nh4 + urea_as_nh4_mg_l
    no3_mg_l_raw = water_no3_mg_l + fert_no3_mg_l_as_no3

    n_from_nh4 = _n_molecule_to_n_element(nh4_mg_l_raw, mm, "NH4") if nh4_mg_l_raw else 0.0
    n_from_no3 = _n_molecule_to_n_element(no3_mg_l_raw, mm, "NO3") if no3_mg_l_raw else 0.0
    n_from_urea = _urea_molecule_to_element(urea_mg_l, mm) if urea_mg_l else 0.0

    n_total = n_from_nh4 + n_from_no3 + n_from_urea
    elements["N_total"] = n_total
    elements["N_NH4"] = n_from_nh4
    elements["N_NO3"] = n_from_no3
    elements["N_UREA"] = n_from_urea

    return elements, nh4_mg_l_raw, no3_mg_l_raw


def _compute_oxides_and_elements(
    mm: Dict[str, float],
    forms_mg_l: Dict[str, float],
    water_forms: Dict[str, float],
    elements: Dict[str, float],
) -> Dict[str, float]:
    oxides = {key: 0.0 for key in OXIDE_FORM_COLS}
    oxides["N_total"] = elements.get("N_total", 0.0)

    for form in (
        "P2O5",
        "K2O",
        "CaO",
        "MgO",
        "Na2O",
        "SO4",
        "Fe",
        "Mn",
        "Cu",
        "Zn",
        "B",
        "Mo",
        "Cl",
        "CO3",
        "SiO2",
    ):
        oxides[form] = forms_mg_l.get(form, 0.0) + water_forms.get(form, 0.0)

    # Oxides from fertilizers
    for ox in ("P2O5", "K2O", "CaO", "MgO", "Na2O"):
        mg_l = forms_mg_l.get(ox, 0.0) + water_forms.get(ox, 0.0)
        if mg_l:
            el, val = _oxide_to_element(mg_l, mm, ox)
            elements[el] = elements.get(el, 0.0) + val

    # Other forms (SO4, CO3, SiO2, Cl + traces)
    for form in ("SO4", "CO3", "SiO2", "Cl", "Fe", "Mn", "Cu", "Zn", "B", "Mo"):
        mg_l = forms_mg_l.get(form, 0.0) + water_forms.get(form, 0.0)
        if mg_l:
            el, val = _form_to_element(mg_l, mm, form)
            elements[el] = elements.get(el, 0.0) + val

    return oxides


def _compute_ions(
    mm: Dict[str, float],
    forms_mg_l: Dict[str, float],
    water_forms: Dict[str, float],
    elements: Dict[str, float],
    nh4_mg_l_raw: float,
    no3_mg_l_raw: float,
    phosphate_species: str,
) -> tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    ions_mmol: Dict[str, float] = {}
    ions_meq: Dict[str, float] = {}

    def add_ion(label: str, mg_l_val: float, mm_key: str, charge: int) -> None:
        mmol = 0.0 if mg_l_val == 0 else mg_l_val / _mm(mm, mm_key)
        ions_mmol[label] = mmol
        ions_meq[label] = mmol * charge

    # Cations
    add_ion("NH4+", nh4_mg_l_raw, "NH4", charge=+1)

    for el, charge in (("K", +1), ("Ca", +2), ("Mg", +2), ("Na", +1)):
        mg_l_el = elements.get(el, 0.0)
        if mg_l_el:
            label = f"{el}{'+' if charge > 0 else ''}{charge if charge not in (1, -1) else ''}".replace("+1", "+")
            add_ion(label, mg_l_el, el, charge)

    # Anions
    add_ion("NO3-", no3_mg_l_raw, "NO3", charge=-1)

    p_mg_l = elements.get("P", 0.0)
    if p_mg_l:
        po4_mg_l = p_mg_l * _mm(mm, "PO4") / _mm(mm, "P")
        if phosphate_species.upper() == "HPO4":
            add_ion("HPO4^2-", po4_mg_l, "PO4", charge=-2)
        else:
            add_ion("H2PO4-", po4_mg_l, "PO4", charge=-1)

    so4_mg_l = forms_mg_l.get("SO4", 0.0) + water_forms.get("SO4", 0.0)
    if so4_mg_l:
        add_ion("SO4^2-", so4_mg_l, "SO4", charge=-2)

    cl_mg_l = elements.get("Cl", 0.0)
    if cl_mg_l:
        add_ion("Cl-", cl_mg_l, "Cl", charge=-1)

    hco3_mg_l = water_forms.get("HCO3", 0.0)
    if hco3_mg_l:
        add_ion("HCO3-", hco3_mg_l, "HCO3", charge=-1)
    co3_mg_l = forms_mg_l.get("CO3", 0.0) + water_forms.get("CO3", 0.0)
    if co3_mg_l:
        add_ion("CO3^2-", co3_mg_l, "CO3", charge=-2)

    cations_sum = sum(v for v in ions_meq.values() if v > 0)
    anions_sum = -sum(v for v in ions_meq.values() if v < 0)
    denom = (cations_sum + anions_sum)
    err_signed = 0.0 if denom == 0 else (cations_sum - anions_sum) / denom * 100.0
    err_abs = abs(err_signed)

    ion_balance = {
        "cations_meq_per_l": cations_sum,
        "anions_meq_per_l": anions_sum,
        "error_percent_signed": err_signed,
        "error_percent_abs": err_abs,
    }

    return ions_mmol, ions_meq, ion_balance


def _compute_sluijsmann(
    recipe: dict,
    oxides_mg_l: Dict[str, float],
    elements_mg_l: Dict[str, float],
    liters: float,
) -> Dict[str, Any]:
    cfg = recipe.get("sluijsmann")
    if not isinstance(cfg, dict):
        cfg = {}

    mode = str(cfg.get("mode") or recipe.get("sluijsmann_mode") or "arable").strip().lower()
    n_override = cfg.get("n", recipe.get("sluijsmann_n"))
    n_factor = float(n_override) if n_override is not None else float(SLUIJSMANN_DEFAULTS.get(mode, 1.0))

    ca_o = float(oxides_mg_l.get("CaO", 0.0) or 0.0)
    mg_o = float(oxides_mg_l.get("MgO", 0.0) or 0.0)
    k2_o = float(oxides_mg_l.get("K2O", 0.0) or 0.0)
    na2_o = float(oxides_mg_l.get("Na2O", 0.0) or 0.0)
    p2_o5 = float(oxides_mg_l.get("P2O5", 0.0) or 0.0)

    so3 = float(oxides_mg_l.get("SO3", 0.0) or 0.0)
    if not so3:
        so4 = float(oxides_mg_l.get("SO4", 0.0) or 0.0)
        if so4:
            so3 = so4 * SO3_FROM_SO4_FACTOR
        else:
            s_val = float(elements_mg_l.get("S", 0.0) or 0.0)
            if s_val:
                so3 = s_val * SO3_FROM_S_FACTOR

    cl_val = float(oxides_mg_l.get("Cl", 0.0) or 0.0)
    if not cl_val:
        cl_val = float(elements_mg_l.get("Cl", 0.0) or 0.0)

    n_total = float(elements_mg_l.get("N_total", 0.0) or 0.0)

    terms = {
        "+CaO": ca_o,
        "+1.4*MgO": 1.4 * mg_o,
        "+0.6*K2O": 0.6 * k2_o,
        "+0.9*Na2O": 0.9 * na2_o,
        "-0.4*P2O5": -0.4 * p2_o5,
        "-0.7*SO3": -0.7 * so3,
        "-0.8*Cl": -0.8 * cl_val,
        "-n*N": -n_factor * n_total,
    }

    e_mg_per_l = sum(terms.values())

    return {
        "mode": mode,
        "n": n_factor,
        "E_mg_CaOeq_per_l": e_mg_per_l,
        "E_kg_CaOeq_per_m3": e_mg_per_l / 1000.0,
        "E_g_CaOeq_for_batch": e_mg_per_l * liters / 1000.0,
        "inputs_mg_per_l": {
            "CaO": ca_o,
            "MgO": mg_o,
            "K2O": k2_o,
            "Na2O": na2_o,
            "P2O5": p2_o5,
            "SO3": so3,
            "Cl": cl_val,
            "N": n_total,
        },
        "terms_mg_per_l": terms,
    }


@dataclass
class CalcResult:
    liters: float
    elements_mg_l: Dict[str, float]
    oxides_mg_l: Dict[str, float]
    ions_mmol_l: Dict[str, float]
    ions_meq_l: Dict[str, float]
    ion_balance: Dict[str, float]
    sluijsmann: Dict[str, Any]

    def to_dict(self) -> dict:
        from .metrics import format_npks

        return {
            "liters": self.liters,
            "elements_mg_per_l": self.elements_mg_l,
            "oxides_mg_per_l": self.oxides_mg_l,
            "ions_mmol_per_l": self.ions_mmol_l,
            "ions_meq_per_l": self.ions_meq_l,
            "ion_balance": self.ion_balance,
            "npk_metrics": format_npks(self),
            "sluijsmann": self.sluijsmann,
        }


def compute_solution(
    recipe: dict,
    fertilizers: Dict[str, Fertilizer],
    molar_masses: Dict[str, float],
    water_mg_l: Dict[str, float] | None = None,
) -> CalcResult:
    mm = molar_masses
    water_mg_l = water_mg_l or {}
    water_forms = _normalize_mg_l(water_mg_l)

    liters = float(recipe.get("liters") or 10.0)
    urea_as_nh4 = bool(recipe.get("urea_as_nh4", False))
    phosphate_species = str(recipe.get("phosphate_species", "H2PO4"))

    # 1) Contributions from fertilizers -> mg/L in their declared forms
    forms_mg_l: Dict[str, float] = {k: 0.0 for k in COMP_COLS}
    for entry in recipe.get("fertilizers", []):
        name = str(entry.get("name") or "").strip()
        grams = float(entry.get("grams") or 0.0)
        if grams == 0.0:
            continue
        if name not in fertilizers:
            raise KeyError(f"Unbekannter Dünger im Rezept: '{name}'")

        fert = fertilizers[name]
        eff_g = grams * float(fert.weight_factor or 1.0)
        for key, frac in fert.comp.items():
            if key not in forms_mg_l:
                continue
            forms_mg_l[key] += eff_g * float(frac) * 1000.0 / liters

    # 2) Add water baseline (water profile is in mg/L of its own forms)
    # Water NH4/NO3 are interpreted as molecules (NH4, NO3), NOT "N as ...".

    # 3) Compute element totals (mg/L)
    elements, nh4_mg_l_raw, no3_mg_l_raw = _compute_nitrogen(mm, forms_mg_l, water_forms, urea_as_nh4)
    oxides = _compute_oxides_and_elements(mm, forms_mg_l, water_forms, elements)

    # 4) Ion balance (meq/L) – use molecule forms
    ions_mmol, ions_meq, ion_balance = _compute_ions(
        mm,
        forms_mg_l,
        water_forms,
        elements,
        nh4_mg_l_raw,
        no3_mg_l_raw,
        phosphate_species,
    )
    sluijsmann = _compute_sluijsmann(recipe, oxides, elements, liters)

    return CalcResult(
        liters=liters,
        elements_mg_l=elements,
        oxides_mg_l=oxides,
        ions_mmol_l=ions_mmol,
        ions_meq_l=ions_meq,
        ion_balance=ion_balance,
        sluijsmann=sluijsmann,
    )


def run_recipe(recipe_path: Path) -> dict:
    recipe = load_recipe(recipe_path)
    ferts = load_fertilizers()
    mm = load_molar_masses()

    wp_name = str(recipe.get("water_profile") or "default")
    wp_path = repo_root() / "data" / "water_profiles" / f"{wp_name}.yml"
    water = load_water_profile(wp_path)

    res = compute_solution(recipe, ferts, mm, water)
    return res.to_dict()
