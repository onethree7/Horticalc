from __future__ import annotations

N_FERTILIZER_FORM_COLS = ("NO3", "NH4", "UREA")
OXIDE_FERTILIZER_COLS = ("P2O5", "K2O", "CaO", "MgO", "Na2O")
OTHER_FERTILIZER_FORM_COLS = ("SO4", "Cl", "CO3", "HCO3", "SiO2")
TRACE_ELEMENT_KEYS = ("Fe", "Mn", "Cu", "Zn", "B", "Mo")

COMP_COLS: list[str] = [
    *N_FERTILIZER_FORM_COLS,
    *OXIDE_FERTILIZER_COLS,
    *OTHER_FERTILIZER_FORM_COLS,
    *TRACE_ELEMENT_KEYS,
]

OXIDE_FORM_COLS: list[str] = [
    *OXIDE_FERTILIZER_COLS,
    "SO4",
    *TRACE_ELEMENT_KEYS,
    "Cl",
    "CO3",
    "HCO3",
    "SiO2",
]

WATER_PROFILE_KEYS: list[str] = [
    "NH4",
    "NO3",
    *OXIDE_FERTILIZER_COLS,
    "SO4",
    "Cl",
    "SiO2",
    "HCO3",
    *TRACE_ELEMENT_KEYS,
]

OXIDE_TOTAL_KEYS = [
    "N_NH4",
    "N_NO3",
    "N_UREA",
    *OXIDE_FERTILIZER_COLS,
    "SO4",
    "Cl",
    *TRACE_ELEMENT_KEYS,
    "CO3",
    "SiO2",
]

ALLOWED_WATER_KEYS = {
    "NH4",
    "NO3",
    "PO4",
    "P",
    "SO4",
    "S",
    "K",
    "Ca",
    "Mg",
    "Na",
    "Cl",
    "HCO3",
    "CO3",
    "CaCO3",
    "KH",
    *TRACE_ELEMENT_KEYS,
    *OXIDE_FERTILIZER_COLS,
    "SiO2",
}

ALLOWED_TARGET_KEYS = {
    "N_total",
    "N_NH4",
    "N_NO3",
    "N_UREA",
    "P",
    "K",
    "Ca",
    "Mg",
    "S",
    "SO4",
    *TRACE_ELEMENT_KEYS,
    "Si",
    "Cl",
    "Na",
    "HCO3",
}

N_FORM_KEYS = {"N_NH4", "N_NO3", "N_UREA"}
FERTILIZER_N_FORM_OUTPUT_KEYS = {
    "NH4": "N_NH4",
    "NO3": "N_NO3",
    "UREA": "N_UREA",
}

OXIDE_ELEMENT_RULES: dict[str, tuple[str, float]] = {
    "P2O5": ("P", 2.0),
    "K2O": ("K", 2.0),
    "CaO": ("Ca", 1.0),
    "MgO": ("Mg", 1.0),
    "Na2O": ("Na", 2.0),
}

FORM_ELEMENT_RULES: dict[str, tuple[str, float]] = {
    "SO4": ("S", 1.0),
    "CO3": ("C", 1.0),
    "SiO2": ("Si", 1.0),
    "Cl": ("Cl", 1.0),
    "Fe": ("Fe", 1.0),
    "Mn": ("Mn", 1.0),
    "Cu": ("Cu", 1.0),
    "Zn": ("Zn", 1.0),
    "B": ("B", 1.0),
    "Mo": ("Mo", 1.0),
}

N_MOLECULE_FORMS: tuple[str, ...] = ("NH4", "NO3")
OXIDE_ELEMENT_FORMS: tuple[str, ...] = tuple(OXIDE_ELEMENT_RULES)
OTHER_ELEMENT_FORMS: tuple[str, ...] = tuple(FORM_ELEMENT_RULES)
DEFAULT_PORTFOLIO_MACRO_KEYS = ("P", "K", "Ca", "Mg", "Si")
DEFAULT_PORTFOLIO_MICRO_KEYS = TRACE_ELEMENT_KEYS
