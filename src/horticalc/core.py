from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .data_io import (
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_recipe,
    load_water_profile_data,
    repo_root,
)
from .sluijsmann import compute_sluijsmann


COMP_COLS: List[str] = [
    # N forms (as element N fraction in fertilizers)
    "NH4", "NO3", "Ur-N",
    # oxides
    "P2O5", "K2O", "CaO", "MgO", "Na2O",
    # anions / other
    "SO4", "Cl", "CO3", "HCO3", "SiO2",
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
    "HCO3",
    "SiO2",
]

WATER_PROFILE_KEYS: List[str] = [
    "NH4",
    "NO3",
    "P2O5",
    "K2O",
    "CaO",
    "MgO",
    "Na2O",
    "SO4",
    "Cl",
    "SiO2",
    "HCO3",
    "Fe",
    "Mn",
    "Cu",
    "Zn",
    "B",
    "Mo",
]

OXIDE_ELEMENT_FORMS: tuple[str, ...] = ("P2O5", "K2O", "CaO", "MgO", "Na2O")

OTHER_ELEMENT_FORMS: tuple[str, ...] = ("SO4", "CO3", "SiO2", "Cl", "Fe", "Mn", "Cu", "Zn", "B", "Mo")


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

    def hco3_from_kh(dkh: float) -> float:
        if dkh == 0.0:
            return 0.0
        mg_l_caco3 = dkh * 17.848
        return hco3_from_caco3(mg_l_caco3)

    for key in WATER_PROFILE_KEYS:
        add(key, raw.get(key, 0.0))

    add("NH4", raw.get("NH3", 0.0))
    add("NO3", raw.get("NO2", 0.0))

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

    if raw.get("HCO3", 0.0) == 0.0:
        add("HCO3", hco3_from_caco3(raw.get("CaCO3", 0.0)))
        add("HCO3", hco3_from_kh(raw.get("KH", 0.0)))

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
) -> tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float]]:
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

    hco3_mg_l = forms_mg_l.get("HCO3", 0.0) + water_forms.get("HCO3", 0.0)
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


