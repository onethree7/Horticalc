export const DEFAULT_LITERS = 10;
export const DEFAULT_VOLUME_UNIT = "liter";
export const DEFAULT_SOLID_DOSE_UNIT = "gram";
export const DEFAULT_LIQUID_DOSE_UNIT = "milliliter";
export const DEFAULT_THEME = "horticalc-dark";
export const SCALE_STEP = 0.05;

export const FALLBACK_VOLUME_UNITS = [
  { key: "liter", label: "Liter", symbol: "L", liters_per_unit: 1 },
  { key: "us_gallon", label: "US gallon", symbol: "US gal", liters_per_unit: 3.785411784 },
  { key: "imperial_gallon", label: "Imperial gallon", symbol: "Imp gal", liters_per_unit: 4.54609 },
  { key: "cubic_meter", label: "Cubic meter", symbol: "m³", liters_per_unit: 1000 },
];

export const FALLBACK_MASS_UNITS = [
  { key: "gram", label: "Gram", symbol: "g", grams_per_unit: 1 },
  { key: "kilogram", label: "Kilogram", symbol: "kg", grams_per_unit: 1000 },
  { key: "ounce", label: "Ounce", symbol: "oz", grams_per_unit: 28.349523125 },
  { key: "pound", label: "Pound", symbol: "lb", grams_per_unit: 453.59237 },
];

export const FALLBACK_LIQUID_VOLUME_UNITS = [
  { key: "milliliter", label: "Milliliter", symbol: "mL", milliliters_per_unit: 1 },
  { key: "liter", label: "Liter", symbol: "L", milliliters_per_unit: 1000 },
  { key: "us_fluid_ounce", label: "US fluid ounce", symbol: "US fl oz", milliliters_per_unit: 29.5735295625 },
  { key: "imperial_fluid_ounce", label: "Imperial fluid ounce", symbol: "Imp fl oz", milliliters_per_unit: 28.4130625 },
];

export const THEME_STORAGE_KEY = "horticalc.theme";

export const LAST_SOLUTION_CALCULATED_KEY = "last_solution_calculated";
export const SUMMARY_VIEW_KEY = "horticalc.summary_view";
export const ION_NITROGEN_EXPANDED_KEY = "horticalc.ion_n_expanded";
export const SOLVER_AUTO_APPLY_KEY = "horticalc.solver_auto_apply";
export const LAST_FERTILIZERS_ALLOWED_CONTEXT_KEY_PREFIX = "last_fertilizers_allowed::";

export const NUMBER_FORMATTER = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
  useGrouping: false,
});
export const NUTRIENT_FORMATTER = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
  useGrouping: false,
});
export const SOLVER_MAX_FORMATTER = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 6,
  useGrouping: false,
});
export const ION_FORMATTER = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  useGrouping: false,
});
export const NUTRIENT_INTEGER_FORMATTER = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
  useGrouping: false,
});

export const SUMMARY_COLUMN_ORDER = [
  { oxide: "N_total", element: "N_total", oxideHeaderLabelKey: "solver.nTotal", ionHeaderLabelKey: "solver.nTotal" },
  { oxide: "P2O5", element: "P", oxideHeaderLabel: "P2O5", ionHeaderLabel: "P" },
  { oxide: "K2O", element: "K", oxideHeaderLabel: "K2O", ionHeaderLabel: "K" },
  { oxide: "CaO", element: "Ca", oxideHeaderLabel: "CaO", ionHeaderLabel: "Ca" },
  { oxide: "MgO", element: "Mg", oxideHeaderLabel: "MgO", ionHeaderLabel: "Mg" },
  { oxide: "SO4", element: "S", oxideHeaderLabel: "SO4", ionHeaderLabel: "S" },
  { oxide: "Fe", element: "Fe", oxideHeaderLabel: "Fe", ionHeaderLabel: "Fe" },
  { oxide: "Mn", element: "Mn", oxideHeaderLabel: "Mn", ionHeaderLabel: "Mn" },
  { oxide: "Cu", element: "Cu", oxideHeaderLabel: "Cu", ionHeaderLabel: "Cu" },
  { oxide: "Zn", element: "Zn", oxideHeaderLabel: "Zn", ionHeaderLabel: "Zn" },
  { oxide: "B", element: "B", oxideHeaderLabel: "B", ionHeaderLabel: "B" },
  { oxide: "Mo", element: "Mo", oxideHeaderLabel: "Mo", ionHeaderLabel: "Mo" },
  { oxide: "SiO2", element: "Si", oxideHeaderLabel: "SiO2", ionHeaderLabel: "Si" },
  { oxide: "Na2O", element: "Na", oxideHeaderLabel: "Na2O", ionHeaderLabel: "Na" },
  { oxide: "Cl", element: "Cl", oxideHeaderLabel: "Cl", ionHeaderLabel: "Cl" },
  { oxide: "HCO3", element: "HCO3", oxideHeaderLabel: "HCO3", ionHeaderLabel: "HCO3" },
];

export const FALLBACK_SOLVER_CONFIG_DEFINITIONS = [
  {
    key: "solver_model",
    type: "string",
    defaultValue: "nnls_tuning",
    choices: ["mass_nnls", "hierarchical", "nnls_tuning"],
  },
  { key: "relative_weighting", type: "boolean", defaultValue: false },
  { key: "nitrogen_objective_mode", type: "string", defaultValue: "n_total_only" },
  { key: "overshoot_penalty", type: "number", defaultValue: 1, minimum: 0 },
  { key: "irls_max_outer_iter", type: "integer", defaultValue: 4, minimum: 1, maximum: 12 },
  { key: "scale_eps_mg_per_l", type: "number", defaultValue: 1, exclusiveMinimum: 0 },
  { key: "s_objective_enabled", type: "boolean", defaultValue: false },
  { key: "singleton_supplier_enabled", type: "boolean", defaultValue: false },
  { key: "singleton_share_threshold", type: "number", defaultValue: 0.85, minimum: 0, maximum: 1 },
  { key: "singleton_max_regress_pp", type: "number", defaultValue: 0.25, minimum: 0 },
  { key: "singleton_underfill_enabled", type: "boolean", defaultValue: true },
  { key: "singleton_underfill_share_threshold", type: "number", defaultValue: 0.85, minimum: 0, maximum: 1 },
  { key: "singleton_underfill_max_iter", type: "integer", defaultValue: 2, minimum: 1, maximum: 8 },
  { key: "n_total_governor_enabled", type: "boolean", defaultValue: false },
  { key: "n_total_governor_weight", type: "number", defaultValue: 1, minimum: 0 },
];
