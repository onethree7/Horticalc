from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from .chemistry import (
    COMP_COLS,
    FORM_ELEMENT_RULES,
    N_MOLECULE_FORMS,
    OTHER_ELEMENT_FORMS,
    OXIDE_ELEMENT_FORMS,
    OXIDE_ELEMENT_RULES,
    OXIDE_FORM_COLS,
    WATER_PROFILE_KEYS,
)
from .data_io import (
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_recipe,
    load_water_profile_data,
)
from .paths import resolve_water_profile_path
from .sluijsmann import compute_sluijsmann


def _mm(mm: Dict[str, float], key: str) -> float:
    if key not in mm:
        raise KeyError(f"Molar mass missing for '{key}' (data/molar_masses.yml)")
    return float(mm[key])


def _oxide_to_element(mg_l_oxide: float, mm: Dict[str, float], oxide: str) -> Tuple[str, float]:
    try:
        element, multiplier = OXIDE_ELEMENT_RULES[oxide]
    except KeyError as exc:
        raise ValueError(f"Unsupported oxide: {oxide}") from exc
    return element, mg_l_oxide * (multiplier * _mm(mm, element)) / _mm(mm, oxide)


def oxide_to_element_mg_l(mm: Dict[str, float], oxide_key: str, mg_l: float) -> Tuple[str, float]:
    mg_l_oxide = float(mg_l)
    if oxide_key in OXIDE_ELEMENT_FORMS:
        return _oxide_to_element(mg_l_oxide, mm, oxide_key)
    return _form_to_element(mg_l_oxide, mm, oxide_key)


def augment_water_profile_with_elements(mm: Dict[str, float], water_profile: Dict[str, float]) -> Dict[str, float]:
    augmented = dict(water_profile)
    for oxide_key in OXIDE_ELEMENT_FORMS + ("SO4",):
        mg_l_oxide = float(water_profile.get(oxide_key, 0.0))
        if mg_l_oxide == 0.0:
            continue
        element_key, mg_l_element = oxide_to_element_mg_l(mm, oxide_key, mg_l_oxide)
        augmented[element_key] = mg_l_element
        if oxide_key == "P2O5":
            augmented["PO4"] = mg_l_oxide * (2 * _mm(mm, "PO4")) / _mm(mm, "P2O5")
    return augmented


def _form_to_element(mg_l: float, mm: Dict[str, float], form: str) -> Tuple[str, float]:
    try:
        element, multiplier = FORM_ELEMENT_RULES[form]
    except KeyError as exc:
        raise ValueError(f"Unsupported form: {form}") from exc
    return element, mg_l * (multiplier * _mm(mm, element)) / _mm(mm, form)


def _n_molecule_to_n_element(mg_l_molecule: float, mm: Dict[str, float], molecule: str) -> float:
    if molecule not in N_MOLECULE_FORMS:
        raise ValueError(molecule)
    return mg_l_molecule * _mm(mm, "N") / _mm(mm, molecule)


def _n_element_to_molecule(mg_l_n: float, mm: Dict[str, float], molecule: str) -> float:
    if molecule not in N_MOLECULE_FORMS:
        raise ValueError(molecule)
    return mg_l_n * _mm(mm, molecule) / _mm(mm, "N")


def _urea_element_to_molecule(mg_l_n: float, mm: Dict[str, float]) -> float:
    return mg_l_n * _mm(mm, "UREA") / (2 * _mm(mm, "N"))


def _urea_molecule_to_element(mg_l_urea: float, mm: Dict[str, float]) -> float:
    return mg_l_urea * (2 * _mm(mm, "N")) / _mm(mm, "UREA")


def _normalize_mg_l(values: Dict[str, float]) -> Dict[str, float]:
    return {str(k): float(v) for k, v in values.items()}


