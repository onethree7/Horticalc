const fertilizerSelectTableWrap = qs("#fertilizerSelectTableWrap");
const calculatorTableWrap = qs("#calculatorTableWrap");
const calculateButton = qs("#calculateBtn");
const copyCalculatorResultsButton = qs("#copyCalculatorResults");
const copyCalculatorResultsStatus = qs("#copyCalculatorResultsStatus");
const addRowButton = qs("#addFertilizerRow");
const removeRowButton = qs("#removeFertilizerRow");
const waterTableBody = qs("#waterValuesTable tbody");
const waterProfileSelect = qs("#waterProfileSelect");
const waterProfileNameInput = qs("#waterProfileName");
const loadWaterProfileButton = qs("#loadWaterProfile");
const saveWaterProfileButton = qs("#saveWaterProfile");
const resetWaterProfileButton = qs("#resetWaterProfile");
const osmosisPercentInput = qs("#osmosisPercent");
const waterUnitToggle = qs("#waterUnitToggle");
const waterSection = qs("#waterSection");
const npkAllPctValue = qs("#npkAllPct");
const npkPNormValue = qs("#npkPNorm");
const npkNpkPctValue = qs("#npkNpkPct");
const caMgRatioValue = qs("#caMgRatio");
const ionRatioList = qs("#ionRatioList");
const ec18Value = qs("#ec18Value");
const ec25Value = qs("#ec25Value");
const ecWater18Value = qs("#ecWater18Value");
const ecWater25Value = qs("#ecWater25Value");
const profileSectionTitle = qs("#profileSectionTitle");
const profileSectionHint = qs("#profileSectionHint");
const profileSection = qs("#profileSection");
const profileSelect = qs("#profileSelect");
const loadProfileButton = qs("#loadProfile");
const resetProfileButton = qs("#resetProfile");
const profileNameInput = qs("#profileName");
const saveProfileButton = qs("#saveProfile");
const solverProfileActions = qs("#solverProfileActions");
const saveSolverAsRecipeButton = qs("#saveSolverAsRecipe");
const applySolverToCalculatorButton = qs("#applySolverToCalculator");
const calculatorScaleDownButton = qs("#calculatorScaleDown");
const calculatorScaleUpButton = qs("#calculatorScaleUp");
const calculatorScaleValue = qs("#calculatorScaleValue");
const configLitersInput = qs("#configLiters");
const configLitersStatus = qs("#configLitersStatus");
const configVolumeUnitSymbol = qs("#configVolumeUnitSymbol");
const configUnitSummary = qs("#configUnitSummary");
const configVolumeUnitSelect = qs("#configVolumeUnit");
const configSolidDoseUnitSelect = qs("#configSolidDoseUnit");
const configLiquidDoseUnitSelect = qs("#configLiquidDoseUnit");
const themeSelect = qs("#themeSelect");
const languageSelect = qs("#languageSelect");