@dataclass
class CalcResult:
    liters: float
    elements_mg_l: Dict[str, float]
    oxides_mg_l: Dict[str, float]
    ions_mmol_l: Dict[str, float]
    ions_meq_l: Dict[str, float]
    ion_balance: Dict[str, float]
    fertilizer_elements_mg_l: Dict[str, float]
    fertilizer_oxides_mg_l: Dict[str, float]
    fertilizer_ions_mmol_l: Dict[str, float]
    fertilizer_ions_meq_l: Dict[str, float]
    fertilizer_ion_balance: Dict[str, float]
    ec_fertilizer: Dict[str, object]
    water_elements_mg_l: Dict[str, float]
    water_oxides_mg_l: Dict[str, float]
    water_ions_mmol_l: Dict[str, float]
    water_ions_meq_l: Dict[str, float]
    water_ion_balance: Dict[str, float]
    ec_water: Dict[str, object]
    sluijsmann: Dict[str, float | dict]
    osmosis_percent: float
    speciation: Dict[str, object] | None = None
    ec_validation: Dict[str, object] | None = None

    def to_dict(self) -> dict:
        from .metrics import format_npks
        from .ec import compute_ec

        payload = {
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
        if self.speciation is not None:
            payload["speciation"] = self.speciation
        if self.ec_validation is not None:
            payload["ec_validation"] = self.ec_validation
        return payload


def _parse_feature_config(config: object | None) -> tuple[bool, dict]:
    if config is None:
        return False, {}
    if isinstance(config, bool):
        return config, {}
    if isinstance(config, dict):
        enabled = bool(config.get("enabled", True))
        return enabled, config
    return False, {}


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
            raise KeyError(f"Unbekannter Dünger im Rezept: '{name}'")

        fert = fertilizers[name]
        eff_g = grams * float(fert.weight_factor or 1.0)
        for key, frac in fert.comp.items():
            if key not in forms_mg_l:
                continue
            forms_mg_l[key] += eff_g * float(frac) * 1000.0 / liters

    # 2) Add water baseline (water profile is in mg/L of its own forms)
    # Water NH4/NO3 are interpreted as molecules (NH4, NO3), NOT "N as ...".

    # 3) Compute element totals (mg/L), oxides, and ions
    elements, oxides, ions_mmol, ions_meq, ion_balance = _compute_solution_state(
        mm,
        forms_mg_l,
        water_forms,
        urea_as_nh4,
        phosphate_species,
    )

    # 4b) Water-only EC (baseline without fertilizers)
    water_only_forms = {k: 0.0 for k in COMP_COLS}
    water_elements, water_oxides, water_ions_mmol, water_ions_meq, water_ion_balance = _compute_solution_state(
        mm,
        water_only_forms,
        water_forms,
        urea_as_nh4,
        phosphate_species,
    )
    ec_water = compute_ec(water_ions_mmol)
    fertilizer_only_forms = dict(forms_mg_l)
    fertilizer_water_forms: Dict[str, float] = {k: 0.0 for k in OXIDE_FORM_COLS}
    fert_elements, fert_oxides, fert_ions_mmol, fert_ions_meq, fert_ion_balance = _compute_solution_state(
        mm,
        fertilizer_only_forms,
        fertilizer_water_forms,
        urea_as_nh4,
        phosphate_species,
    )
    ec_fertilizer = compute_ec(fert_ions_mmol)

    speciation = None
    speciation_enabled, speciation_config = _parse_feature_config(recipe.get("speciation"))
    if speciation_enabled:
        from .speciation import SpeciationConfig, compute_speciation

        speciation = compute_speciation(
            molar_masses=mm,
            elements_mg_l=elements,
            config=SpeciationConfig(
                backend=str(speciation_config.get("backend", "pyequion2")),
                activity_model=str(speciation_config.get("activity_model", "PITZER")),
                temperature_c=float(speciation_config.get("temperature_c", 25.0)),
                include_gas_phases=bool(speciation_config.get("include_gas_phases", False)),
            ),
        )

    ec_validation = None
    ec_validation_enabled, ec_validation_config = _parse_feature_config(recipe.get("ec_validation"))
    if ec_validation_enabled:
        from .ec_validation import compute_ec_validation

        ec_validation = compute_ec_validation(
            ions_mmol_per_l=ions_mmol,
            temperature_c=float(ec_validation_config.get("temperature_c", 25.0)),
            backend=str(ec_validation_config.get("backend", "pyEQL")),
        )
        if ec_validation.get("status") == "ok":
            ec_primary = compute_ec(ions_mmol)
            primary_ec = ec_primary.get("ec_mS_per_cm", {}).get("25.0")
            if primary_ec is not None:
                ec_validation["primary_ec_mS_per_cm"] = primary_ec
                ec_validation["delta_mS_per_cm"] = ec_validation["ec_mS_per_cm"] - primary_ec

    sluijsmann = compute_sluijsmann(
        liters=liters,
        oxides_mg_l=oxides,
        elements_mg_l=elements,
        config=recipe.get("sluijsmann"),
    )

    return CalcResult(
        liters=liters,
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
        speciation=speciation,
        ec_validation=ec_validation,
    )


def run_recipe(recipe_path: Path) -> dict:
    recipe = load_recipe(recipe_path)
    ferts = load_fertilizers()
    mm = load_molar_masses()

    wp_name = str(recipe.get("water_profile") or "default")
    wp_path = repo_root() / "data" / "water_profiles" / f"{wp_name}.yml"
    water_profile = load_water_profile_data(wp_path)
    osmosis_percent = float(recipe.get("osmosis_percent", water_profile.get("osmosis_percent", 0.0)))
    water = water_profile.get("mg_per_l") or {}

    res = compute_solution(recipe, ferts, mm, water, osmosis_percent=osmosis_percent)
    return res.to_dict()