def normalize_water_profile(mm: Dict[str, float], water_mg_l: Dict[str, float]) -> Dict[str, float]:
    raw = _normalize_mg_l(water_mg_l)
    normalized: Dict[str, float] = {}

    def add(key: str, value: float) -> None:
        if value == 0.0:
            return
        normalized[key] = normalized.get(key, 0.0) + value

    def oxide_from_element(element_mg_l: float, oxide_key: str, element_key: str, multiplier: float = 1.0) -> float:
        if element_mg_l == 0.0:
            return 0.0
        return element_mg_l * _mm(mm, oxide_key) / (multiplier * _mm(mm, element_key))

    def p2o5_from_p(mg_l_p: float) -> float:
        return oxide_from_element(mg_l_p, "P2O5", "P", multiplier=2.0)

    def p2o5_from_po4(mg_l_po4: float) -> float:
        if mg_l_po4 == 0.0:
            return 0.0
        mg_l_p = mg_l_po4 * _mm(mm, "P") / _mm(mm, "PO4")
        return p2o5_from_p(mg_l_p)

    def hco3_from_caco3(mg_l_caco3: float) -> float:
        if mg_l_caco3 == 0.0:
            return 0.0
        equiv_weight_caco3 = _mm(mm, "CaCO3") / 2.0
        return mg_l_caco3 * _mm(mm, "HCO3") / equiv_weight_caco3

    def hco3_from_co3(mg_l_co3: float) -> float:
        if mg_l_co3 == 0.0:
            return 0.0
        return mg_l_co3 * _mm(mm, "HCO3") / _mm(mm, "CO3")

    def hco3_from_kh(dkh: float) -> float:
        if dkh == 0.0:
            return 0.0
        mg_l_caco3 = dkh * 17.848
        return hco3_from_caco3(mg_l_caco3)

    for key in WATER_PROFILE_KEYS:
        add(key, raw.get(key, 0.0))

    helper_hco3 = (
        hco3_from_co3(raw.get("CO3", 0.0))
        + hco3_from_caco3(raw.get("CaCO3", 0.0))
        + hco3_from_kh(raw.get("KH", 0.0))
    )
    if helper_hco3 > 0.0:
        normalized["HCO3"] = helper_hco3

    add("P2O5", p2o5_from_po4(raw.get("PO4", 0.0)))
    add("P2O5", p2o5_from_p(raw.get("P", 0.0)))

    element_to_oxide: Dict[str, tuple[str, float]] = {
        "S": ("SO4", 1.0),
        "K": ("K2O", 2.0),
        "Na": ("Na2O", 2.0),
        "Ca": ("CaO", 1.0),
        "Mg": ("MgO", 1.0),
    }
    for element_key, (oxide_key, multiplier) in element_to_oxide.items():
        add(oxide_key, oxide_from_element(raw.get(element_key, 0.0), oxide_key, element_key, multiplier=multiplier))

    return normalized


def apply_osmosis_mix(water_mg_l: Dict[str, float], osmosis_percent: float) -> Dict[str, float]:
    factor = 1.0 - max(0.0, min(osmosis_percent, 100.0)) / 100.0
    if factor == 1.0:
        return dict(water_mg_l)
    return {k: float(v) * factor for k, v in water_mg_l.items()}


