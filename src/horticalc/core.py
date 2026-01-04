from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

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
    "NH4",
    "NO3",
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
    "Ur-N",
]


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


@dataclass
class CalcResult:
    liters: float
    elements_mg_l: Dict[str, float]
    n_forms_mg_l: Dict[str, float]
    oxides_mg_l: Dict[str, float]
    ions_mmol_l: Dict[str, float]
    ions_meq_l: Dict[str, float]
    ion_balance: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "liters": self.liters,
            "elements_mg_per_l": self.elements_mg_l,
            "n_forms_mg_per_l": self.n_forms_mg_l,
            "oxides_mg_per_l": self.oxides_mg_l,
            "ions_mmol_per_l": self.ions_mmol_l,
            "ions_meq_per_l": self.ions_meq_l,
            "ion_balance": self.ion_balance,
        }


def compute_solution(
    recipe: dict,
    fertilizers: Dict[str, Fertilizer],
    molar_masses: Dict[str, float],
    water_mg_l: Dict[str, float] | None = None,
) -> CalcResult:
    mm = molar_masses
    water_mg_l = water_mg_l or {}

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
    # To merge with fertilizer model, we keep them in separate variables and convert later.
    water_forms = dict(water_mg_l)

    # 3) Compute element totals (mg/L)
    elements: Dict[str, float] = {}

    # Nitrogen from fertilizers (already as element N)
    n_fert_from_nh4 = float(forms_mg_l.get("NH4", 0.0))
    n_fert_from_no3 = float(forms_mg_l.get("NO3", 0.0))
    n_fert_from_urea = float(forms_mg_l.get("Ur-N", 0.0))

    # Nitrogen from water (molecules)
    water_nh4_mg_l = float(water_forms.get("NH4", 0.0))
    water_no3_mg_l = float(water_forms.get("NO3", 0.0))
    # Elementares N aus dem jeweiligen Ionen-Typ (z.B. NO3 * (N / NO3) == 0.226...)
    n_ion_aus_nh4_wasser = _n_molecule_to_n_element(water_nh4_mg_l, mm, "NH4") if water_nh4_mg_l else 0.0
    n_ion_aus_no3_wasser = _n_molecule_to_n_element(water_no3_mg_l, mm, "NO3") if water_no3_mg_l else 0.0

    n_ion_aus_nh4 = n_fert_from_nh4 + n_ion_aus_nh4_wasser
    n_ion_aus_no3 = n_fert_from_no3 + n_ion_aus_no3_wasser
    n_total = n_ion_aus_nh4 + n_ion_aus_no3 + n_fert_from_urea
    elements["N_total"] = n_total

    # Also expose the split
    n_forms = {
        "N_ION_AUS_NH4": n_ion_aus_nh4,
        "N_ION_AUS_NO3": n_ion_aus_no3,
        "N_ION_AUS_UREA": n_fert_from_urea,
        "N_FERT_AUS_NH4": n_fert_from_nh4,
        "N_FERT_AUS_NO3": n_fert_from_no3,
        "N_FERT_AUS_UREA": n_fert_from_urea,
        "N_WASSER_AUS_NH4": n_ion_aus_nh4_wasser,
        "N_WASSER_AUS_NO3": n_ion_aus_no3_wasser,
    }

    oxides = {key: 0.0 for key in OXIDE_FORM_COLS}
    oxides["NH4"] = n_ion_aus_nh4
    oxides["NO3"] = n_ion_aus_no3
    oxides["Ur-N"] = n_fert_from_urea
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
        oxides[form] = float(forms_mg_l.get(form, 0.0)) + float(water_forms.get(form, 0.0))

    # Oxides from fertilizers
    for ox in ("P2O5", "K2O", "CaO", "MgO", "Na2O"):
        mg_l = float(forms_mg_l.get(ox, 0.0)) + float(water_forms.get(ox, 0.0))
        if mg_l:
            el, val = _oxide_to_element(mg_l, mm, ox)
            elements[el] = elements.get(el, 0.0) + val

    # Other forms (SO4, CO3, SiO2, Cl + traces)
    for f in ("SO4", "CO3", "SiO2", "Cl", "Fe", "Mn", "Cu", "Zn", "B", "Mo"):
        mg_l = float(forms_mg_l.get(f, 0.0)) + float(water_forms.get(f, 0.0))
        if mg_l:
            el, val = _form_to_element(mg_l, mm, f)
            elements[el] = elements.get(el, 0.0) + val

    # 4) Ion balance (meq/L) – use molecule forms
    ions_mmol: Dict[str, float] = {}
    ions_meq: Dict[str, float] = {}

    def add_ion(label: str, mg_l_val: float, mm_key: str, charge: int) -> None:
        mmol = 0.0 if mg_l_val == 0 else mg_l_val / _mm(mm, mm_key)
        ions_mmol[label] = mmol
        ions_meq[label] = mmol * charge

    # Cations
    # NH4+: fertilizer NH4-N -> NH4 molecule; plus water NH4 molecule
    fert_nh4_mg_l_as_nh4 = _n_element_to_molecule(n_fert_from_nh4, mm, "NH4") if n_fert_from_nh4 else 0.0
    urea_as_nh4_mg_l = _n_element_to_molecule(n_fert_from_urea, mm, "NH4") if (urea_as_nh4 and n_fert_from_urea) else 0.0
    nh4_mg_l_total = water_nh4_mg_l + fert_nh4_mg_l_as_nh4 + urea_as_nh4_mg_l
    add_ion("NH4+", nh4_mg_l_total, "NH4", charge=+1)

    # K+, Ca2+, Mg2+, Na+ from element totals (convert to mmol)
    for el, charge in (("K", +1), ("Ca", +2), ("Mg", +2), ("Na", +1)):
        mg_l_el = float(elements.get(el, 0.0))
        if mg_l_el:
            add_ion(f"{el}{'+' if charge>0 else ''}{charge if charge not in (1,-1) else ''}".replace("+1", "+"), mg_l_el, el, charge)

    # Anions
    # NO3-: fertilizer NO3-N -> NO3 molecule; plus water NO3 molecule
    fert_no3_mg_l_as_no3 = _n_element_to_molecule(n_fert_from_no3, mm, "NO3") if n_fert_from_no3 else 0.0
    no3_mg_l_total = water_no3_mg_l + fert_no3_mg_l_as_no3
    add_ion("NO3-", no3_mg_l_total, "NO3", charge=-1)

    # Phosphate: derive PO4 mass from P element
    p_mg_l = float(elements.get("P", 0.0))
    if p_mg_l:
        po4_mg_l = p_mg_l * _mm(mm, "PO4") / _mm(mm, "P")
        if phosphate_species.upper() == "HPO4":
            add_ion("HPO4^2-", po4_mg_l, "PO4", charge=-2)
        else:
            add_ion("H2PO4-", po4_mg_l, "PO4", charge=-1)

    # Sulfate
    so4_mg_l = float(forms_mg_l.get("SO4", 0.0)) + float(water_forms.get("SO4", 0.0))
    if so4_mg_l:
        add_ion("SO4^2-", so4_mg_l, "SO4", charge=-2)

    # Chloride
    cl_mg_l = float(elements.get("Cl", 0.0))
    if cl_mg_l:
        add_ion("Cl-", cl_mg_l, "Cl", charge=-1)

    # Bicarbonate/Carbonate from water profile if provided
    hco3_mg_l = float(water_forms.get("HCO3", 0.0))
    if hco3_mg_l:
        add_ion("HCO3-", hco3_mg_l, "HCO3", charge=-1)
    co3_mg_l = float(forms_mg_l.get("CO3", 0.0)) + float(water_forms.get("CO3", 0.0))
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

    return CalcResult(
        liters=liters,
        elements_mg_l=elements,
        n_forms_mg_l=n_forms,
        oxides_mg_l=oxides,
        ions_mmol_l=ions_mmol,
        ions_meq_l=ions_meq,
        ion_balance=ion_balance,
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
