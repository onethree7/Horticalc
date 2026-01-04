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
    # molecule is NH4 or NO3 (always molecule-based for NH4/NO3 inputs)
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


def collect_forms_mg_l(
    recipe: dict,
    fertilizers: Dict[str, Fertilizer],
    liters: float,
) -> Dict[str, float]:
    # NH4/NO3 are always treated as molecules (fertilizers + water); Ur-N stays as element N.
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
    return forms_mg_l


def merge_water_forms(
    forms_mg_l: Dict[str, float],
    water_mg_l: Dict[str, float] | None,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    water_forms = dict(water_mg_l or {})
    merged_keys = set(forms_mg_l) | set(water_forms)
    merged = {
        key: float(forms_mg_l.get(key, 0.0)) + float(water_forms.get(key, 0.0))
        for key in merged_keys
    }
    return merged, water_forms


def forms_to_elements(
    forms: Dict[str, float],
    mm: Dict[str, float],
    n_species_context: Dict[str, float],
) -> Dict[str, float]:
    elements: Dict[str, float] = {}
    elements["N_total"] = n_species_context["n_total"]
    elements["N_NH4"] = n_species_context["n_from_nh4"]
    elements["N_NO3"] = n_species_context["n_from_no3"]
    elements["N_UREA"] = n_species_context["n_from_urea"]

    # OXIDBERECHNUNG: Oxide/Anionen in Elemente überführen
    for ox in ("P2O5", "K2O", "CaO", "MgO", "Na2O"):
        mg_l = float(forms.get(ox, 0.0))
        if mg_l:
            el, val = _oxide_to_element(mg_l, mm, ox)
            elements[el] = elements.get(el, 0.0) + val

    for f in ("SO4", "CO3", "SiO2", "Cl", "Fe", "Mn", "Cu", "Zn", "B", "Mo"):
        mg_l = float(forms.get(f, 0.0))
        if mg_l:
            el, val = _form_to_element(mg_l, mm, f)
            elements[el] = elements.get(el, 0.0) + val

    return elements


def elements_to_ions(
    elements: Dict[str, float],
    forms: Dict[str, float],
    mm: Dict[str, float],
    phosphate_species: str,
    n_species_context: Dict[str, float],
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    ions_mmol: Dict[str, float] = {}
    ions_meq: Dict[str, float] = {}

    # IONENABLEITUNG: Ionentabelle aus Molekül-/Elementdaten ableiten
    def add_ion(label: str, mg_l_val: float, mm_key: str, charge: int) -> None:
        mmol = 0.0 if mg_l_val == 0 else mg_l_val / _mm(mm, mm_key)
        ions_mmol[label] = mmol
        ions_meq[label] = mmol * charge

    # Cations
    add_ion("NH4+", n_species_context["nh4_mg_l_raw"], "NH4", charge=+1)

    for el, charge in (("K", +1), ("Ca", +2), ("Mg", +2), ("Na", +1)):
        mg_l_el = float(elements.get(el, 0.0))
        if mg_l_el:
            label = f"{el}{'+' if charge > 0 else ''}{charge if charge not in (1, -1) else ''}".replace("+1", "+")
            add_ion(label, mg_l_el, el, charge)

    # Anions
    add_ion("NO3-", n_species_context["no3_mg_l_raw"], "NO3", charge=-1)

    p_mg_l = float(elements.get("P", 0.0))
    if p_mg_l:
        po4_mg_l = p_mg_l * _mm(mm, "PO4") / _mm(mm, "P")
        if phosphate_species.upper() == "HPO4":
            add_ion("HPO4^2-", po4_mg_l, "PO4", charge=-2)
        else:
            add_ion("H2PO4-", po4_mg_l, "PO4", charge=-1)

    so4_mg_l = float(forms.get("SO4", 0.0))
    if so4_mg_l:
        add_ion("SO4^2-", so4_mg_l, "SO4", charge=-2)

    cl_mg_l = float(elements.get("Cl", 0.0))
    if cl_mg_l:
        add_ion("Cl-", cl_mg_l, "Cl", charge=-1)

    hco3_mg_l = float(forms.get("HCO3", 0.0))
    if hco3_mg_l:
        add_ion("HCO3-", hco3_mg_l, "HCO3", charge=-1)
    co3_mg_l = float(forms.get("CO3", 0.0))
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


@dataclass
class CalcResult:
    liters: float
    elements_mg_l: Dict[str, float]
    oxides_mg_l: Dict[str, float]
    ions_mmol_l: Dict[str, float]
    ions_meq_l: Dict[str, float]
    ion_balance: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "liters": self.liters,
            "elements_mg_per_l": self.elements_mg_l,
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

    # 1) sammeln: Contributions from fertilizers -> mg/L in their declared forms
    forms_mg_l = collect_forms_mg_l(recipe, fertilizers, liters)

    # 2) Wasserprofile sauber kombinieren
    merged_forms, water_forms = merge_water_forms(forms_mg_l, water_mg_l)

    # 3) N-Spezies ableiten (NH4/NO3 sind immer Moleküle, auch im Dünger)
    fert_nh4_mg_l = float(forms_mg_l.get("NH4", 0.0))
    fert_no3_mg_l = float(forms_mg_l.get("NO3", 0.0))
    n_fert_from_urea = float(forms_mg_l.get("Ur-N", 0.0))
    water_nh4_mg_l = float(water_forms.get("NH4", 0.0))
    water_no3_mg_l = float(water_forms.get("NO3", 0.0))

    urea_mg_l = _urea_element_to_molecule(n_fert_from_urea, mm) if n_fert_from_urea else 0.0
    urea_as_nh4_mg_l = _n_element_to_molecule(n_fert_from_urea, mm, "NH4") if (urea_as_nh4 and n_fert_from_urea) else 0.0

    nh4_mg_l_raw = water_nh4_mg_l + fert_nh4_mg_l + urea_as_nh4_mg_l
    no3_mg_l_raw = water_no3_mg_l + fert_no3_mg_l

    n_from_nh4 = _n_molecule_to_n_element(nh4_mg_l_raw, mm, "NH4") if nh4_mg_l_raw else 0.0
    n_from_no3 = _n_molecule_to_n_element(no3_mg_l_raw, mm, "NO3") if no3_mg_l_raw else 0.0
    n_from_urea = _urea_molecule_to_element(urea_mg_l, mm) if urea_mg_l else 0.0

    n_total = n_from_nh4 + n_from_no3 + n_from_urea
    n_species_context = {
        "n_total": n_total,
        "n_from_nh4": n_from_nh4,
        "n_from_no3": n_from_no3,
        "n_from_urea": n_from_urea,
        "nh4_mg_l_raw": nh4_mg_l_raw,
        "no3_mg_l_raw": no3_mg_l_raw,
    }

    # 4) Elemente/Oxide aus Formen ableiten
    elements = forms_to_elements(merged_forms, mm, n_species_context)
    oxides = {key: float(merged_forms.get(key, 0.0)) for key in OXIDE_FORM_COLS}
    oxides["N_total"] = n_total

    # 5) Ionentabelle berechnen
    ions_mmol, ions_meq, ion_balance = elements_to_ions(
        elements,
        merged_forms,
        mm,
        phosphate_species,
        n_species_context,
    )

    return CalcResult(
        liters=liters,
        elements_mg_l=elements,
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