def _compute_nitrogen(
    mm: Dict[str, float],
    forms_mg_l: Dict[str, float],
    water_forms: Dict[str, float],
    urea_as_nh4: bool,
) -> tuple[Dict[str, float], float, float]:
    elements: Dict[str, float] = {}

    n_fert_from_nh4 = forms_mg_l.get("NH4", 0.0)
    n_fert_from_no3 = forms_mg_l.get("NO3", 0.0)
    n_fert_from_urea = forms_mg_l.get("UREA", 0.0)

    water_nh4_mg_l = water_forms.get("NH4", 0.0)
    water_no3_mg_l = water_forms.get("NO3", 0.0)

    fert_nh4_mg_l_as_nh4 = _n_element_to_molecule(n_fert_from_nh4, mm, "NH4") if n_fert_from_nh4 else 0.0
    fert_no3_mg_l_as_no3 = _n_element_to_molecule(n_fert_from_no3, mm, "NO3") if n_fert_from_no3 else 0.0
    urea_mg_l = _urea_element_to_molecule(n_fert_from_urea, mm) if n_fert_from_urea else 0.0
    urea_as_nh4_mg_l = (
        _n_element_to_molecule(n_fert_from_urea, mm, "NH4")
        if (urea_as_nh4 and n_fert_from_urea)
        else 0.0
    )
    if urea_as_nh4:
        urea_mg_l = 0.0

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

    for form in OXIDE_FORM_COLS:
        oxides[form] = forms_mg_l.get(form, 0.0) + water_forms.get(form, 0.0)

    # Oxides from fertilizers
    for ox in OXIDE_ELEMENT_FORMS:
        mg_l = forms_mg_l.get(ox, 0.0) + water_forms.get(ox, 0.0)
        if mg_l:
            el, val = _oxide_to_element(mg_l, mm, ox)
            elements[el] = elements.get(el, 0.0) + val

    # Other forms (SO4, CO3, SiO2, Cl + traces)
    for form in OTHER_ELEMENT_FORMS:
        mg_l = forms_mg_l.get(form, 0.0) + water_forms.get(form, 0.0)
        if mg_l:
            el, val = _form_to_element(mg_l, mm, form)
            elements[el] = elements.get(el, 0.0) + val

    hco3_mg_l = forms_mg_l.get("HCO3", 0.0) + water_forms.get("HCO3", 0.0)
    if hco3_mg_l:
        elements["HCO3"] = elements.get("HCO3", 0.0) + hco3_mg_l

    return oxides


def _compute_solution_state(
    mm: Dict[str, float],
    forms_mg_l: Dict[str, float],
    water_forms: Dict[str, float],
    urea_as_nh4: bool,
    phosphate_species: str,
) -> tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float | str]]:
    elements, nh4_mg_l_raw, no3_mg_l_raw = _compute_nitrogen(mm, forms_mg_l, water_forms, urea_as_nh4)
    oxides = _compute_oxides_and_elements(mm, forms_mg_l, water_forms, elements)
    ions_mmol, ions_meq, ion_balance = _compute_ions(
        mm,
        forms_mg_l,
        water_forms,
        elements,
        nh4_mg_l_raw,
        no3_mg_l_raw,
        phosphate_species,
    )
    return elements, oxides, ions_mmol, ions_meq, ion_balance


def _compute_ion_balance(cations_sum: float, anions_sum: float) -> Dict[str, float | str]:
    denom = cations_sum + anions_sum
    raw_cbe_signed = 0.0 if denom == 0 else (cations_sum - anions_sum) / denom * 100.0
    din_signed = 0.0 if denom == 0 else (cations_sum - anions_sum) / (0.5 * denom) * 100.0

    return {
        "cations_meq_per_l": cations_sum,
        "anions_meq_per_l": anions_sum,
        "error_percent_signed": raw_cbe_signed,
        "error_percent_abs": abs(raw_cbe_signed),
        "raw_cbe_percent_signed": raw_cbe_signed,
        "raw_cbe_percent_abs": abs(raw_cbe_signed),
        "din_38402_62_percent_signed": din_signed,
        "din_38402_62_percent_abs": abs(din_signed),
        "balance_method": "non_speciated_major_ion_balance",
    }


def _compute_ions(
    mm: Dict[str, float],
    forms_mg_l: Dict[str, float],
    water_forms: Dict[str, float],
    elements: Dict[str, float],
    nh4_mg_l_raw: float,
    no3_mg_l_raw: float,
    phosphate_species: str,
) -> tuple[Dict[str, float], Dict[str, float], Dict[str, float | str]]:
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

    hco3_mg_l = forms_mg_l.get("HCO3", 0.0) + water_forms.get("HCO3", 0.0)
    if hco3_mg_l:
        add_ion("HCO3-", hco3_mg_l, "HCO3", charge=-1)
    co3_mg_l = forms_mg_l.get("CO3", 0.0) + water_forms.get("CO3", 0.0)
    if co3_mg_l:
        add_ion("CO3^2-", co3_mg_l, "CO3", charge=-2)

    cations_sum = sum(v for v in ions_meq.values() if v > 0)
    anions_sum = -sum(v for v in ions_meq.values() if v < 0)
    ion_balance = _compute_ion_balance(cations_sum, anions_sum)

    return ions_mmol, ions_meq, ion_balance