const waterSummaryTable = qs("#waterSummaryTable");
const oxideSummaryTable = qs("#oxideSummaryTable");
const ionSummaryTable = qs("#ionSummaryTable");
const waterSummaryBadge = qs("#waterSummaryBadge");
const oxideSummaryBadge = qs("#oxideSummaryBadge");
const ionSummaryBadge = qs("#ionSummaryBadge");
const summaryViewToggle = qs("#summaryViewToggle");
const summaryPanels = qsa(".summary-panel[data-summary-panel]");
const ionMeqList = qs("#ionMeqList");
const ionBalanceList = qs("#ionBalanceList");
const calculatorMode = qs("#calculatorMode");
const solverMode = qs("#solverMode");
const fertilizerEditorMode = qs("#fertilizerEditorMode");
const solverTargetsTable = qs("#solverTargetsTable tbody");
const solverAllowedFertilizersSelect = qs("#solverAllowedFertilizers");
const solverAllowedSearchInput = qs("#solverAllowedSearch");
const solverAllowedCount = qs("#solverAllowedCount");
const solverAllowedClearButton = qs("#solverAllowedClear");
const solverAllowedFromRecipeButton = qs("#solverAllowedFromRecipe");
const solverAllowedAllButton = qs("#solverAllowedAll");
const solverAllowedHideInactiveInput = qs("#solverAllowedHideInactive");
const solverOverridesDetails = qs("#solverOverrides");
const solverOverrideSummary = qs("#solverOverrideSummary");
const solverFixedTable = qs("#solverFixedTable tbody");
const solverFertilizersTable = qs("#solverFertilizersTable tbody");
const solverTargetsResultsTableEl = qs("#solverTargetsResultsTable");
const solverTargetsResultsTable = qs("#solverTargetsResultsTable tbody");
const solverTargetsResultsEmpty = qs("#solverTargetsResultsEmpty");
const solverTargetScaleDownButton = qs("#solverTargetScaleDown");
const solverTargetScaleUpButton = qs("#solverTargetScaleUp");
const solverTargetScaleValue = qs("#solverTargetScaleValue");
const solveButton = qs("#solveBtn");
const copySolverResultsButton = qs("#copySolverResults");
const copySolverResultsStatus = qs("#copySolverResultsStatus");
const solverAutoApplyInput = qs("#solverAutoApply");
const solverApplyStatus = qs("#solverApplyStatus");
const applySolverToCalculatorInlineButton = qs("#applySolverToCalculatorInline");
const solverUreaToggle = qs("#solverUreaToggle");
const solverConfigControls = {
  relative_weighting: qs("#solverConfigRelativeWeighting"),
  nitrogen_objective_mode: qs("#solverConfigNitrogenObjectiveMode"),
  overshoot_penalty: qs("#solverConfigOvershootPenalty"),
  irls_max_outer_iter: qs("#solverConfigIrlsMaxOuterIter"),
  scale_eps_mg_per_l: qs("#solverConfigScaleEpsMgPerL"),
  s_objective_enabled: qs("#solverConfigSObjectiveEnabled"),
  singleton_supplier_enabled: qs("#solverConfigSingletonSupplierEnabled"),
  singleton_share_threshold: qs("#solverConfigSingletonShareThreshold"),
  singleton_max_regress_pp: qs("#solverConfigSingletonMaxRegressPp"),
  singleton_underfill_enabled: qs("#solverConfigSingletonUnderfillEnabled"),
  singleton_underfill_share_threshold: qs("#solverConfigSingletonUnderfillShareThreshold"),
  singleton_underfill_max_iter: qs("#solverConfigSingletonUnderfillMaxIter"),
  n_total_governor_enabled: qs("#solverConfigNTotalGovernorEnabled"),
  n_total_governor_weight: qs("#solverConfigNTotalGovernorWeight"),
};
const solverConfigResetDefaultsButton = qs("#solverConfigResetDefaults");
const fertilizerEditorTableWrap = qs("#fertilizerEditorTableWrap");
const fertEditorSearchInput = qs("#fertEditorSearch");
const fertEditorAddRowButton = qs("#fertEditorAddRow");
const fertEditorDeleteRowButton = qs("#fertEditorDeleteRow");
const fertEditorLoadButton = qs("#fertEditorLoad");
const fertEditorSaveButton = qs("#fertEditorSave");
const apiStatus = qs("#apiStatus");
const liveLastCalc = qs("#liveLastCalc");

const DEFAULT_LITERS = 10.0;
const DEFAULT_VOLUME_UNIT = "liter";
const DEFAULT_SOLID_DOSE_UNIT = "gram";
const DEFAULT_LIQUID_DOSE_UNIT = "milliliter";
const FALLBACK_VOLUME_UNITS = [
  { key: "liter", label: "Liter", symbol: "L", liters_per_unit: 1.0 },
  { key: "us_gallon", label: "US gallon", symbol: "US gal", liters_per_unit: 3.785411784 },
  { key: "imperial_gallon", label: "Imperial gallon", symbol: "Imp gal", liters_per_unit: 4.54609 },
  { key: "cubic_meter", label: "Cubic meter", symbol: "m³", liters_per_unit: 1000.0 },
];
const FALLBACK_MASS_UNITS = [
  { key: "gram", label: "Gram", symbol: "g", grams_per_unit: 1.0 },
  { key: "kilogram", label: "Kilogram", symbol: "kg", grams_per_unit: 1000.0 },
  { key: "ounce", label: "Ounce", symbol: "oz", grams_per_unit: 28.349523125 },
  { key: "pound", label: "Pound", symbol: "lb", grams_per_unit: 453.59237 },
];
const FALLBACK_LIQUID_VOLUME_UNITS = [
  { key: "milliliter", label: "Milliliter", symbol: "mL", milliliters_per_unit: 1.0 },
  { key: "liter", label: "Liter", symbol: "L", milliliters_per_unit: 1000.0 },
  { key: "us_fluid_ounce", label: "US fluid ounce", symbol: "US fl oz", milliliters_per_unit: 29.5735295625 },
  { key: "imperial_fluid_ounce", label: "Imperial fluid ounce", symbol: "Imp fl oz", milliliters_per_unit: 28.4130625 },
];
const DEFAULT_THEME = "horticalc-dark";
const FERTILIZER_EDITOR_SEARCH_DELAY_MS = 150;
const SOLVER_ALLOWED_SEARCH_DELAY_MS = 150;
const THEME_STORAGE_KEY = "horticalc.theme";
const THEME_OPTIONS = new Set([
  DEFAULT_THEME,
  "horticalc-light",
  "high-contrast",
  "soil",
  "gch-classic",
  "vt-green",
  "blue-matrix",
]);

