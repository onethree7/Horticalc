SOLVER_TARGET_DEFINITIONS = (
    {"key": "N_total", "label": "N_total"},
    {"key": "N_NH4", "label": "N_NH4"},
    {"key": "N_NO3", "label": "N_NO3"},
    {"key": "N_UREA", "label": "N_UREA"},
    {"key": "P", "label": "P"},
    {"key": "K", "label": "K"},
    {"key": "Ca", "label": "Ca"},
    {"key": "Mg", "label": "Mg"},
    {"key": "S", "label": "S"},
    {"key": "SO4", "label": "SO4"},
    {"key": "Fe", "label": "Fe"},
    {"key": "Mn", "label": "Mn"},
    {"key": "Cu", "label": "Cu"},
    {"key": "Zn", "label": "Zn"},
    {"key": "B", "label": "B"},
    {"key": "Mo", "label": "Mo"},
    {"key": "Si", "label": "Si"},
    {"key": "Cl", "label": "Cl"},
    {"key": "Na", "label": "Na"},
    {"key": "HCO3", "label": "HCO3"},
)

SOLVER_TARGET_KEYS = frozenset(entry["key"] for entry in SOLVER_TARGET_DEFINITIONS)