@dataclass
class CalcResult:
    liters: float
    forms_mg_l: Dict[str, float]
    water_forms_mg_l: Dict[str, float]
    fertilizer_forms_mg_l: Dict[str, float]
    elements_mg_l: Dict[str, float]
    oxides_mg_l: Dict[str, float]
    ions_mmol_l: Dict[str, float]
    ions_meq_l: Dict[str, float]
    ion_balance: Dict[str, float | str]
    fertilizer_elements_mg_l: Dict[str, float]
    fertilizer_oxides_mg_l: Dict[str, float]
    fertilizer_ions_mmol_l: Dict[str, float]
    fertilizer_ions_meq_l: Dict[str, float]
    fertilizer_ion_balance: Dict[str, float | str]
    ec_fertilizer: Dict[str, object]
    water_elements_mg_l: Dict[str, float]
    water_oxides_mg_l: Dict[str, float]
    water_ions_mmol_l: Dict[str, float]
    water_ions_meq_l: Dict[str, float]
    water_ion_balance: Dict[str, float | str]
    ec_water: Dict[str, object]
    sluijsmann: Dict[str, float | str | Dict[str, float]]
    osmosis_percent: float

    def to_dict(self) -> dict:
        from .metrics import format_npks
        from .ec import compute_ec

        return {
            "liters": self.liters,
            "elements_mg_per_l": self.elements_mg_l,
            "oxides_mg_per_l": self.oxides_mg_l,
            "ions_mmol_per_l": self.ions_mmol_l,
            "ions_meq_per_l": self.ions_meq_l,
            "ion_balance": self.ion_balance,
            "fertilizer_elements_mg_per_l": self.fertilizer_elements_mg_l,
            "fertilizer_oxides_mg_per_l": self.fertilizer_oxides_mg_l,
            "fertilizer_ions_mmol_per_l": self.fertilizer_ions_mmol_l,
            "fertilizer_ions_meq_per_l": self.fertilizer_ions_meq_l,
            "fertilizer_ion_balance": self.fertilizer_ion_balance,
            "ec_fertilizer": self.ec_fertilizer,
            "water_elements_mg_per_l": self.water_elements_mg_l,
            "water_oxides_mg_per_l": self.water_oxides_mg_l,
            "water_ions_mmol_per_l": self.water_ions_mmol_l,
            "water_ions_meq_per_l": self.water_ions_meq_l,
            "water_ion_balance": self.water_ion_balance,
            "ec": compute_ec(self.ions_mmol_l),
            "ec_water": self.ec_water,
            "npk_metrics": format_npks(self),
            "sluijsmann": self.sluijsmann,
            "osmosis_percent": self.osmosis_percent,
        }