let fertilizerOptions = [];
let calculatorRows = [];
let molarMasses = {};
let waterProfiles = [];
let recipeProfiles = [];
let nutrientSolutions = [];
let waterUnit = "mg_l";
let lastCalculation = null;
let calculatorResultCurrent = false;
let lastSolveResult = null;
let recalculateTimer = null;
const calculationRequests = createLatestRequestGate();
const solveRequests = createLatestRequestGate();
const profileRequests = createLatestRequestGate();
const waterProfileRequests = createLatestRequestGate();
let fertilizerSelectTable;
let userPreferences = {};
let preferenceLoadPromise = null;
let preferenceWritePromise = Promise.resolve();
let calculatorTable;
let currentProfileMode = "calculator";
let copySolverStatusTimer = null;
let copyCalculatorStatusTimer = null;
let solverApplyStatusTimer = null;
let fertilizerEditorRows = [];
let fertilizerEditorSelectedIndex = 0;
let fertilizerEditorFilter = "";
let fertilizerEditorSearchTimer = null;
let solverAllowedSearchTimer = null;
let fertilizerEditorTable;
let fertilizerEditorNameWidthPx = 288;
let fertilizerEditorCompKeys = [];
let fertilizerEditorSort = { key: "name", direction: "asc" };
let summaryView = "ion";
let ionNitrogenExpanded = false;
let fertilizerEditorPreferredKeys = [];
let currentLiters = DEFAULT_LITERS;
let volumeUnitDefinitions = [...FALLBACK_VOLUME_UNITS];
let volumeUnit = DEFAULT_VOLUME_UNIT;
let massUnitDefinitions = [...FALLBACK_MASS_UNITS];
let liquidVolumeUnitDefinitions = [...FALLBACK_LIQUID_VOLUME_UNITS];
let solidDoseUnit = DEFAULT_SOLID_DOSE_UNIT;
let liquidDoseUnit = DEFAULT_LIQUID_DOSE_UNIT;
let currentShellView = "fertilizers";

const shellViewConfigs = {
  fertilizers: {
    mode: "calculator",
    anchor: "fertilizers",
  },
  water: {
    mode: "water",
    anchor: "water",
  },
  solver: {
    mode: "solver",
    anchor: "solver",
  },
  editor: {
    mode: "fertilizers",
    anchor: "editor",
  },
};

const solverTargetDefinitions = [
  { key: "N_total", label: "N_total" },
  { key: "N_NH4", label: "N_NH4" },
  { key: "N_NO3", label: "N_NO3" },
  { key: "N_UREA", label: "N_UREA" },
  { key: "P", label: "P" },
  { key: "K", label: "K" },
  { key: "Ca", label: "Ca" },
  { key: "Mg", label: "Mg" },
  { key: "S", label: "S" },
  { key: "Fe", label: "Fe" },
  { key: "Mn", label: "Mn" },
  { key: "Cu", label: "Cu" },
  { key: "Zn", label: "Zn" },
  { key: "B", label: "B" },
  { key: "Mo", label: "Mo" },
  { key: "Si", label: "Si" },
  { key: "Cl", label: "Cl" },
  { key: "Na", label: "Na" },
  { key: "HCO3", label: "HCO3" },
];

const solverTargetValues = Object.fromEntries(
  solverTargetDefinitions.map((field) => [field.key, 0])
);
const solverTargetBaseValues = Object.fromEntries(
  solverTargetDefinitions.map((field) => [field.key, 0])
);
let solverTargetScaleFactor = 1.0;
let calculatorScaleFactor = 1.0;
const SCALE_STEP = 0.05;
const solverAllowedFertilizers = [];
let solverAllowedContext = "global";
let solverAllowedFilter = "";
let solverAllowedHideInactive = false;
const solverFixedGrams = {};

const waterFieldDefinitions = [
  { key: "NH4", labelKey: "waterField.NH4", label: "Ammonium as NH4" },
  { key: "NO3", labelKey: "waterField.NO3", label: "Nitrate as NO3" },
  { key: "PO4", labelKey: "waterField.PO4", label: "Phosphate as PO4" },
  { key: "P", labelKey: "waterField.P", label: "Phosphorus as P" },
  { key: "K", labelKey: "waterField.K", label: "Potassium as K" },
  { key: "Ca", labelKey: "waterField.Ca", label: "Calcium as Ca" },
  { key: "Mg", labelKey: "waterField.Mg", label: "Magnesium as Mg" },
  { key: "Na", labelKey: "waterField.Na", label: "Sodium as Na" },
  { key: "SO4", labelKey: "waterField.SO4", label: "Sulfate as SO4" },
  { key: "S", labelKey: "waterField.S", label: "Sulfur as S" },
  { key: "Fe", labelKey: "waterField.Fe", label: "Iron as Fe" },
  { key: "Mn", labelKey: "waterField.Mn", label: "Manganese as Mn" },
  { key: "Cu", labelKey: "waterField.Cu", label: "Copper as Cu" },
  { key: "Zn", labelKey: "waterField.Zn", label: "Zinc as Zn" },
  { key: "B", labelKey: "waterField.B", label: "Boron as B" },
  { key: "Mo", labelKey: "waterField.Mo", label: "Molybdenum as Mo" },
  { key: "Cl", labelKey: "waterField.Cl", label: "Chloride as Cl" },
  { key: "HCO3", labelKey: "waterField.HCO3", label: "Carbonate alkalinity as HCO3" },
  { key: "CO3", labelKey: "waterField.CO3", label: "Carbonate as CO3" },
  { key: "CaCO3", labelKey: "waterField.CaCO3", label: "Total carbonate hardness as CaCO3" },
  { key: "KH", labelKey: "waterField.KH", label: "Carbonate hardness as °KH" },
  { key: "SiO2", labelKey: "waterField.SiO2", label: "Silicon as SiO2" },
];

const waterValues = Object.fromEntries(waterFieldDefinitions.map((field) => [field.key, 0]));
const numberFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
  useGrouping: false,
});
const nutrientFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
  useGrouping: false,
});
const solverMaxFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 6,
  useGrouping: false,
});
const ionFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  useGrouping: false,
});
const nutrientIntegerFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
  useGrouping: false,
});
const LAST_FERTILIZERS_ALLOWED_CONTEXT_KEY_PREFIX = "last_fertilizers_allowed::";
const LAST_SOLUTION_CALCULATED_KEY = "last_solution_calculated";
const SUMMARY_VIEW_KEY = "horticalc.summary_view";
const SOLVER_AUTO_APPLY_KEY = "horticalc.solver_auto_apply";
const NITROGEN_OBJECTIVE_TOTAL_ONLY = "n_total_only";
const NITROGEN_OBJECTIVE_FORMS_ONLY = "n_forms_only";
const i18n = window.HorticalcI18n || {
  t: (key, params = {}) => {
    let text = String(key);
    Object.entries(params).forEach(([paramKey, value]) => {
      text = text.replaceAll(`{${paramKey}}`, String(value));
    });
    return text;
  },
  setLocale: () => {},
  getLocale: () => "de",
  applyDomTranslations: () => {},
};
const nutrientIntegerKeys = new Set(["N_total", "P", "K", "Ca", "Mg", "S"]);
const nutrientTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "Si"]);
const oxideIntegerKeys = new Set([
  "N_total",
  "P2O5",
  "K2O",
  "CaO",
  "MgO",
  "SO4",
]);
const oxideTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "SiO2"]);
const carbonateHelperKeys = new Set(["CO3", "CaCO3", "KH"]);
const waterHelperKeys = new Set(["S", ...carbonateHelperKeys]);
// THE ONLY ALLOWED HARDCODED CONVERSION FOR UI OUTSIDE OF CORE.
const summaryColumnOrder = [
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
const summaryLabelWidth = "12rem";
const ION_NITROGEN_EXPANDED_KEY = "horticalc.ion_n_expanded";

const FALLBACK_SOLVER_CONFIG_DEFINITIONS = [
  { key: "relative_weighting", type: "boolean", defaultValue: false },
  { key: "nitrogen_objective_mode", type: "string", defaultValue: NITROGEN_OBJECTIVE_TOTAL_ONLY },
  { key: "overshoot_penalty", type: "number", defaultValue: 1.0 },
  { key: "irls_max_outer_iter", type: "integer", defaultValue: 4 },
  { key: "scale_eps_mg_per_l", type: "number", defaultValue: 1.0 },
  { key: "s_objective_enabled", type: "boolean", defaultValue: false },
  { key: "singleton_supplier_enabled", type: "boolean", defaultValue: false },
  { key: "singleton_share_threshold", type: "number", defaultValue: 0.85 },
  { key: "singleton_max_regress_pp", type: "number", defaultValue: 0.25 },
  { key: "singleton_underfill_enabled", type: "boolean", defaultValue: true },
  { key: "singleton_underfill_share_threshold", type: "number", defaultValue: 0.85 },
  { key: "singleton_underfill_max_iter", type: "integer", defaultValue: 2 },
  { key: "n_total_governor_enabled", type: "boolean", defaultValue: false },
  { key: "n_total_governor_weight", type: "number", defaultValue: 1.0 },
];
let solverConfigDefinitions = [...FALLBACK_SOLVER_CONFIG_DEFINITIONS];

const profileConfigs = {
  calculator: {
    titleKey: "profile.recipeTitle",
    hintKey: "profile.recipeHint",
  },
  solver: {
    titleKey: "profile.targetTitle",
    hintKey: "profile.targetHint",
  },
};