def compute_solution(
    recipe: dict,
    fertilizers: Dict[str, Fertilizer],
    molar_masses: Dict[str, float],
    water_mg_l: Dict[str, float] | None = None,
    osmosis_percent: float = 0.0,
) -> CalcResult:
    from .ec import compute_ec

    mm = molar_masses
    water_mg_l = apply_osmosis_mix(water_mg_l or {}, osmosis_percent)
    water_forms = normalize_water_profile(mm, water_mg_l)

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
            raise KeyError(f"Unknown fertilizer in recipe: '{name}'")

        fert = fertilizers[name]
        eff_g = grams * float(fert.weight_factor or 1.0)
        for key, frac in fert.comp.items():
            if key not in forms_mg_l:
                continue
            forms_mg_l[key] += eff_g * float(frac) * 1000.0 / liters

    # 2) Add water baseline (water profile is in mg/L of its own forms)
    # Water NH4/NO3 are interpreted as molecules (NH4, NO3), NOT "N as ...".
    water_forms_mg_l = {k: water_forms.get(k, 0.0) for k in COMP_COLS}
    fertilizer_forms_mg_l = dict(forms_mg_l)
    total_forms_mg_l = {
        k: fertilizer_forms_mg_l.get(k, 0.0) + water_forms_mg_l.get(k, 0.0)
        for k in COMP_COLS
    }

    # 3) Compute element totals (mg/L), oxides, and ions
    elements, oxides, ions_mmol, ions_meq, ion_balance = _compute_solution_state(
        mm,
        forms_mg_l,
        water_forms,
        urea_as_nh4,
        phosphate_species,
    )

    # 4) Compute the water-only and fertilizer-only states
    water_elements, water_oxides, water_ions_mmol, water_ions_meq, water_ion_balance = _compute_solution_state(
        mm,
        {},
        water_forms,
        urea_as_nh4,
        phosphate_species,
    )
    ec_water = compute_ec(water_ions_mmol)
    fert_elements, fert_oxides, fert_ions_mmol, fert_ions_meq, fert_ion_balance = _compute_solution_state(
        mm,
        fertilizer_forms_mg_l,
        {},
        urea_as_nh4,
        phosphate_species,
    )
    ec_fertilizer = compute_ec(fert_ions_mmol)

    sluijsmann = compute_sluijsmann(
        liters=liters,
        oxides_mg_l=oxides,
        elements_mg_l=elements,
        config=recipe.get("sluijsmann"),
    )

    return CalcResult(
        liters=liters,
        forms_mg_l=total_forms_mg_l,
        water_forms_mg_l=water_forms_mg_l,
        fertilizer_forms_mg_l=fertilizer_forms_mg_l,
        elements_mg_l=elements,
        oxides_mg_l=oxides,
        ions_mmol_l=ions_mmol,
        ions_meq_l=ions_meq,
        ion_balance=ion_balance,
        fertilizer_elements_mg_l=fert_elements,
        fertilizer_oxides_mg_l=fert_oxides,
        fertilizer_ions_mmol_l=fert_ions_mmol,
        fertilizer_ions_meq_l=fert_ions_meq,
        fertilizer_ion_balance=fert_ion_balance,
        ec_fertilizer=ec_fertilizer,
        water_elements_mg_l=water_elements,
        water_oxides_mg_l=water_oxides,
        water_ions_mmol_l=water_ions_mmol,
        water_ions_meq_l=water_ions_meq,
        water_ion_balance=water_ion_balance,
        ec_water=ec_water,
        sluijsmann=sluijsmann,
        osmosis_percent=float(osmosis_percent),
    )


def run_recipe(recipe_path: Path, water_profile_path: Path | None = None) -> dict:
    recipe = load_recipe(recipe_path)
    ferts = load_fertilizers()
    mm = load_molar_masses()

    water_profile_value = recipe.get("water_profile")
    if water_profile_path is not None:
        water_profile = load_water_profile_data(water_profile_path)
    elif isinstance(water_profile_value, dict):
        water_profile = water_profile_value
    else:
        wp_name = str(water_profile_value or "default")
        water_profile = load_water_profile_data(resolve_water_profile_path(wp_name))
    osmosis_percent = float(recipe.get("osmosis_percent", water_profile.get("osmosis_percent", 0.0)))
    water = water_profile.get("mg_per_l") or {}

    res = compute_solution(recipe, ferts, mm, water, osmosis_percent=osmosis_percent)
    return res.to_dict()


def solve_recipe(
    recipe_path: Path,
    water_profile_path: Path | None = None,
    solver_config_overrides: dict | None = None,
) -> dict:
    from .solver import solve_recipe as run_solver

    result = run_solver(
        recipe_path,
        water_profile_path=water_profile_path,
        solver_config_overrides=solver_config_overrides,
    )
    return result.to_dict()
