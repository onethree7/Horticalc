const qs = (selector, root = document) => root.querySelector(selector);
const qsa = (selector, root = document) => root.querySelectorAll(selector);

const fertilizerSelectTableWrap = qs("#fertilizerSelectTableWrap");
const calculatorTableWrap = qs("#calculatorTableWrap");
const calculateButton = qs("#calculateBtn");
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
const modeToggleInputs = qsa('input[name="modeToggle"]');
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
const solverPhosphateSelect = qs("#solverPhosphate");
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
const DEFAULT_THEME = "horticalc-dark";
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
const selectedFertilizers = [{ name: "", liquid: false, weight: "" }];
const fertilizerAmounts = [0];
let molarMasses = {};
let waterProfiles = [];
let recipeProfiles = [];
let nutrientSolutions = [];
let waterUnit = "mg_l";
let lastCalculation = null;
let lastSolveResult = null;
let recalculateTimer = null;
let fertilizerSelectTable;
let userPreferences = {};
let preferenceLoadPromise = null;
let calculatorTable;
let currentProfileMode = "calculator";
let activeMode = "calculator";
let copySolverStatusTimer = null;
let solverApplyStatusTimer = null;
let fertilizerEditorRows = [];
let fertilizerEditorSelectedIndex = 0;
let fertilizerEditorFilter = "";
let fertilizerEditorTable;
let fertilizerEditorNameWidthPx = 288;
let fertilizerEditorCompKeys = [];
let fertilizerEditorSort = { key: "name", direction: "asc" };
let summaryView = "ion";
let ionNitrogenExpanded = false;
let fertilizerEditorPreferredKeys = [];
let activeShellView = "fertilizers";
let currentLiters = DEFAULT_LITERS;

const shellViewConfigs = {
  fertilizers: {
    mode: "calculator",
    anchor: "fertilizers",
    labelKey: "workflow.calculatorUpper",
  },
  water: {
    mode: "water",
    anchor: "water",
    labelKey: "workflow.waterUpper",
  },
  solver: {
    mode: "solver",
    anchor: "solver",
    labelKey: "workflow.solverUpper",
  },
  editor: {
    mode: "fertilizers",
    anchor: "editor",
    labelKey: "workflow.editorUpper",
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
const calculatorBaseAmounts = [0];
let solverTargetScaleFactor = 1.0;
let calculatorScaleFactor = 1.0;
const SCALE_STEP = 0.05;
const solverAllowedFertilizers = [];
let solverAllowedContext = "global";
let solverAllowedFilter = "";
let solverAllowedHideInactive = false;
const solverFixedGrams = {};

const waterFieldDefinitions = [
  { key: "NH4", labelKey: "waterField.NH4", label: "Ammonium in NH4" },
  { key: "NO3", labelKey: "waterField.NO3", label: "Nitrat in NO3" },
  { key: "PO4", labelKey: "waterField.PO4", label: "Phosphat in PO4" },
  { key: "P", labelKey: "waterField.P", label: "Phosphor in P" },
  { key: "K", labelKey: "waterField.K", label: "Kalium in K" },
  { key: "Ca", labelKey: "waterField.Ca", label: "Calcium in Ca" },
  { key: "Mg", labelKey: "waterField.Mg", label: "Magnesium in Mg" },
  { key: "Na", labelKey: "waterField.Na", label: "Natrium in Na" },
  { key: "SO4", labelKey: "waterField.SO4", label: "Sulfat in SO4" },
  { key: "S", labelKey: "waterField.S", label: "Schwefel in S" },
  { key: "Fe", labelKey: "waterField.Fe", label: "Eisen in Fe" },
  { key: "Mn", labelKey: "waterField.Mn", label: "Mangan in Mn" },
  { key: "Cu", labelKey: "waterField.Cu", label: "Kupfer in Cu" },
  { key: "Zn", labelKey: "waterField.Zn", label: "Zink in Zn" },
  { key: "B", labelKey: "waterField.B", label: "Bor in B" },
  { key: "Mo", labelKey: "waterField.Mo", label: "Molybdän in Mo" },
  { key: "Cl", labelKey: "waterField.Cl", label: "Chlor in Cl" },
  { key: "HCO3", labelKey: "waterField.HCO3", label: "Carbonate in HCO3" },
  { key: "CO3", labelKey: "waterField.CO3", label: "Carbonat in CO3" },
  { key: "CaCO3", labelKey: "waterField.CaCO3", label: "Gesamtcarbonathärte in CaCO3" },
  { key: "KH", labelKey: "waterField.KH", label: "Carbonathärte in °KH" },
  { key: "SiO2", labelKey: "waterField.SiO2", label: "Silicium in SiO2" },
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
const fertilizerTraceFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 4,
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
const t = (key, params) => i18n.t(key, params);
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
function applyWaterHelpers(values) {
  const updatedKeys = new Set();
  if (!values || typeof values !== "object") {
    return updatedKeys;
  }

  const mm = (key) => getMolarMass(key) || null;
  const hco3FromCo3 = (mgPerL) => {
    const mmCo3 = mm("CO3");
    const mmHco3 = mm("HCO3");
    return mgPerL && mmCo3 && mmHco3 ? (mgPerL * mmHco3) / mmCo3 : 0;
  };
  const hco3FromCaco3 = (mgPerL) => {
    const mmCaco3 = mm("CaCO3");
    const mmHco3 = mm("HCO3");
    return mgPerL && mmCaco3 && mmHco3 ? (mgPerL * mmHco3) / (mmCaco3 / 2) : 0;
  };
  const hco3FromKh = (dkh) => (dkh ? hco3FromCaco3(dkh * 17.848) : 0);
  const so4FromS = (mgPerL) => {
    const mmSo4 = mm("SO4");
    const mmS = mm("S");
    return mgPerL && mmSo4 && mmS ? (mgPerL * mmSo4) / mmS : 0;
  };

  const helperHco3 = hco3FromCo3(values.CO3) + hco3FromCaco3(values.CaCO3) + hco3FromKh(values.KH);
  if (helperHco3 > 0) {
    values.HCO3 = helperHco3;
    values.CO3 = 0;
    values.CaCO3 = 0;
    values.KH = 0;
    updatedKeys.add("HCO3");
    updatedKeys.add("CO3");
    updatedKeys.add("CaCO3");
    updatedKeys.add("KH");
  }

  const so4Value = so4FromS(values.S || 0);
  if (so4Value > 0) {
    values.SO4 = so4Value;
    values.S = 0;
    updatedKeys.add("SO4");
    updatedKeys.add("S");
  }

  return updatedKeys;
}
const summaryColumnOrder = [
  { oxide: "N_total", element: "N_total", oxideHeaderLabel: "N-Σ", ionHeaderLabel: "N-Σ" },
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

function apiBase() {
  return "";
}

function lsGet(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw);
  } catch (error) {
    return fallback;
  }
}

function lsSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    // ignore storage errors
  }
}

function normalizeTheme(theme) {
  return THEME_OPTIONS.has(theme) ? theme : DEFAULT_THEME;
}

function applyTheme(theme) {
  const nextTheme = normalizeTheme(theme);
  document.body.dataset.theme = nextTheme;
  if (themeSelect) {
    themeSelect.value = nextTheme;
  }
  return nextTheme;
}

function loadPreferences() {
  if (!preferenceLoadPromise) {
    preferenceLoadPromise = fetch(`${apiBase()}/preferences`)
      .then((response) => (response.ok ? response.json() : {}))
      .then((preferences) => {
        userPreferences = preferences && typeof preferences === "object" ? preferences : {};
        return userPreferences;
      })
      .catch(() => userPreferences);
  }
  return preferenceLoadPromise;
}

function persistPreferences(updates) {
  userPreferences = { ...userPreferences, ...updates };
  return fetch(`${apiBase()}/preferences`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
    keepalive: true,
  })
    .then((response) => (response.ok ? response.json() : userPreferences))
    .then((preferences) => {
      userPreferences = preferences && typeof preferences === "object" ? preferences : userPreferences;
      return userPreferences;
    })
    .catch(() => userPreferences);
}

async function initializeThemeControl() {
  let themeChanged = false;
  const activeTheme = applyTheme(lsGet(THEME_STORAGE_KEY, DEFAULT_THEME));
  lsSet(THEME_STORAGE_KEY, activeTheme);
  if (!themeSelect) {
    return;
  }
  themeSelect.addEventListener("change", (event) => {
    themeChanged = true;
    const nextTheme = applyTheme(event.target.value);
    lsSet(THEME_STORAGE_KEY, nextTheme);
    persistPreferences({ theme: nextTheme });
  });
  try {
    const preferences = await loadPreferences();
    if (themeChanged) {
      return;
    }
    const savedTheme = applyTheme(preferences.theme || activeTheme);
    lsSet(THEME_STORAGE_KEY, savedTheme);
  } catch (error) {
    // Browser storage remains the fallback when the preference API is unavailable.
  }
}

function initializeLanguageControl() {
  i18n.setLocale(i18n.getLocale(), { persist: false });
  if (!languageSelect) {
    return;
  }
  languageSelect.value = i18n.getLocale();
  languageSelect.addEventListener("change", (event) => {
    i18n.setLocale(event.target.value);
  });
}

function parseDecimalInput(raw) {
  const s = String(raw ?? "").trim();
  if (!s) {
    return null;
  }
  const n = Number(s.replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

function decimalInputValue(raw, fallback = 0) {
  const parsed = parseDecimalInput(raw);
  return parsed === null ? fallback : parsed;
}

function normalizeDecimalInputElement(input, value, fallback = "0") {
  input.value = Number.isFinite(value) ? String(value) : fallback;
}

function normalizeSolverConfigDefinitions(definitions = []) {
  if (!Array.isArray(definitions)) {
    return [...FALLBACK_SOLVER_CONFIG_DEFINITIONS];
  }
  const normalized = definitions
    .map((definition) => ({
      key: String(definition?.key || ""),
      type: String(definition?.type || ""),
      defaultValue: Object.prototype.hasOwnProperty.call(definition || {}, "default")
        ? definition.default
        : definition?.defaultValue,
    }))
    .filter(
      (definition) =>
        definition.key &&
        solverConfigControls[definition.key] &&
        (["boolean", "number", "integer"].includes(definition.type) ||
          (definition.key === "nitrogen_objective_mode" && definition.type === "string"))
    );
  if (!normalized.length) {
    return [...FALLBACK_SOLVER_CONFIG_DEFINITIONS];
  }
  const seenKeys = new Set(normalized.map((definition) => definition.key));
  FALLBACK_SOLVER_CONFIG_DEFINITIONS.forEach((definition) => {
    if (!seenKeys.has(definition.key) && solverConfigControls[definition.key]) {
      normalized.push({ ...definition });
    }
  });
  return normalized;
}

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

function validLiters(value) {
  const liters = parseDecimalInput(value);
  return Number.isFinite(liters) && liters > 0 ? liters : DEFAULT_LITERS;
}

function formatLiters(value) {
  const liters = validLiters(value);
  return Number.isInteger(liters) ? String(liters) : String(Math.round(liters * 10) / 10);
}

function updateLitersDisplay() {
  if (configLitersInput) {
    configLitersInput.value = formatLiters(currentLiters);
  }
  if (configLitersStatus) {
    configLitersStatus.setAttribute("aria-label", `${t("config.solutionLiters")} ${formatLiters(currentLiters)} L`);
  }
}

function scaleCurrentBatch(fromLiters, toLiters) {
  const oldLiters = validLiters(fromLiters);
  const newLiters = validLiters(toLiters);
  const factor = newLiters / oldLiters;
  fertilizerAmounts.forEach((amount, index) => {
    const scaled = roundScaledValue((Number(amount) || 0) * factor);
    fertilizerAmounts[index] = scaled;
    calculatorBaseAmounts[index] =
      calculatorScaleFactor > 0 ? roundScaledValue(scaled / calculatorScaleFactor) : scaled;
  });
  Object.keys(solverFixedGrams).forEach((key) => {
    solverFixedGrams[key] = roundScaledValue((Number(solverFixedGrams[key]) || 0) * factor);
  });
}

function setCurrentLiters(value, { scaleBatch = false, recalculate = false, invalidateSolver = true } = {}) {
  const nextLiters = validLiters(value);
  const previousLiters = currentLiters;
  if (scaleBatch && previousLiters > 0 && nextLiters !== previousLiters) {
    scaleCurrentBatch(previousLiters, nextLiters);
    renderCalculatorTable();
    renderSolverFixedTable();
  }
  currentLiters = nextLiters;
  updateLitersDisplay();
  if (invalidateSolver) {
    renderSolverResults(null);
  }
  if (recalculate) {
    scheduleRecalculate();
  }
}

function buildSolverConfigPayload() {
  const config = {};
  solverConfigDefinitions.forEach((definition) => {
    const input = solverConfigControls[definition.key];
    if (!input) {
      return;
    }
    if (definition.key === "nitrogen_objective_mode") {
      config[definition.key] = input.checked
        ? NITROGEN_OBJECTIVE_TOTAL_ONLY
        : NITROGEN_OBJECTIVE_FORMS_ONLY;
      return;
    }
    if (definition.type === "boolean") {
      config[definition.key] = Boolean(input.checked);
      return;
    }
    const rawValue = parseDecimalInput(input.value);
    if (rawValue === null) {
      return;
    }
    config[definition.key] = definition.type === "integer" ? Math.max(1, Math.round(rawValue)) : rawValue;
  });
  return config;
}

function sanitizeSolverConfig(config = {}) {
  const allowedKeys = new Set(solverConfigDefinitions.map((definition) => definition.key));
  const sanitized = {};
  Object.entries(config || {}).forEach(([key, value]) => {
    if (allowedKeys.has(key)) {
      sanitized[key] = value;
    }
  });
  return sanitized;
}

function applySolverConfig(config = {}) {
  const sanitized = sanitizeSolverConfig(config);
  solverConfigDefinitions.forEach((definition) => {
    const input = solverConfigControls[definition.key];
    if (!input) {
      return;
    }
    const value = Object.prototype.hasOwnProperty.call(sanitized, definition.key)
      ? sanitized[definition.key]
      : definition.defaultValue;
    if (definition.key === "nitrogen_objective_mode") {
      input.checked = value !== NITROGEN_OBJECTIVE_FORMS_ONLY;
    } else if (definition.type === "boolean") {
      input.checked = Boolean(value);
    } else {
      input.value = String(value);
    }
  });
}

function createSelect(options, onChange) {
  const select = document.createElement("select");
  const emptyOption = document.createElement("option");
  emptyOption.value = "";
  emptyOption.textContent = t("common.selectEmpty");
  select.appendChild(emptyOption);

  options.forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt.name;
    option.textContent = opt.name;
    select.appendChild(option);
  });

  select.addEventListener("change", (event) => onChange(event.target.value));
  return select;
}

function createTable({ id, className, colgroupClasses, headerCells }) {
  const table = document.createElement("table");
  table.id = id;
  table.className = className;

  const colgroup = document.createElement("colgroup");
  colgroupClasses.forEach((colClass) => {
    const col = document.createElement("col");
    col.className = colClass;
    colgroup.appendChild(col);
  });
  table.appendChild(colgroup);

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headerCells.forEach((cell) => {
    const th = document.createElement("th");
    const label = cell.labelKey ? t(cell.labelKey) : cell.label;
    if (cell.onClick) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "table-sort-button";
      button.textContent = label;
      button.addEventListener("click", cell.onClick);
      th.classList.add("is-sortable");
      th.setAttribute("aria-sort", cell.sortDirection || "none");
      th.appendChild(button);
    } else {
      if (cell.labelKey) {
        th.dataset.i18n = cell.labelKey;
      }
      th.textContent = label;
    }
    if (cell.colSpan) {
      th.colSpan = cell.colSpan;
    }
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  table.appendChild(tbody);

  return { table, tbody };
}

function initializeFertilizerTables() {
  const selectTable = createTable({
    id: "fertilizerSelectTable",
    className: "grid grid--form grid--fertilizer",
    colgroupClasses: ["col-index", "col-name", "col-liquid", "col-weight"],
    headerCells: [
      { label: "#" },
      { labelKey: "calculator.fertilizerDropdown", label: "Dünger (Dropdown)" },
      { labelKey: "common.productType", label: "Typ" },
      { labelKey: "common.mass", label: "Masse" },
    ],
  });
  fertilizerSelectTableWrap.appendChild(selectTable.table);
  fertilizerSelectTable = selectTable.tbody;

  const calculator = createTable({
    id: "calculatorTable",
    className: "grid grid--form grid--fertilizer",
    colgroupClasses: ["col-index", "col-name", "col-form", "col-amount"],
    headerCells: [
      { label: "#" },
      { labelKey: "editor.fertilizerName", label: "Düngername", colSpan: 2 },
      { labelKey: "common.grams", label: "Gramm/ml" },
    ],
  });
  calculatorTableWrap.appendChild(calculator.table);
  calculatorTable = calculator.tbody;
}

function renderTableRows(tableBody, rowCount, buildRow) {
  tableBody.innerHTML = "";
  for (let i = 0; i < rowCount; i += 1) {
    tableBody.appendChild(buildRow(i));
  }
}

function setMode(mode) {
  const isSolver = mode === "solver";
  const isEditor = mode === "fertilizers";
  const isWater = mode === "water";
  calculatorMode.classList.toggle("is-hidden", isSolver || isEditor || isWater);
  solverMode.classList.toggle("is-hidden", !isSolver);
  fertilizerEditorMode.classList.toggle("is-hidden", !isEditor);
  waterSection.classList.toggle("is-hidden", !isWater);
  profileSection.classList.toggle("is-hidden", isEditor || isWater);
  activeMode = mode;
  updateModeToggleUI();
  if (!isEditor && !isWater) {
    setProfileMode(mode);
  }
}

function setApiStatus(message, state = "ready") {
  if (!apiStatus) {
    return;
  }
  apiStatus.textContent = message;
  apiStatus.dataset.state = state;
}

function refreshApiStatusLabel() {
  if (!apiStatus) {
    return;
  }
  if (apiStatus.dataset.state === "loading") {
    setApiStatus(t("status.loadingData"), "loading");
  } else if (apiStatus.dataset.state === "error") {
    setApiStatus(t("status.checking"), "error");
  } else {
    setApiStatus(t("status.apiReady"), "ready");
  }
}

function syncModeRadio(mode) {
  modeToggleInputs.forEach((input) => {
    input.checked = input.value === mode;
  });
  updateModeToggleUI();
}

function setActiveShellView(view) {
  activeShellView = view;
  qsa("[data-shell-view]").forEach((button) => {
    const isActive = button.dataset.shellView === view;
    button.classList.toggle("is-active", isActive);
    if (isActive) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  });
}

function scrollToPanelAnchor(anchor, shouldFocus = true) {
  const target = qs(`[data-panel-anchor="${anchor}"]`);
  if (!target) {
    return;
  }
  const scroller = target.closest(".workspace");
  if (scroller) {
    const scrollerTop = scroller.getBoundingClientRect().top;
    const targetTop = target.getBoundingClientRect().top;
    const scrollTop = scroller.scrollTop + targetTop - scrollerTop - 12;
    scroller.scrollTo({ top: Math.max(0, scrollTop), behavior: "smooth" });
  } else {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  if (shouldFocus) {
    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  }
}

function showShellView(view, options = {}) {
  const config = shellViewConfigs[view] || shellViewConfigs.fertilizers;
  const shouldScroll = options.scroll !== false;
  syncModeRadio(config.mode);
  setMode(config.mode);
  setActiveShellView(view);
  updateLiveResultBar();
  if (shouldScroll) {
    window.setTimeout(() => scrollToPanelAnchor(config.anchor), 0);
  }
}

function bindShellNavigation() {
  qsa("[data-shell-view]").forEach((button) => {
    if (button.dataset.shellBound === "true") {
      return;
    }
    button.dataset.shellBound = "true";
    button.addEventListener("click", () => {
      showShellView(button.dataset.shellView || "fertilizers");
    });
  });
}

function updateLiveResultBar(data = lastCalculation) {
  if (!liveLastCalc) {
    return;
  }
  if (!data) {
    liveLastCalc.textContent = t("status.noCalculation");
    return;
  }

  liveLastCalc.textContent = t("status.updatedAt", {
    time: new Date().toLocaleTimeString(i18n.getLocale()),
  });
}

function updateModeToggleUI() {
  modeToggleInputs.forEach((input) => {
    const label = input.closest("label");
    if (!label) {
      return;
    }
    label.classList.toggle("is-active", input.checked);
  });
}

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

function setProfileMode(mode) {
  currentProfileMode = mode === "solver" ? "solver" : "calculator";
  const config = profileConfigs[currentProfileMode];
  profileSectionTitle.dataset.i18n = config.titleKey;
  profileSectionHint.dataset.i18n = config.hintKey;
  profileSectionTitle.textContent = t(config.titleKey);
  profileSectionHint.textContent = t(config.hintKey);
  solverProfileActions.classList.toggle("is-hidden", currentProfileMode !== "solver");
  renderProfileOptions();
}

function renderProfileOptions() {
  profileSelect.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = t("common.selectEmpty");
  profileSelect.appendChild(empty);

  const profiles = currentProfileMode === "solver" ? nutrientSolutions : recipeProfiles;
  profiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.filename;
    option.textContent = profile.name || profile.filename;
    profileSelect.appendChild(option);
  });
}

function renderSolverTargetsTable() {
  solverTargetsTable.innerHTML = "";
  solverTargetDefinitions.forEach((field) => {
    const row = document.createElement("tr");

    const labelCell = document.createElement("td");
    labelCell.textContent = field.labelKey ? t(field.labelKey) : field.label;

    const valueCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.min = "0";
    input.step = "0.1";
    input.value = solverTargetValues[field.key] || 0;
    input.addEventListener("input", (event) => {
      const rawValue = Math.max(0, decimalInputValue(event.target.value));
      solverTargetValues[field.key] = rawValue;
      solverTargetBaseValues[field.key] =
        solverTargetScaleFactor > 0 ? roundScaledValue(rawValue / solverTargetScaleFactor) : 0;
    });
    input.addEventListener("change", () => {
      normalizeDecimalInputElement(input, solverTargetValues[field.key]);
    });
    valueCell.appendChild(input);

    row.append(labelCell, valueCell);
    solverTargetsTable.appendChild(row);
  });
}

function roundScaledValue(value) {
  return Math.round(value * 1000) / 1000;
}

function roundScaleFactor(value) {
  return Math.round(value * 100) / 100;
}

function updateScaleDisplay(displayEl, factor) {
  if (displayEl) {
    displayEl.textContent = `${factor.toFixed(2)}x`;
  }
}

function applyScaleFactor({
  nextFactor,
  definitions,
  getBaseValue,
  setScaledValue,
  setFactor,
  render,
  displayEl,
}) {
  const factor = Math.max(0, roundScaleFactor(nextFactor));
  setFactor(factor);
  definitions.forEach((definition) => {
    const baseValue = getBaseValue(definition) || 0;
    const scaledValue = roundScaledValue(baseValue * factor);
    setScaledValue(definition, Math.max(0, scaledValue));
  });
  updateScaleDisplay(displayEl, factor);
  render();
}

function updateSolverTargetScaleDisplay() {
  updateScaleDisplay(solverTargetScaleValue, solverTargetScaleFactor);
}

function applySolverTargetScaleFactor(nextFactor) {
  applyScaleFactor({
    nextFactor,
    definitions: solverTargetDefinitions,
    getBaseValue: (field) => solverTargetBaseValues[field.key],
    setScaledValue: (field, value) => {
      solverTargetValues[field.key] = value;
    },
    setFactor: (factor) => {
      solverTargetScaleFactor = factor;
    },
    render: renderSolverTargetsTable,
    displayEl: solverTargetScaleValue,
  });
}

function updateCalculatorScaleDisplay() {
  updateScaleDisplay(calculatorScaleValue, calculatorScaleFactor);
}

function applyCalculatorScaleFactor(nextFactor) {
  const definitions = fertilizerAmounts.map((_, index) => index);
  applyScaleFactor({
    nextFactor,
    definitions,
    getBaseValue: (index) => calculatorBaseAmounts[index],
    setScaledValue: (index, value) => {
      fertilizerAmounts[index] = value;
    },
    setFactor: (factor) => {
      calculatorScaleFactor = factor;
    },
    render: renderCalculatorTable,
    displayEl: calculatorScaleValue,
  });
  scheduleRecalculate();
}

function bindScaleButtons(downButton, upButton, currentFactor, applyFactor) {
  if (downButton) {
    downButton.addEventListener("click", () => {
      applyFactor(currentFactor() - SCALE_STEP);
    });
  }
  if (upButton) {
    upButton.addEventListener("click", () => {
      applyFactor(currentFactor() + SCALE_STEP);
    });
  }
}

function buildFertilizerCompKeys(fertilizers) {
  const keySet = new Set();
  const keyLookup = new Map();
  fertilizers.forEach((fert) => {
    Object.keys(fert.comp || {}).forEach((key) => {
      keySet.add(key);
      const normalized = key.trim().toUpperCase();
      if (!keyLookup.has(normalized)) {
        keyLookup.set(normalized, key);
      }
    });
  });
  const ordered = [];
  fertilizerEditorPreferredKeys.forEach((key) => {
    const normalized = key.trim().toUpperCase();
    const matchedKey = keyLookup.get(normalized);
    if (matchedKey && keySet.has(matchedKey)) {
      ordered.push(matchedKey);
      keySet.delete(matchedKey);
    }
  });
  ordered.push(...Array.from(keySet).sort((a, b) => a.localeCompare(b)));
  return ordered;
}

function setFertilizerEditorData(fertilizers) {
  fertilizerEditorRows = (fertilizers || []).map((fert) => ({
    name: fert.name || "",
    liquid: Boolean(fert.liquid),
    weight_factor: Number.isFinite(fert.weight_factor) ? fert.weight_factor : null,
    comp: { ...(fert.comp || {}) },
  }));
  fertilizerEditorSelectedIndex = 0;
  fertilizerEditorCompKeys = buildFertilizerCompKeys(fertilizerEditorRows);
  renderFertilizerEditor();
}

function focusEditorInput(rowIndex, field, compKey) {
  if (!fertilizerEditorTableWrap) {
    return;
  }
  let selector = `input[data-row-index="${rowIndex}"][data-field="${field}"]`;
  if (compKey) {
    selector += `[data-comp-key="${compKey}"]`;
  }
  const input = qs(selector, fertilizerEditorTableWrap);
  if (input) {
    input.focus();
  }
}

function setSelectedEditorRow(editorIndex) {
  fertilizerEditorSelectedIndex = editorIndex;
  if (!fertilizerEditorTable) {
    return;
  }
  const rows = Array.from(qsa("tr[data-editor-index]", fertilizerEditorTable));
  rows.forEach((row) => {
    row.classList.toggle("is-selected", Number(row.dataset.editorIndex) === editorIndex);
  });
}

function handleEditorEnterKey(event) {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  const input = event.target;
  const colIndex = Number(input.dataset.colIndex);
  const row = input.closest("tr");
  if (!row || Number.isNaN(colIndex)) {
    return;
  }
  const nextInRow = qs(`input[data-col-index="${colIndex + 1}"]`, row);
  if (nextInRow) {
    nextInRow.focus();
    return;
  }
  const nextRow = row.nextElementSibling;
  if (!nextRow) {
    return;
  }
  const nextRowInput = qs(`input[data-col-index="${colIndex}"]`, nextRow);
  if (nextRowInput) {
    nextRowInput.focus();
  }
}

function fertilizerEditorSortValue(row, key) {
  if (key.startsWith("comp:")) {
    return Number(row.comp?.[key.slice(5)]);
  }
  if (key === "weight_factor") {
    return row.weight_factor === null ? Number.NaN : Number(row.weight_factor);
  }
  if (key === "liquid") {
    return row.liquid ? 1 : 0;
  }
  return String(row[key] || "").trim();
}

function compareFertilizerEditorRows(left, right) {
  const { key, direction } = fertilizerEditorSort;
  const leftValue = fertilizerEditorSortValue(left.row, key);
  const rightValue = fertilizerEditorSortValue(right.row, key);
  const leftMissing = leftValue === "" || (typeof leftValue === "number" && !Number.isFinite(leftValue));
  const rightMissing = rightValue === "" || (typeof rightValue === "number" && !Number.isFinite(rightValue));
  if (leftMissing !== rightMissing) {
    return leftMissing ? 1 : -1;
  }
  let comparison = 0;
  if (typeof leftValue === "number" && typeof rightValue === "number") {
    comparison = leftValue - rightValue;
  } else {
    comparison = String(leftValue).localeCompare(String(rightValue), i18n.getLocale?.() || undefined, {
      numeric: true,
      sensitivity: "base",
    });
  }
  if (comparison === 0) {
    comparison = left.index - right.index;
  }
  return direction === "desc" ? -comparison : comparison;
}

function setFertilizerEditorSort(key) {
  fertilizerEditorSort = {
    key,
    direction: fertilizerEditorSort.key === key && fertilizerEditorSort.direction === "asc" ? "desc" : "asc",
  };
  renderFertilizerEditor();
}

function fertilizerEditorHeader(label, key, labelKey = null) {
  const active = fertilizerEditorSort.key === key;
  return {
    label,
    labelKey,
    onClick: () => setFertilizerEditorSort(key),
    sortDirection: active ? `${fertilizerEditorSort.direction}ending` : "none",
  };
}

function addFertilizerNameColumnResizer(table) {
  const header = table.querySelector("thead th:nth-child(2)");
  if (!header) {
    return;
  }
  const handle = document.createElement("span");
  handle.className = "column-resize-handle";
  handle.setAttribute("role", "separator");
  handle.setAttribute("aria-orientation", "vertical");
  handle.setAttribute("aria-label", t("editor.resizeNameColumn"));
  handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const startX = event.clientX;
    const startWidth = header.getBoundingClientRect().width;
    const onPointerMove = (moveEvent) => {
      fertilizerEditorNameWidthPx = Math.min(640, Math.max(180, startWidth + moveEvent.clientX - startX));
      table.style.setProperty("--fert-editor-name-width", `${fertilizerEditorNameWidthPx}px`);
    };
    const onPointerUp = () => {
      document.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("pointerup", onPointerUp);
    };
    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", onPointerUp);
  });
  header.appendChild(handle);
}

function renderFertilizerEditor() {
  if (!fertilizerEditorTableWrap) {
    return;
  }
  fertilizerEditorTableWrap.innerHTML = "";

  fertilizerEditorCompKeys = buildFertilizerCompKeys(fertilizerEditorRows);
  const filterValue = fertilizerEditorFilter.trim().toLowerCase();
  const filteredRows = fertilizerEditorRows
    .map((row, index) => ({ row, index }))
    .filter(({ row }) => {
      if (!filterValue) {
        return true;
      }
      return row.name.toLowerCase().includes(filterValue);
    })
    .sort(compareFertilizerEditorRows);
  const indexDigitCount = String(Math.max(1, filteredRows.length)).length;
  const colgroupClasses = [
    "col-index",
    "col-name",
    "col-liquid",
    "col-weight",
    ...fertilizerEditorCompKeys.map(() => "col-nutrient"),
  ];
  const headerCells = [
    { label: "#" },
    fertilizerEditorHeader("Düngername", "name", "editor.fertilizerName"),
    fertilizerEditorHeader("Flüssig", "liquid", "common.liquid"),
    fertilizerEditorHeader("m [g]", "weight_factor"),
    ...fertilizerEditorCompKeys.map((key) => fertilizerEditorHeader(key, `comp:${key}`)),
  ];
  const table = createTable({
    id: "fertilizerEditorTable",
    className: "grid grid--form grid--fertilizer grid--fertilizer-editor",
    colgroupClasses,
    headerCells,
  });
  fertilizerEditorTableWrap.appendChild(table.table);
  fertilizerEditorTable = table.table;
  fertilizerEditorTable.style.setProperty("--fert-editor-name-width", `${fertilizerEditorNameWidthPx}px`);
  addFertilizerNameColumnResizer(fertilizerEditorTable);
  const massHeaderButton = fertilizerEditorTable.querySelector("thead th:nth-child(4) .table-sort-button");
  const massSymbol = document.createElement("var");
  massSymbol.className = "quantity-symbol";
  massSymbol.textContent = "m";
  const massUnit = document.createElement("span");
  massUnit.className = "quantity-unit";
  massUnit.textContent = " [g]";
  massHeaderButton.replaceChildren(massSymbol, massUnit);
  fertilizerEditorTable.style.setProperty(
    "--fert-editor-index-width",
    `calc(${indexDigitCount}ch + (var(--space-2) * 2))`
  );

  if (filteredRows.length) {
    const stillVisible = filteredRows.some(({ index }) => index === fertilizerEditorSelectedIndex);
    if (!stillVisible) {
      fertilizerEditorSelectedIndex = filteredRows[0].index;
    }
  }

  filteredRows.forEach(({ row, index }, visibleIndex) => {
    const tr = document.createElement("tr");
    tr.dataset.editorIndex = index;
    tr.classList.toggle("is-selected", index === fertilizerEditorSelectedIndex);
    tr.addEventListener("click", () => setSelectedEditorRow(index));

    const indexCell = document.createElement("td");
    indexCell.textContent = String(visibleIndex + 1);
    tr.appendChild(indexCell);

    let colIndex = 0;
    const nameCell = document.createElement("td");
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.value = row.name;
    nameInput.dataset.rowIndex = index;
    nameInput.dataset.field = "name";
    nameInput.dataset.colIndex = colIndex;
    nameInput.addEventListener("input", (event) => {
      row.name = event.target.value;
    });
    nameInput.addEventListener("keydown", handleEditorEnterKey);
    nameCell.appendChild(nameInput);
    tr.appendChild(nameCell);
    colIndex += 1;

    const liquidCell = document.createElement("td");
    const liquidInput = document.createElement("input");
    liquidInput.type = "checkbox";
    liquidInput.checked = Boolean(row.liquid);
    liquidInput.dataset.rowIndex = index;
    liquidInput.dataset.field = "liquid";
    liquidInput.dataset.colIndex = colIndex;
    liquidInput.addEventListener("change", (event) => {
      row.liquid = event.target.checked;
    });
    liquidInput.addEventListener("keydown", handleEditorEnterKey);
    liquidCell.appendChild(liquidInput);
    tr.appendChild(liquidCell);
    colIndex += 1;

    const weightCell = document.createElement("td");
    const weightInput = document.createElement("input");
    weightInput.type = "text";
    weightInput.inputMode = "decimal";
    weightInput.value = Number.isFinite(row.weight_factor)
      ? formatNumber(row.weight_factor, nutrientFormatter)
      : "";
    weightInput.dataset.rowIndex = index;
    weightInput.dataset.field = "weight_factor";
    weightInput.dataset.colIndex = colIndex;
    weightInput.addEventListener("input", (event) => {
      row.weight_factor = parseDecimalInput(event.target.value);
    });
    weightInput.addEventListener("change", () => {
      normalizeDecimalInputElement(weightInput, row.weight_factor, "");
    });
    weightInput.addEventListener("keydown", handleEditorEnterKey);
    weightCell.appendChild(weightInput);
    tr.appendChild(weightCell);
    colIndex += 1;

    fertilizerEditorCompKeys.forEach((key) => {
      const cell = document.createElement("td");
      const input = document.createElement("input");
      input.type = "text";
      input.inputMode = "decimal";
      const value = row.comp?.[key];
      input.value = Number.isFinite(value) ? formatNumber(value * 100, nutrientFormatter) : "";
      input.dataset.rowIndex = index;
      input.dataset.field = "comp";
      input.dataset.compKey = key;
      input.dataset.colIndex = colIndex;
      input.addEventListener("input", (event) => {
        const parsed = parseDecimalInput(event.target.value);
        if (!row.comp) {
          row.comp = {};
        }
        if (parsed === null) {
          delete row.comp[key];
        } else {
          row.comp[key] = parsed / 100;
        }
      });
      input.addEventListener("change", () => {
        const percentValue = Number.isFinite(row.comp?.[key]) ? row.comp[key] * 100 : null;
        normalizeDecimalInputElement(input, percentValue, "");
      });
      input.addEventListener("keydown", handleEditorEnterKey);
      cell.appendChild(input);
      tr.appendChild(cell);
      colIndex += 1;
    });

    table.tbody.appendChild(tr);
  });
}

async function putFertilizers(payload) {
  const response = await fetch(`${apiBase()}/fertilizers`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || t("errors.saveFailed"));
  }
}

async function saveFertilizerEditor() {
  const payload = [];
  const seen = new Set();
  for (let index = 0; index < fertilizerEditorRows.length; index += 1) {
    const row = fertilizerEditorRows[index];
    const name = row.name.trim();
    if (!name) {
      reportError(null, t("editor.nameRequired"));
      focusEditorInput(index, "name");
      return;
    }
    if (seen.has(name)) {
      reportError(null, t("editor.uniqueNames"));
      focusEditorInput(index, "name");
      return;
    }
    seen.add(name);

    const weight = Number.isFinite(row.weight_factor) ? row.weight_factor : 1.0;
    const comp = {};
    Object.entries(row.comp || {}).forEach(([key, value]) => {
      if (Number.isFinite(value) && value > 0) {
        comp[key] = value;
      }
    });
    payload.push({
      name,
      liquid: Boolean(row.liquid),
      weight_factor: weight,
      comp,
    });
  }
  try {
    await putFertilizers(payload);
    const previousMode = activeMode;
    await init();
    if (previousMode === "fertilizers") {
      setMode("fertilizers");
    }
  } catch (error) {
    reportError(error, t("errors.saveFailed"));
  }
}

async function reloadFertilizerEditor() {
  try {
    fertilizerOptions = await fetchFertilizers();
    setFertilizerEditorData(fertilizerOptions);
    renderSelectionTable();
    renderCalculatorTable();
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  } catch (error) {
    reportError(error, t("errors.loadFertilizers"));
  }
}

function addFertilizerEditorRow() {
  fertilizerEditorRows.push({ name: "", liquid: false, weight_factor: null, comp: {} });
  fertilizerEditorSelectedIndex = fertilizerEditorRows.length - 1;
  renderFertilizerEditor();
  focusEditorInput(fertilizerEditorSelectedIndex, "name");
}

function deleteFertilizerEditorRow() {
  if (!fertilizerEditorRows.length) {
    return;
  }
  fertilizerEditorRows.splice(fertilizerEditorSelectedIndex, 1);
  if (fertilizerEditorSelectedIndex >= fertilizerEditorRows.length) {
    fertilizerEditorSelectedIndex = Math.max(0, fertilizerEditorRows.length - 1);
  }
  renderFertilizerEditor();
}

function updateSolverAllowedCount() {
  if (!solverAllowedCount) {
    return;
  }
  const visibleCount = getVisibleSolverAllowedOptions().length;
  const selectedCount = solverAllowedFertilizers.length;
  const suffix = solverAllowedFilter.trim() ? t("status.visibleSuffix", { count: visibleCount }) : "";
  solverAllowedCount.textContent = t("status.selectedCount", { count: selectedCount, suffix });
}

function solverAllowedMatchesFilter(fert) {
  if (solverAllowedHideInactive && !solverAllowedFertilizers.includes(fert.name)) {
    return false;
  }
  const query = solverAllowedFilter.trim().toLowerCase();
  if (!query) {
    return true;
  }
  return [fert.name, fert.liquid ? t("common.liquid") : t("common.solid"), String(fert.weight_factor ?? "")]
    .some((value) => String(value || "").toLowerCase().includes(query));
}

function getVisibleSolverAllowedOptions() {
  return fertilizerOptions.filter(solverAllowedMatchesFilter);
}

function setSolverAllowedRowState(row, checked) {
  row.classList.toggle("is-selected", checked);
  const checkbox = qs('input[type="checkbox"]', row);
  if (checkbox) {
    checkbox.checked = checked;
  }
  const pressed = checked ? "true" : "false";
  row.setAttribute("aria-selected", pressed);
}

function renderSolverAllowedOptions() {
  if (!solverAllowedFertilizersSelect) {
    return;
  }
  solverAllowedFertilizersSelect.innerHTML = "";
  const visibleOptions = getVisibleSolverAllowedOptions();

  const table = document.createElement("table");
  table.className = "grid grid--form solver-picker-table";

  const colgroup = document.createElement("colgroup");
  const checkCol = document.createElement("col");
  checkCol.className = "col-check";
  const nameCol = document.createElement("col");
  colgroup.append(checkCol, nameCol);

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  const checkHead = document.createElement("th");
  checkHead.textContent = "";
  const nameHead = document.createElement("th");
  nameHead.textContent = t("common.fertilizer");
  headRow.append(checkHead, nameHead);
  thead.appendChild(headRow);

  const tbody = document.createElement("tbody");
  table.append(colgroup, thead, tbody);

  if (!visibleOptions.length) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.colSpan = 2;
    emptyCell.textContent = t("solver.noFertilizersFound");
    emptyRow.appendChild(emptyCell);
    tbody.appendChild(emptyRow);
    solverAllowedFertilizersSelect.appendChild(table);
    updateSolverAllowedCount();
    return;
  }

  visibleOptions.forEach((fert) => {
    const name = fert.name;
    const row = document.createElement("tr");
    row.className = "solver-picker-row";
    row.setAttribute("role", "option");
    row.tabIndex = 0;

    const checkCell = document.createElement("td");
    checkCell.className = "solver-picker-check";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = name;
    checkbox.setAttribute("aria-label", name);
    checkbox.checked = solverAllowedFertilizers.includes(name);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        updateSolverAllowedFertilizers([name], "merge", { rerenderPicker: false });
      } else {
        updateSolverAllowedFertilizers(
          solverAllowedFertilizers.filter((allowedName) => allowedName !== name),
          "replace",
          { rerenderPicker: false }
        );
      }
      setSolverAllowedRowState(row, checkbox.checked);
    });
    row.addEventListener("click", (event) => {
      if (event.target === checkbox) {
        return;
      }
      checkbox.checked = !checkbox.checked;
      checkbox.dispatchEvent(new Event("change", { bubbles: true }));
    });
    row.addEventListener("keydown", (event) => {
      if (event.key !== " " && event.key !== "Enter") {
        return;
      }
      event.preventDefault();
      checkbox.checked = !checkbox.checked;
      checkbox.dispatchEvent(new Event("change", { bubbles: true }));
    });

    const nameCell = document.createElement("td");
    nameCell.textContent = name;
    checkCell.appendChild(checkbox);
    row.append(checkCell, nameCell);
    setSolverAllowedRowState(row, checkbox.checked);
    tbody.appendChild(row);
  });
  solverAllowedFertilizersSelect.appendChild(table);
  updateSolverAllowedCount();
}

function activeSolverOverrideCount() {
  return Object.values(solverFixedGrams).filter((value) => Number(value) > 0).length;
}

function syncSolverOverridePanel({ forceOpen = false } = {}) {
  const activeCount = activeSolverOverrideCount();
  if (solverOverrideSummary) {
    solverOverrideSummary.textContent = t("status.activeCount", { count: activeCount });
  }
  if (solverOverridesDetails && (forceOpen || activeCount > 0)) {
    solverOverridesDetails.open = true;
  }
}

function renderSolverFixedTable() {
  solverFixedTable.innerHTML = "";
  solverAllowedFertilizers.forEach((name) => {
    const row = document.createElement("tr");

    const nameCell = document.createElement("td");
    nameCell.textContent = name;

    const valueCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.min = "0";
    input.step = "0.01";
    input.value = solverFixedGrams[name] || 0;
    input.addEventListener("input", (event) => {
      solverFixedGrams[name] = decimalInputValue(event.target.value);
      syncSolverOverridePanel({ forceOpen: solverFixedGrams[name] > 0 });
    });
    input.addEventListener("change", () => {
      normalizeDecimalInputElement(input, solverFixedGrams[name]);
    });
    valueCell.appendChild(input);

    row.append(nameCell, valueCell);
    solverFixedTable.appendChild(row);
  });
  syncSolverOverridePanel();
}

function solverResultDisplayKeys(data) {
  const nitrogenKeys = ["N_total", "N_NO3", "N_NH4", "N_UREA"];
  const orderedKeys = [
    ...nitrogenKeys,
    ...summaryColumnOrder.map((column) => column.element).filter((key) => !nitrogenKeys.includes(key)),
  ];
  const seen = new Set();
  const addKey = (key) => {
    if (key && !seen.has(key)) {
      seen.add(key);
      orderedKeys.push(key);
    }
  };

  Object.keys(data?.targets_mg_per_l || {}).forEach(addKey);
  Object.keys(data?.achieved_elements_mg_per_l || {}).forEach(addKey);
  (data?.objective_elements || []).forEach(addKey);

  return orderedKeys.filter((key, index) => orderedKeys.indexOf(key) === index);
}

function renderSolverResults(data) {
  lastSolveResult = data || null;
  updateSolverResultActions();
  if (solverTargetsResultsTableEl) {
    solverTargetsResultsTableEl.classList.toggle("is-hidden", !data);
  }
  if (solverTargetsResultsEmpty) {
    solverTargetsResultsEmpty.classList.toggle("is-hidden", !!data);
  }
  solverFertilizersTable.innerHTML = "";
  solverTargetsResultsTable.innerHTML = "";

  const fertilizers = Array.isArray(data?.fertilizers) ? data.fertilizers : [];
  if (!fertilizers.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 2;
    cell.textContent = t("solver.noFertilizersCalculated");
    row.appendChild(cell);
    solverFertilizersTable.appendChild(row);
  } else {
    fertilizers.forEach((fert) => {
      const row = document.createElement("tr");
      const nameCell = document.createElement("td");
      nameCell.textContent = fert.name;
      const gramsCell = document.createElement("td");
      gramsCell.textContent = formatFertilizerGrams(Number(fert.grams));
      row.append(nameCell, gramsCell);
      solverFertilizersTable.appendChild(row);
    });
  }

  if (!data) {
    return;
  }

  const targets = data?.targets_mg_per_l || {};
  const achieved = data?.achieved_elements_mg_per_l || {};
  const errors = data?.errors_mg_per_l || {};
  const errorsPercent = data?.errors_percent || {};
  const nitrogenKeys = ["N_total", "N_NO3", "N_NH4", "N_UREA"];
  const labelMap = {
    N_total: "N-Σ",
    N_NO3: "NO3",
    N_NH4: "NH4",
    N_UREA: "UREA",
  };
  const objectiveKeys = new Set(data?.objective_elements || []);
  const displayKeys = solverResultDisplayKeys(data);

  displayKeys.forEach((key) => {
    const row = document.createElement("tr");
    const keyCell = document.createElement("td");
    keyCell.textContent = labelMap[key] || key;
    if (key !== "N_total" && nitrogenKeys.includes(key)) {
      keyCell.classList.add("solver-n-extra");
    }

    const hasTarget = Number(targets[key]) > 0 || objectiveKeys.has(key);
    if (!hasTarget) {
      row.classList.add("solver-result-inactive");
    }

    const targetValue = Number(targets[key] ?? 0);
    const achievedValue = Number(achieved[key] ?? 0);
    const errorValue = Number.isFinite(errors[key])
      ? Number(errors[key])
      : achievedValue - targetValue;
    const percentValue = Number.isFinite(errorsPercent[key])
      ? Number(errorsPercent[key])
      : targetValue
        ? (achievedValue - targetValue) / targetValue * 100
        : NaN;

    const targetCell = document.createElement("td");
    targetCell.textContent = hasTarget ? formatNumber(targetValue, nutrientFormatter) : "-";

    const achievedCell = document.createElement("td");
    achievedCell.textContent = formatNumber(achievedValue, nutrientFormatter);

    const deltaCell = document.createElement("td");
    deltaCell.textContent = formatNumber(errorValue, nutrientFormatter);

    const percentCell = document.createElement("td");
    percentCell.textContent = Number.isFinite(percentValue) ? `${percentValue.toFixed(1)}%` : "-";

    if (key !== "N_total" && nitrogenKeys.includes(key)) {
      targetCell.classList.add("solver-n-extra");
      achievedCell.classList.add("solver-n-extra");
      deltaCell.classList.add("solver-n-extra");
      percentCell.classList.add("solver-n-extra");
      row.classList.add("solver-n-row");
    }

    row.append(keyCell, targetCell, achievedCell, deltaCell, percentCell);
    solverTargetsResultsTable.appendChild(row);
  });
}

function setCopySolverStatus(message) {
  if (!copySolverResultsStatus) {
    return;
  }
  copySolverResultsStatus.textContent = message;
  if (copySolverStatusTimer) {
    window.clearTimeout(copySolverStatusTimer);
  }
  copySolverStatusTimer = window.setTimeout(() => {
    copySolverResultsStatus.textContent = "";
    copySolverStatusTimer = null;
  }, 2000);
}

function setSolverApplyStatus(message) {
  if (!solverApplyStatus) {
    return;
  }
  solverApplyStatus.textContent = message;
  if (solverApplyStatusTimer) {
    window.clearTimeout(solverApplyStatusTimer);
  }
  solverApplyStatusTimer = window.setTimeout(() => {
    solverApplyStatus.textContent = "";
    solverApplyStatusTimer = null;
  }, 2400);
}

function solverAutoApplyEnabled() {
  return !solverAutoApplyInput || solverAutoApplyInput.checked;
}

function restoreSolverAutoApplyPreference() {
  if (!solverAutoApplyInput) {
    return;
  }
  const stored = lsGet(SOLVER_AUTO_APPLY_KEY, true);
  solverAutoApplyInput.checked = stored !== false;
}

function persistSolverAutoApplyPreference() {
  if (!solverAutoApplyInput) {
    return;
  }
  lsSet(SOLVER_AUTO_APPLY_KEY, solverAutoApplyInput.checked);
}

function applySolverResultToCalculator({ switchToCalculator = false } = {}) {
  if (!lastSolveResult) {
    reportError(null, t("solver.noResult"));
    return false;
  }
  const fertilizers = (lastSolveResult.fertilizers || []).map((fert) => ({
    name: fert.name,
    grams: Number(fert.grams || 0),
  }));
  const recipe = {
    liters: currentLiters,
    fertilizers,
  };
  applyRecipe(recipe);
  scheduleRecalculate();
  setSolverApplyStatus(t("status.appliedCalculator"));

  if (switchToCalculator) {
    const calculatorInput = Array.from(modeToggleInputs).find((input) => input.value === "calculator");
    if (calculatorInput) {
      calculatorInput.checked = true;
    }
    showShellView("fertilizers");
  }
  return true;
}

function formatClipboardIonLabel(key) {
  if (key === "N_total") {
    return "N";
  }
  return key;
}

function buildClipboardRows(headers, rows, numericColumns = []) {
  const allRows = headers ? [headers, ...rows] : rows;
  const widths = allRows.reduce((currentWidths, row) => {
    row.forEach((cell, index) => {
      currentWidths[index] = Math.max(currentWidths[index] || 0, String(cell).length);
    });
    return currentWidths;
  }, []);
  const numericColumnSet = new Set(numericColumns);

  return allRows.map((row) =>
    row
      .map((cell, index) => {
        const value = String(cell);
        return numericColumnSet.has(index)
          ? value.padStart(widths[index])
          : value.padEnd(widths[index]);
      })
      .join("  ")
      .trimEnd()
  );
}

function buildSolverClipboardText() {
  const fertilizers = Array.isArray(lastSolveResult?.fertilizers) ? lastSolveResult.fertilizers : [];
  const lines = [t("solver.clipboardTitle")];
  lines.push(
    ...buildClipboardRows(null, [
      [t("solver.clipboardBatchLiters"), formatNumber(currentLiters)],
      [t("solver.clipboardOsmosis"), formatNumber(decimalInputValue(osmosisPercentInput.value))],
    ], [1])
  );
  lines.push("");
  lines.push(
    ...buildClipboardRows(
      [t("common.fertilizer"), t("common.grams")],
      fertilizers.map((fert) => [
        fert.name || "",
        formatFertilizerGrams(Number(fert.grams)),
      ]),
      [1]
    )
  );

  const calculateData = {
    liters: currentLiters,
    fertilizers,
    water_mg_l: buildWaterPayloadForApi(waterValues),
    osmosis_percent: decimalInputValue(osmosisPercentInput.value),
  };

  return calculate(calculateData).then((data) => {
    const npkMetrics = data?.npk_metrics || {};
    const ecValues = data?.ec?.ec_mS_per_cm || {};
    const ionValues = data?.elements_mg_per_l || {};

    lines.push("");
    lines.push(t("solver.clipboardNpk"));
    lines.push(
      ...buildClipboardRows(null, [
        [t("live.npkTotal"), npkMetrics.npk_all_pct || "-"],
        ["NPK P-Norm", npkMetrics.npk_p_norm || "-"],
        [t("live.npkRatio"), npkMetrics.npk_npk_pct || "-"],
      ], [1])
    );

    lines.push("");
    lines.push("EC (mS/cm)");
    lines.push(
      ...buildClipboardRows(null, [
        ["EC 25°C", formatNumber(Number(ecValues["25.0"]))],
        ["EC 18°C", formatNumber(Number(ecValues["18.0"]))],
      ], [1])
    );

    lines.push("");
    lines.push(t("solver.clipboardTargets"));
    const targets = lastSolveResult?.targets_mg_per_l || {};
    const achieved = lastSolveResult?.achieved_elements_mg_per_l || {};
    const errors = lastSolveResult?.errors_mg_per_l || {};
    const solverRows = solverResultDisplayKeys(lastSolveResult).map((key) => {
      const targetValue = Number(targets[key] ?? 0);
      const achievedValue = Number(achieved[key] ?? 0);
      const errorValue = Number.isFinite(errors[key])
        ? Number(errors[key])
        : achievedValue - targetValue;
      return [
        formatClipboardIonLabel(key),
        targetValue > 0 ? formatNumber(targetValue, nutrientFormatter) : "-",
        formatNumber(achievedValue, nutrientFormatter),
        formatNumber(errorValue, nutrientFormatter),
      ];
    });
    lines.push(
      ...buildClipboardRows([t("common.element"), t("common.target"), t("common.achieved"), t("common.delta")], solverRows, [1, 2, 3])
    );

    lines.push("");
    lines.push(t("solver.clipboardIons"));
    const ionRows = summaryColumnOrder.map((column) => {
      const key = column.element;
      const value = Number(ionValues[key]);
      return [formatClipboardIonLabel(key), formatNumber(value, nutrientFormatter)];
    });
    lines.push(...buildClipboardRows(null, ionRows, [1]));

    return lines.join("\n");
  });
}

function copyTextWithFallback(text) {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }

  return new Promise((resolve, reject) => {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.setAttribute("readonly", "");
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      const successful = document.execCommand("copy");
      document.body.removeChild(textArea);
      if (!successful) {
        reject(new Error(t("errors.copyFailed")));
        return;
      }
      resolve();
    } catch (error) {
      document.body.removeChild(textArea);
      reject(error);
    }
  });
}

async function copySolverResultsToClipboard() {
  if (!lastSolveResult || !Array.isArray(lastSolveResult.fertilizers) || !lastSolveResult.fertilizers.length) {
    reportError(null, t("solver.noResult"));
    return;
  }

  try {
    const text = await buildSolverClipboardText();
    await copyTextWithFallback(text);
    setCopySolverStatus(t("status.copied"));
  } catch (error) {
    reportError(error, t("errors.copyFailed"));
    setCopySolverStatus(t("status.copyFailed"));
  }
}

function renderSelectionTable() {
  renderTableRows(fertilizerSelectTable, selectedFertilizers.length, (i) => {
    const row = document.createElement("tr");

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const selectCell = document.createElement("td");
    const select = createSelect(fertilizerOptions, (value) => {
      const match = fertilizerOptions.find((opt) => opt.name === value);
      selectedFertilizers[i] = {
        name: value,
        liquid: Boolean(match?.liquid),
        weight: match ? match.weight_factor : "",
      };
      renderSelectionTable();
      renderCalculatorTable();
      scheduleRecalculate();
    });
    select.value = selectedFertilizers[i].name;
    selectCell.appendChild(select);

    const liquidCell = document.createElement("td");
    liquidCell.textContent = selectedFertilizers[i].name
      ? selectedFertilizers[i].liquid
        ? t("common.liquid")
        : t("common.solid")
      : "-";

    const weightCell = document.createElement("td");
    weightCell.textContent = selectedFertilizers[i].weight || "-";

    row.append(indexCell, selectCell, liquidCell, weightCell);
    return row;
  });
}

function renderCalculatorTable() {
  renderTableRows(calculatorTable, selectedFertilizers.length, (i) => {
    const row = document.createElement("tr");
    if (calculatorBaseAmounts[i] === undefined) {
      const currentAmount = Math.max(0, Number(fertilizerAmounts[i]) || 0);
      calculatorBaseAmounts[i] =
        calculatorScaleFactor > 0 ? roundScaledValue(currentAmount / calculatorScaleFactor) : 0;
    }

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const nameCell = document.createElement("td");
    nameCell.textContent = selectedFertilizers[i].name || "-";
    nameCell.colSpan = 2;

    const amountCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.min = "0";
    input.step = "any";
    input.value = formatFertilizerGramsInput(fertilizerAmounts[i]);
    input.addEventListener("input", (event) => {
      const rawValue = Math.max(0, decimalInputValue(event.target.value));
      fertilizerAmounts[i] = rawValue;
      calculatorBaseAmounts[i] =
        calculatorScaleFactor > 0 ? roundScaledValue(rawValue / calculatorScaleFactor) : 0;
      scheduleRecalculate();
    });
    input.addEventListener("change", () => {
      input.value = formatFertilizerGramsInput(fertilizerAmounts[i]);
    });
    amountCell.appendChild(input);

    row.append(indexCell, nameCell, amountCell);
    return row;
  });
}

function renderWaterTable() {
  waterTableBody.innerHTML = "";
  waterFieldDefinitions.forEach((field) => {
    const row = document.createElement("tr");

    const labelCell = document.createElement("td");
    labelCell.textContent = field.labelKey ? t(field.labelKey) : field.label;

    const valueCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.min = "0";
    input.step = waterUnit === "mol_l" && field.key !== "KH" ? "0.001" : "0.01";
    const rawValue = waterValues[field.key] || 0;
    const displayValue = waterUnit === "mol_l" ? mgToMol(field.key, rawValue) : rawValue;
    input.value = formatWaterDisplayValue(displayValue);
    input.dataset.waterKey = field.key;
    if (waterHelperKeys.has(field.key)) {
      input.classList.add("is-helper");
    }
    input.addEventListener("input", (event) => {
      const parsed = decimalInputValue(event.target.value);
      waterValues[field.key] = waterUnit === "mol_l" ? molToMg(field.key, parsed) : parsed;
      const updatedKeys = applyWaterHelpers(waterValues, getMolarMass);
      updatedKeys
        .filter((key) => key !== field.key)
        .forEach((key) => updateWaterInputValue(key));
      scheduleRecalculate();
    });
    input.addEventListener("change", () => {
      updateWaterInputValue(field.key);
    });
    input.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") {
        return;
      }
      event.preventDefault();
      const parsed = decimalInputValue(event.target.value);
      waterValues[field.key] = waterUnit === "mol_l" ? molToMg(field.key, parsed) : parsed;
      const updatedKeys = applyWaterHelpers(waterValues, getMolarMass);
      updatedKeys.forEach((key) => updateWaterInputValue(key));
      scheduleRecalculate();
    });
    valueCell.appendChild(input);

    const unitCell = document.createElement("td");
    unitCell.textContent = unitLabelForKey(field.key);

    row.append(labelCell, valueCell, unitCell);
    waterTableBody.appendChild(row);
  });
}

function updateWaterInputValue(key) {
  const input = qs(`input[data-water-key="${key}"]`, waterTableBody);
  if (!input) {
    return;
  }
  const rawValue = waterValues[key] || 0;
  const displayValue = waterUnit === "mol_l" ? mgToMol(key, rawValue) : rawValue;
  input.value = formatWaterDisplayValue(displayValue);
}

function formatWaterDisplayValue(value) {
  if (!Number.isFinite(value)) {
    return "0";
  }

  const absValue = Math.abs(value);
  if (absValue >= 0.1 || absValue === 0) {
    return value.toFixed(1);
  }

  let decimals = 2;
  if (absValue < 0.01) {
    decimals = 3;
  }
  if (absValue < 0.001) {
    decimals = 4;
  }
  if (absValue < 0.0001) {
    decimals = 5;
  }
  if (absValue < 0.00001) {
    decimals = 6;
  }

  const formatted = value.toFixed(decimals);
  return formatted.replace(/(\.\d*?[1-9])0+$/, "$1").replace(/\.0+$/, "");
}

function formatNumber(value, formatter = numberFormatter) {
  if (Number.isFinite(value)) {
    return formatter.format(value);
  }
  return "-";
}

function formatFertilizerGrams(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  if (value === 0 || Math.abs(value) >= 0.01) {
    return nutrientFormatter.format(value);
  }

  const formatted = fertilizerTraceFormatter.format(value);
  return formatted === "0" ? "<0.0001" : formatted;
}

function formatFertilizerGramsInput(value) {
  if (!Number.isFinite(Number(value))) {
    return "0";
  }
  const numericValue = Number(value);
  if (numericValue === 0 || Math.abs(numericValue) >= 0.01) {
    return String(numericValue);
  }

  const formatted = fertilizerTraceFormatter.format(numericValue);
  return formatted === "0" ? String(numericValue) : formatted;
}

function reportError(error, fallbackMessage = t("errors.unknown")) {
  const message = error?.message || fallbackMessage;
  setApiStatus(t("status.checking"), "error");
  alert(message);
}

function getMolarMass(key) {
  const value = molarMasses[key];
  return Number.isFinite(value) ? value : null;
}

function convertWaterUnitValue(key, value, convert) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  if (key === "KH") {
    return value;
  }
  const mm = getMolarMass(key);
  if (!mm) {
    return value;
  }
  return convert(value, mm);
}

function mgToMol(key, value) {
  return convertWaterUnitValue(key, value, (mgValue, mm) => mgValue / mm);
}

function molToMg(key, value) {
  return convertWaterUnitValue(key, value, (molValue, mm) => molValue * mm);
}

function unitLabelForKey(key) {
  if (key === "KH") {
    return "°dKH";
  }
  return waterUnit === "mol_l" ? "mmol/L" : "mg/L";
}

function scheduleRecalculate() {
  if (recalculateTimer) {
    clearTimeout(recalculateTimer);
  }
  recalculateTimer = setTimeout(async () => {
    try {
      await calculateAndRender();
    } catch (error) {
      reportError(error, t("errors.calculateFailed"));
    }
  }, 250);
}


function renderIonCompactList(container, entries) {
  container.innerHTML = "";
  const cations = [];
  const anions = [];

  entries.forEach(([key, value]) => {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
      return;
    }
    const item = { key, value: numericValue };
    if (numericValue >= 0) {
      cations.push(item);
    } else {
      anions.push(item);
    }
  });

  const maxCols = Math.max(cations.length, anions.length, 1);
  const table = document.createElement("table");
  table.classList.add("compact-ion-table");
  table.style.setProperty("--ion-cols", `${maxCols}`);

  const colgroup = document.createElement("colgroup");
  const labelCol = document.createElement("col");
  labelCol.classList.add("compact-ion-label-col");
  colgroup.appendChild(labelCol);
  for (let i = 0; i < maxCols; i += 1) {
    const col = document.createElement("col");
    col.classList.add("compact-ion-value-col");
    colgroup.appendChild(col);
  }
  table.appendChild(colgroup);

  const tbody = document.createElement("tbody");
  tbody.appendChild(buildIonRow(t("chem.cations"), cations, maxCols));
  tbody.appendChild(buildIonRow(t("chem.anions"), anions, maxCols));
  table.appendChild(tbody);
  container.appendChild(table);
}

function buildIonRow(label, items, maxCols) {
  const row = document.createElement("tr");

  const labelCell = document.createElement("th");
  labelCell.classList.add("compact-label");
  labelCell.textContent = label;
  row.appendChild(labelCell);

  for (let i = 0; i < maxCols; i += 1) {
    const cell = document.createElement("td");
    cell.classList.add("compact-ion-cell");
    const item = items[i];
    if (item) {
      cell.textContent = `${item.key} ${ionFormatter.format(Math.abs(item.value))}`;
    } else {
      cell.textContent = "";
    }
    row.appendChild(cell);
  }

  return row;
}

function renderIonBalanceCompact(container, entries) {
  container.innerHTML = "";
  const labelMap = {
    cations_meq_per_l: "Σ+",
    anions_meq_per_l: "Σ-",
    raw_cbe_percent_signed: "CBE-raw",
    din_38402_62_percent_signed: "DIN-raw",
  };
  const unitMap = {
    cations_meq_per_l: "meq/L",
    anions_meq_per_l: "meq/L",
    raw_cbe_percent_signed: "%",
    din_38402_62_percent_signed: "%",
  };
  const rows = [
    ["cations_meq_per_l", "anions_meq_per_l"],
    ["raw_cbe_percent_signed", "din_38402_62_percent_signed"],
  ];
  const values = new Map(entries.map(([key, value]) => [key, value]));
  if (!values.has("raw_cbe_percent_signed") && values.has("error_percent_signed")) {
    values.set("raw_cbe_percent_signed", values.get("error_percent_signed"));
  }
  if (!values.has("din_38402_62_percent_signed")) {
    const rawCbe = Number(values.get("raw_cbe_percent_signed"));
    if (Number.isFinite(rawCbe)) {
      values.set("din_38402_62_percent_signed", rawCbe * 2.0);
    }
  }

  const table = document.createElement("table");
  table.classList.add("compact-ion-table", "compact-balance-table");
  table.style.setProperty("--ion-cols", "2");

  const colgroup = document.createElement("colgroup");
  const labelCol = document.createElement("col");
  labelCol.classList.add("compact-ion-label-col");
  colgroup.appendChild(labelCol);
  for (let i = 0; i < 2; i += 1) {
    const col = document.createElement("col");
    col.classList.add("compact-ion-value-col");
    colgroup.appendChild(col);
  }
  table.appendChild(colgroup);

  const tbody = document.createElement("tbody");
  rows.forEach((rowKeys) => {
    const row = document.createElement("tr");
    const unit = unitMap[rowKeys[0]];
    const labelCell = document.createElement("th");
    labelCell.classList.add("compact-label");
    labelCell.textContent = unit.toUpperCase();
    row.appendChild(labelCell);

    rowKeys.forEach((key) => {
      const cell = document.createElement("td");
      cell.classList.add("compact-ion-cell");
      const value = Number(values.get(key));
      cell.textContent = Number.isFinite(value)
        ? `${labelMap[key]} ${ionFormatter.format(value)} ${unitMap[key]}`
        : "";
      row.appendChild(cell);
    });
    tbody.appendChild(row);
  });
  table.appendChild(tbody);

  container.appendChild(table);
}

function buildSummaryColumns(extraColumns = []) {
  const columns = [];
  summaryColumnOrder.forEach((column) => {
    columns.push({ type: "base", column });
    if (column.element === "N_total" && extraColumns.length) {
      extraColumns.forEach((extra) => {
        columns.push({ type: "extra", column: extra });
      });
    }
  });
  return columns;
}

function buildSummaryColgroup(summaryColumns) {
  const colgroup = document.createElement("colgroup");
  const labelCol = document.createElement("col");
  labelCol.classList.add("col-row-label");
  labelCol.style.width = summaryLabelWidth;
  colgroup.appendChild(labelCol);
  summaryColumns.forEach((columnGroup) => {
    const col = document.createElement("col");
    if (columnGroup.type === "extra") {
      const key = columnGroup.column.key;
      col.classList.add(`col-${normalizeColumnKey(key)}`, "ion-n-extra");
    } else {
      col.classList.add(`col-${normalizeColumnKey(columnGroup.column.oxide)}`);
    }
    colgroup.appendChild(col);
  });
  return colgroup;
}

function renderSummaryTable({
  table,
  headerLabels,
  rowLabel,
  rowLabelClass,
  valueMap,
  valueKey,
  formatter,
  extraColumns = [],
  extraFormatter,
}) {
  table.innerHTML = "";
  const summaryColumns = buildSummaryColumns(extraColumns);
  table.appendChild(buildSummaryColgroup(summaryColumns));

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const spacer = document.createElement("th");
  spacer.textContent = "";
  headerRow.appendChild(spacer);
  summaryColumns.forEach((columnGroup) => {
    const th = document.createElement("th");
    if (columnGroup.type === "extra") {
      const key = columnGroup.column.key;
      th.textContent = columnGroup.column.label;
      th.classList.add(`col-${normalizeColumnKey(key)}`, "ion-n-extra");
    } else {
      const column = columnGroup.column;
      const label = document.createElement("span");
      label.textContent = headerLabels(column);
      th.appendChild(label);
      th.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
      if (column.element === "N_total" && extraColumns.length) {
        th.classList.add("has-expander");
        const toggleButton = document.createElement("button");
        toggleButton.type = "button";
        toggleButton.classList.add("column-expander");
        toggleButton.dataset.ionNToggle = "true";
        toggleButton.setAttribute("aria-label", t("aria.toggleNDetails"));
        toggleButton.setAttribute("aria-expanded", ionNitrogenExpanded ? "true" : "false");
        toggleButton.textContent = ionNitrogenExpanded ? "‹" : "›";
        th.appendChild(toggleButton);
      }
    }
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const tr = document.createElement("tr");
  const labelCell = document.createElement("th");
  labelCell.textContent = rowLabel;
  labelCell.classList.add("row-label");
  if (rowLabelClass) {
    labelCell.classList.add(rowLabelClass);
  }
  labelCell.scope = "row";
  tr.appendChild(labelCell);

  summaryColumns.forEach((columnGroup) => {
    if (columnGroup.type === "extra") {
      const key = columnGroup.column.key;
      const rawValue = valueMap.get(key);
      const formatted = extraFormatter
        ? extraFormatter(key, Number(rawValue))
        : formatter({ element: key }, Number(rawValue));
      const extraCell = document.createElement("td");
      extraCell.textContent = formatted;
      extraCell.classList.add(`col-${normalizeColumnKey(key)}`, "ion-n-extra");
      tr.appendChild(extraCell);
      return;
    }
    const column = columnGroup.column;
    const rawValue = valueMap.get(valueKey(column));
    const td = document.createElement("td");
    const formatted = formatter(column, Number(rawValue));
    td.textContent = formatted;
    td.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
    tr.appendChild(td);
  });
  tbody.appendChild(tr);
  table.appendChild(tbody);
}

function renderWaterSummaryTable(table, waterElements) {
  const waterMap = new Map(Object.entries(waterElements || {}));
  if (waterSummaryBadge) {
    waterSummaryBadge.textContent = waterUnit === "mol_l" ? "mmol/L" : "mg/L";
  }
  renderSummaryTable({
    table,
    headerLabels: (column) => column.ionHeaderLabel,
    valueKey: (column) => column.element,
    rowLabel: t("water.rowWaterValues"),
    valueMap: waterMap,
    formatter: (column, value) =>
      waterUnit === "mol_l" ? formatTraceValue(value) : formatNutrientValue(column.element, value),
  });
}

function renderOxideSummaryTable(table, oxides) {
  const oxideMap = new Map(Object.entries(oxides || {}));
  if (oxideSummaryBadge) {
    oxideSummaryBadge.textContent = t("unit.mgLoxide");
  }
  renderSummaryTable({
    table,
    headerLabels: (column) => column.oxideHeaderLabel,
    valueKey: (column) => column.oxide,
    rowLabel: t("calculator.oxideForms"),
    valueMap: oxideMap,
    formatter: (column, value) => formatOxideValue(column.oxide, value),
  });
}

function renderIonSummaryTable(table, elements) {
  const elementMap = new Map(Object.entries(elements || {}));
  if (ionSummaryBadge) {
    ionSummaryBadge.textContent = "mg/L";
  }
  const nitrogenColumns = [
    { key: "N_NO3", label: "NO3" },
    { key: "N_NH4", label: "NH4" },
    { key: "N_UREA", label: "UREA" },
  ];
  renderSummaryTable({
    table,
    headerLabels: (column) => column.ionHeaderLabel,
    valueKey: (column) => column.element,
    rowLabel: t("water.rowDissolvedIons"),
    rowLabelClass: "row-label--ion",
    valueMap: elementMap,
    formatter: (column, value) => formatNutrientValue(column.element, value),
    extraColumns: nitrogenColumns,
    extraFormatter: (key, value) => formatNutrientValue(key, value),
  });
  table.classList.toggle("is-n-expanded", ionNitrogenExpanded);
  table.classList.toggle("is-n-collapsed", !ionNitrogenExpanded);
  const toggleButton = qs("[data-ion-n-toggle]", table);
  if (toggleButton) {
    toggleButton.addEventListener("click", () => {
      ionNitrogenExpanded = !ionNitrogenExpanded;
      lsSet(ION_NITROGEN_EXPANDED_KEY, ionNitrogenExpanded);
      table.classList.toggle("is-n-expanded", ionNitrogenExpanded);
      table.classList.toggle("is-n-collapsed", !ionNitrogenExpanded);
      toggleButton.textContent = ionNitrogenExpanded ? "‹" : "›";
      toggleButton.setAttribute("aria-expanded", ionNitrogenExpanded ? "true" : "false");
    });
  }
}

function setSummaryView(nextView) {
  const allowed = new Set(["water", "oxide", "ion"]);
  const view = allowed.has(nextView) ? nextView : "ion";
  summaryView = view;
  lsSet(SUMMARY_VIEW_KEY, view);

  if (summaryViewToggle) {
    qsa("button[data-summary-view]", summaryViewToggle).forEach((button) => {
      const isActive = button.dataset.summaryView === view;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
      button.tabIndex = isActive ? 0 : -1;
    });
  }

  summaryPanels.forEach((panel) => {
    const panelView = panel.dataset.summaryPanel;
    panel.hidden = panelView !== view;
  });

  if (summaryViewToggle) {
    const activePanel = qs(`.summary-panel[data-summary-panel="${view}"]`);
    const activeTitle = activePanel ? qs(".table-card-title", activePanel) : null;
    if (activeTitle && !activeTitle.contains(summaryViewToggle)) {
      activeTitle.prepend(summaryViewToggle);
    }
  }

  const summaryScroll = qs("#summaryScroll");
  if (summaryScroll) {
    summaryScroll.scrollLeft = 0;
  }
}

function normalizeColumnKey(key) {
  return key.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function formatTraceValue(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }

  const absValue = Math.abs(value);
  let maxDecimals = 2;
  if (absValue < 0.01) {
    maxDecimals = 4;
  } else if (absValue < 1) {
    maxDecimals = 3;
  }

  const formatter = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxDecimals,
    useGrouping: false,
  });
  return formatter.format(value);
}

function formatNutrientValue(key, value) {
  if (!Number.isFinite(value)) {
    return "-";
  }

  if (nutrientIntegerKeys.has(key)) {
    return nutrientIntegerFormatter.format(value);
  }

  if (nutrientTraceKeys.has(key)) {
    return formatTraceValue(value);
  }

  return nutrientFormatter.format(value);
}

function formatOxideValue(key, value) {
  if (!Number.isFinite(value)) {
    return "-";
  }

  if (oxideIntegerKeys.has(key)) {
    return nutrientIntegerFormatter.format(value);
  }

  if (oxideTraceKeys.has(key)) {
    return formatTraceValue(value);
  }

  return nutrientFormatter.format(value);
}

function buildWaterPayloadForApi(rawValues) {
  const values = { ...rawValues };
  applyWaterHelpers(values, getMolarMass);
  return values;
}

function waterElementsForDisplay(elements) {
  if (waterUnit !== "mol_l") {
    return elements;
  }
  const converted = {};
  const mm = (key) => getMolarMass(key) || null;
  Object.entries(elements).forEach(([key, value]) => {
    let molKey = key;
    if (key === "N_total") {
      molKey = "N";
    }
    const molarMass = mm(molKey);
    converted[key] = molarMass ? value / molarMass : value;
  });
  return converted;
}

function buildSelectedFertilizerEntries({ allowZeroGrams = false } = {}) {
  return selectedFertilizers
    .map((fert, index) => ({
      name: fert.name,
      grams: Number(fertilizerAmounts[index]) || 0,
    }))
    .filter((entry) => entry.name && (allowZeroGrams || entry.grams > 0));
}

function buildPayload() {
  const fertilizers = buildSelectedFertilizerEntries();

  const waterPayload = buildWaterPayloadForApi(waterValues);

  return {
    liters: currentLiters,
    fertilizers,
    water_mg_l: waterPayload,
    osmosis_percent: decimalInputValue(osmosisPercentInput.value),
  };
}

function buildSolvePayload() {
  const targets = {};
  Object.entries(solverTargetValues).forEach(([key, value]) => {
    if (Number(value) > 0) {
      targets[key] = Number(value);
    }
  });

  const fixedGrams = {};
  Object.entries(solverFixedGrams).forEach(([key, value]) => {
    if (Number(value) > 0) {
      fixedGrams[key] = Number(value);
    }
  });

  const waterPayload = buildWaterPayloadForApi(waterValues);
  return {
    liters: currentLiters,
    targets,
    water_profile: {
      mg_per_l: waterPayload,
      osmosis_percent: decimalInputValue(osmosisPercentInput.value),
    },
    fertilizers_allowed: solverAllowedFertilizers,
    fixed_grams: fixedGrams,
    urea_as_nh4: solverUreaToggle.checked,
    phosphate_species: solverPhosphateSelect.value,
    solver_config: buildSolverConfigPayload(),
  };
}

async function fetchJson(url, errorMessage) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(errorMessage);
  }
  return response.json();
}

async function postJson(url, payload, errorMessage) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || errorMessage);
  }
  return response.json();
}

function fetchFertilizers() {
  return fetchJson(`${apiBase()}/fertilizers`, t("errors.loadFertilizers"));
}

async function fetchFertilizerCompKeys() {
  const data = await fetchJson(
    `${apiBase()}/schema/fertilizer-comp-keys`,
    t("errors.loadFertilizerSchema")
  );
  if (Array.isArray(data)) {
    return data;
  }
  if (Array.isArray(data?.keys)) {
    return data.keys;
  }
  return [];
}

function fetchMolarMasses() {
  return fetchJson(`${apiBase()}/molar-masses`, t("errors.loadMolarMasses"));
}

function fetchWaterProfiles() {
  return fetchJson(`${apiBase()}/water-profiles`, t("errors.loadWaterProfiles"));
}

function fetchWaterProfileData(filename) {
  return fetchJson(
    `${apiBase()}/water-profiles/${encodeURIComponent(filename)}`,
    t("errors.loadWaterProfile")
  );
}

async function saveWaterProfile() {
  const name = waterProfileNameInput.value.trim();
  if (!name) {
    reportError(null, t("errors.profileNameRequired"));
    return;
  }
  const waterPayload = buildWaterPayloadForApi(waterValues);
  const payload = {
    name,
    source: "Horticalc UI",
    mg_per_l: waterPayload,
    osmosis_percent: decimalInputValue(osmosisPercentInput.value),
  };
  await postJson(`${apiBase()}/water-profiles`, payload, t("errors.saveFailed"));
}

function fetchDefaultRecipe() {
  return fetchJson(`${apiBase()}/recipes/default`, t("errors.loadDefaultRecipe"));
}

function fetchRecipes() {
  return fetchJson(`${apiBase()}/recipes`, t("errors.loadRecipes"));
}

async function fetchSolverConfigDefinitions() {
  const data = await fetchJson(
    `${apiBase()}/schema/solver-config`,
    t("errors.loadSolverConfig")
  );
  return normalizeSolverConfigDefinitions(data?.definitions || []);
}

function fetchRecipeData(filename) {
  return fetchJson(`${apiBase()}/recipes/${encodeURIComponent(filename)}`, t("errors.loadRecipe"));
}

async function saveRecipeData(payload) {
  await postJson(`${apiBase()}/recipes`, payload, t("errors.saveRecipeFailed"));
}

function fetchNutrientSolutions() {
  return fetchJson(`${apiBase()}/nutrient-solutions`, t("errors.loadNutrientSolutions"));
}

function fetchNutrientSolutionData(filename) {
  return fetchJson(
    `${apiBase()}/nutrient-solutions/${encodeURIComponent(filename)}`,
    t("errors.loadNutrientSolution")
  );
}

async function saveNutrientSolutionData(payload) {
  await postJson(`${apiBase()}/nutrient-solutions`, payload, t("errors.saveNutrientSolutionFailed"));
}

async function calculate(payloadOverride = null) {
  const payload = payloadOverride || buildPayload();
  return postJson(`${apiBase()}/calculate`, payload, t("errors.calculateFailed"));
}

async function calculateAndRender(payloadOverride = null) {
  const data = await calculate(payloadOverride);
  renderCalculation(data);
  return data;
}

async function solveRecipe() {
  const payload = buildSolvePayload();
  return postJson(`${apiBase()}/solve`, payload, t("errors.solveFailed"));
}

function renderEcPair(ecValues, el18, el25) {
  const ec18 = Number(ecValues["18.0"]);
  const ec25 = Number(ecValues["25.0"]);
  el18.textContent = Number.isFinite(ec18) ? formatNumber(ec18) : "-";
  el25.textContent = Number.isFinite(ec25) ? formatNumber(ec25) : "-";
}

function ratioValueText(value) {
  const text = String(value || "").trim();
  if (!text) {
    return "-";
  }
  const markerIndex = text.indexOf("=");
  return markerIndex >= 0 ? text.slice(markerIndex + 1) : text;
}

function formatRatioNumber(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  const rounded = Math.round(value * 10) / 10;
  return rounded.toFixed(1).replace(/\.0$/, "");
}

function ratioToOneText(value, leftLabel, rightLabel) {
  const parts = ratioValueText(value).split(":").map((part) => Number(part));
  if (parts.length !== 2 || !Number.isFinite(parts[0]) || !Number.isFinite(parts[1])) {
    return "-";
  }
  const [left, right] = parts;
  if (left <= 0 && right <= 0) {
    return `0 ${leftLabel} : 0 ${rightLabel}`;
  }
  if (right <= 0) {
    return `${formatRatioNumber(left)} ${leftLabel} : 0 ${rightLabel}`;
  }
  return `${formatRatioNumber(left / right)} ${leftLabel} : 1 ${rightLabel}`;
}

function renderIonRatios(metrics) {
  const ratios = metrics?.npk_ratios_ion || {};
  if (caMgRatioValue) {
    caMgRatioValue.textContent = ratioToOneText(ratios["Ca:Mg"], "Ca", "Mg");
  }
  if (!ionRatioList) {
    return;
  }

  ionRatioList.innerHTML = "";
  ["N:K", "Ca:K", "Na:Mg", "SO4:P", "P:K", "Fe:Mg"].forEach((key) => {
    const item = document.createElement("div");
    item.className = "ion-ratio-pill";

    const label = document.createElement("span");
    label.textContent = key;
    const value = document.createElement("strong");
    value.textContent = ratioValueText(ratios[key]);

    item.append(label, value);
    ionRatioList.appendChild(item);
  });
}

function renderCalculation(data) {
  lastCalculation = data;
  const oxides = data.oxides_mg_per_l || {};
  const elements = data.elements_mg_per_l || {};
  const npkMetrics = data.npk_metrics || {};
  const waterElements = data.water_elements_mg_per_l || {};
  const waterDisplay = waterElementsForDisplay(waterElements);
  renderWaterSummaryTable(waterSummaryTable, waterDisplay);
  renderOxideSummaryTable(oxideSummaryTable, oxides);
  renderIonSummaryTable(ionSummaryTable, elements);

  const ionMeqEntries = Object.entries(data.ions_meq_per_l || {});
  renderIonCompactList(ionMeqList, ionMeqEntries);

  const ionBalanceEntries = Object.entries(data.ion_balance || {});
  renderIonBalanceCompact(ionBalanceList, ionBalanceEntries);

  npkAllPctValue.textContent = npkMetrics.npk_all_pct || "-";
  npkPNormValue.textContent = npkMetrics.npk_p_norm || "-";
  npkNpkPctValue.textContent = npkMetrics.npk_npk_pct || "-";
  renderIonRatios(npkMetrics);

  const ec = data.ec || {};
  renderEcPair(ec.ec_mS_per_cm || {}, ec18Value, ec25Value);

  const waterEc = data.ec_water || {};
  renderEcPair(waterEc.ec_mS_per_cm || {}, ecWater18Value, ecWater25Value);
  updateLiveResultBar(data);
  setApiStatus(t("status.apiReady"), "ready");
}

function applyRecipe(recipe, { applyLiters = true } = {}) {
  if (applyLiters && recipe && recipe.liters !== undefined && recipe.liters !== null) {
    setCurrentLiters(recipe.liters, { scaleBatch: false, recalculate: false, invalidateSolver: false });
  }
  const fertilizers = Array.isArray(recipe.fertilizers) ? recipe.fertilizers : [];
  selectedFertilizers.length = 0;
  fertilizerAmounts.length = 0;
  calculatorBaseAmounts.length = 0;
  calculatorScaleFactor = 1.0;

  fertilizers.forEach((entry) => {
    const name = entry.name || "";
    const match = fertilizerOptions.find((opt) => opt.name === name);
    const grams = Math.max(0, Number(entry.grams) || 0);
    selectedFertilizers.push({
      name,
      liquid: Boolean(match?.liquid),
      weight: match ? match.weight_factor : "",
    });
    fertilizerAmounts.push(grams);
    calculatorBaseAmounts.push(roundScaledValue(grams));
  });

  if (!selectedFertilizers.length) {
    selectedFertilizers.push({ name: "", liquid: false, weight: "" });
    fertilizerAmounts.push(0);
    calculatorBaseAmounts.push(0);
  }

  updateCalculatorScaleDisplay();
  renderSelectionTable();
  renderCalculatorTable();
}

function applyNutrientSolution(solution) {
  const targets = solution?.targets_mg_per_l || solution?.targets || {};
  solverTargetScaleFactor = 1.0;
  solverTargetDefinitions.forEach((field) => {
    const value = Number(targets[field.key]) || 0;
    solverTargetBaseValues[field.key] = value;
    solverTargetValues[field.key] = value;
  });
  updateSolverTargetScaleDisplay();
  renderSolverTargetsTable();
}

function resetSolverTargets() {
  solverTargetScaleFactor = 1.0;
  solverTargetDefinitions.forEach((field) => {
    solverTargetValues[field.key] = 0;
    solverTargetBaseValues[field.key] = 0;
  });
  updateSolverTargetScaleDisplay();
  renderSolverTargetsTable();
  renderSolverResults(null);
}

function updateSolverResultActions() {
  const hasResult = !!(lastSolveResult && lastSolveResult.fertilizers && lastSolveResult.fertilizers.length);
  saveSolverAsRecipeButton.disabled = !hasResult;
  applySolverToCalculatorButton.disabled = !hasResult;
  if (copySolverResultsButton) {
    copySolverResultsButton.disabled = !hasResult;
  }
  if (applySolverToCalculatorInlineButton) {
    applySolverToCalculatorInlineButton.disabled = !hasResult;
  }
}

function collectSelectedFertilizerNames() {
  const names = selectedFertilizers.map((fert) => fert.name).filter(Boolean);
  return Array.from(new Set(names));
}

function pruneSolverFixedGrams() {
  Object.keys(solverFixedGrams).forEach((key) => {
    if (!solverAllowedFertilizers.includes(key)) {
      delete solverFixedGrams[key];
    }
  });
}

function updateSolverAllowedFertilizers(names, mode = "merge", { rerenderPicker = true } = {}) {
  const uniqueNames = Array.from(new Set(names.filter(Boolean)));
  if (mode === "replace") {
    solverAllowedFertilizers.length = 0;
    solverAllowedFertilizers.push(...uniqueNames);
  } else {
    uniqueNames.forEach((name) => {
      if (!solverAllowedFertilizers.includes(name)) {
        solverAllowedFertilizers.push(name);
      }
    });
  }
  pruneSolverFixedGrams();
  if (rerenderPicker) {
    renderSolverAllowedOptions();
  } else {
    updateSolverAllowedCount();
  }
  renderSolverFixedTable();
  persistSolverAllowedToStorage();
}

function normalizeSolverAllowedContext(context) {
  if (typeof context !== "string") {
    return "global";
  }
  const trimmed = context.trim();
  return trimmed || "global";
}

function solverAllowedStorageKey(context = solverAllowedContext) {
  const normalized = normalizeSolverAllowedContext(context);
  return `${LAST_FERTILIZERS_ALLOWED_CONTEXT_KEY_PREFIX}${normalized}`;
}

function persistSolverAllowedToStorage(context = solverAllowedContext) {
  lsSet(solverAllowedStorageKey(context), solverAllowedFertilizers);
}

function syncSolverAllowedWithSelection(mode = "merge") {
  const names = collectSelectedFertilizerNames();
  if (!names.length) {
    return false;
  }
  updateSolverAllowedFertilizers(names, mode);
  return true;
}

function applyWaterProfile(profile) {
  const mg = profile.normalized_mg_per_l || profile.mg_per_l || {};
  waterFieldDefinitions.forEach((field) => {
    waterValues[field.key] = Number(mg[field.key]) || 0;
  });
  applyWaterHelpers(waterValues, getMolarMass);

  waterProfileNameInput.value = profile.name || "";
  osmosisPercentInput.value = profile.osmosis_percent ?? 0;
  renderWaterTable();
  scheduleRecalculate();
}

function addFertilizerRow() {
  selectedFertilizers.push({ name: "", liquid: false, weight: "" });
  fertilizerAmounts.push(0);
  calculatorBaseAmounts.push(0);
  renderSelectionTable();
  renderCalculatorTable();
}

function removeFertilizerRow() {
  if (selectedFertilizers.length <= 1) {
    return;
  }

  selectedFertilizers.pop();
  fertilizerAmounts.pop();
  calculatorBaseAmounts.pop();
  renderSelectionTable();
  renderCalculatorTable();
}

function renderWaterProfileOptions() {
  waterProfileSelect.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = t("common.selectEmpty");
  waterProfileSelect.appendChild(empty);

  waterProfiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.filename;
    option.textContent = profile.name || profile.filename;
    waterProfileSelect.appendChild(option);
  });
}

function refreshLocalizedUi() {
  i18n.applyDomTranslations();
  updateLitersDisplay();
  refreshApiStatusLabel();
  updateLiveResultBar();
  setProfileMode(currentProfileMode);
  renderWaterProfileOptions();
  renderSelectionTable();
  renderCalculatorTable();
  renderWaterTable();
  renderFertilizerEditor();
  renderSolverAllowedOptions();
  renderSolverFixedTable();
  renderSolverTargetsTable();
  renderSolverResults(lastSolveResult);
  if (lastCalculation) {
    renderCalculation(lastCalculation);
  } else {
    renderWaterSummaryTable(waterSummaryTable, {});
    renderOxideSummaryTable(oxideSummaryTable, {});
    renderIonSummaryTable(ionSummaryTable, {});
  }
}

function buildRecipePayload(name, fertilizers, liters, ureaAsNh4, phosphateSpecies) {
  const payload = {
    name,
    liters,
    fertilizers,
    fertilizers_allowed: solverAllowedFertilizers,
    urea_as_nh4: ureaAsNh4,
    phosphate_species: phosphateSpecies,
  };
  const waterProfileSelection = waterProfileSelect.value;
  if (waterProfileSelection) {
    payload.water_profile = waterProfileSelection.replace(/\.yml$/, "");
  }
  const osmosisPercent = parseDecimalInput(osmosisPercentInput.value);
  if (Number.isFinite(osmosisPercent)) {
    payload.osmosis_percent = osmosisPercent;
  }
  return payload;
}

function buildRecipePayloadFromSelection(name) {
  const fertilizers = buildSelectedFertilizerEntries();
  return buildRecipePayload(name, fertilizers, currentLiters, false, "H2PO4");
}

function buildRecipePayloadFromSolver(name) {
  const fertilizers = Array.isArray(lastSolveResult?.fertilizers) ? lastSolveResult.fertilizers : [];
  return buildRecipePayload(
    name,
    fertilizers,
    currentLiters,
    solverUreaToggle.checked,
    solverPhosphateSelect.value
  );
}

function buildSolutionSnapshot() {
  const fertilizers = buildSelectedFertilizerEntries({ allowZeroGrams: true });
  return {
    water_profile_value: waterProfileSelect.value || "",
    osmosis_percent: decimalInputValue(osmosisPercentInput.value),
    water_unit: waterUnit,
    liters: currentLiters,
    water_values: { ...waterValues },
    fertilizers,
  };
}

function restoreSolverAllowedFromStorage(context = solverAllowedContext) {
  const contextKey = solverAllowedStorageKey(context);
  const storedContextAllowed = lsGet(contextKey, null);
  if (!Array.isArray(storedContextAllowed)) {
    return false;
  }
  const options = new Set(fertilizerOptions.map((fert) => fert.name));
  const filtered = storedContextAllowed.filter((name) => options.has(name));
  solverAllowedFertilizers.length = 0;
  solverAllowedFertilizers.push(...filtered);
  renderSolverAllowedOptions();
  renderSolverFixedTable();
  return true;
}

async function init() {
  let hasStoredAllowed = false;
  const preferences = await loadPreferences();
  setApiStatus(t("status.loadingData"), "loading");
  try {
    solverConfigDefinitions = await fetchSolverConfigDefinitions();
  } catch (error) {
    reportError(error, t("errors.loadSolverDefaults"));
    solverConfigDefinitions = [...FALLBACK_SOLVER_CONFIG_DEFINITIONS];
  }
  applySolverConfig(preferences.solver_config || {});
  setCurrentLiters(preferences.default_liters || DEFAULT_LITERS, {
    scaleBatch: false,
    recalculate: false,
    invalidateSolver: false,
  });
  restoreSolverAutoApplyPreference();
  try {
    fertilizerEditorPreferredKeys = await fetchFertilizerCompKeys();
  } catch (error) {
    reportError(error, t("errors.loadFertilizerSchema"));
    fertilizerEditorPreferredKeys = [];
  }
  try {
    fertilizerOptions = await fetchFertilizers();
  } catch (error) {
    reportError(error, t("errors.loadFertilizers"));
    fertilizerOptions = [];
  }
  setFertilizerEditorData(fertilizerOptions);
  solverAllowedContext = normalizeSolverAllowedContext();
  hasStoredAllowed = restoreSolverAllowedFromStorage();
  if (!hasStoredAllowed) {
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  }

  try {
    molarMasses = await fetchMolarMasses();
  } catch (error) {
    reportError(error, t("errors.loadMolarMasses"));
    molarMasses = {};
  }

  try {
    waterProfiles = await fetchWaterProfiles();
  } catch (error) {
    reportError(error, t("errors.loadWaterProfiles"));
    waterProfiles = [];
  }

  renderWaterProfileOptions();

  try {
    recipeProfiles = await fetchRecipes();
  } catch (error) {
    reportError(error, t("errors.loadRecipes"));
    recipeProfiles = [];
  }

  try {
    nutrientSolutions = await fetchNutrientSolutions();
  } catch (error) {
    reportError(error, t("errors.loadNutrientSolutions"));
    nutrientSolutions = [];
  }

  renderProfileOptions();

  const savedSolution = lsGet(LAST_SOLUTION_CALCULATED_KEY, null);

  if (savedSolution) {
    waterUnit = savedSolution.water_unit === "mol_l" ? "mol_l" : "mg_l";
    waterUnitToggle.checked = waterUnit === "mol_l";
    setCurrentLiters(savedSolution.liters || DEFAULT_LITERS, {
      scaleBatch: false,
      recalculate: false,
      invalidateSolver: false,
    });
    osmosisPercentInput.value = Number(savedSolution.osmosis_percent) || 0;
    waterProfileSelect.value = savedSolution.water_profile_value || "";
    waterFieldDefinitions.forEach((field) => {
      waterValues[field.key] = Number(savedSolution.water_values?.[field.key]) || 0;
    });
    applyWaterHelpers(waterValues, getMolarMass);
    renderWaterTable();
    applyRecipe({ fertilizers: savedSolution.fertilizers || [] });
    try {
      await calculateAndRender();
    } catch (error) {
      reportError(error, t("errors.calculateFailed"));
    }
    setApiStatus(t("status.apiReady"), "ready");
    return;
  }

  const preferredWaterProfile = preferences.last_water_profile || "default.yml";
  try {
    const profile = await fetchWaterProfileData(preferredWaterProfile);
    waterProfileSelect.value = preferredWaterProfile.endsWith(".yml")
      ? preferredWaterProfile
      : `${preferredWaterProfile}.yml`;
    applyWaterProfile(profile);
  } catch (error) {
    try {
      const defaultProfile = await fetchWaterProfileData("default");
      waterProfileSelect.value = "default.yml";
      applyWaterProfile(defaultProfile);
    } catch (defaultError) {
      renderWaterTable();
    }
  }

  try {
    const recipe = await fetchDefaultRecipe();
    applyRecipe(recipe, { applyLiters: false });
    await calculateAndRender();
  } catch (error) {
    renderSelectionTable();
    renderCalculatorTable();
    renderWaterSummaryTable(waterSummaryTable, {});
    renderOxideSummaryTable(oxideSummaryTable, {});
    renderIonSummaryTable(ionSummaryTable, {});
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  }
  setApiStatus(t("status.apiReady"), "ready");
}

addRowButton.addEventListener("click", addFertilizerRow);
removeRowButton.addEventListener("click", removeFertilizerRow);
calculateButton.addEventListener("click", async () => {
  try {
    await calculateAndRender();
    lsSet(LAST_SOLUTION_CALCULATED_KEY, buildSolutionSnapshot());
  } catch (error) {
    reportError(error, t("errors.calculateFailed"));
  }
});

modeToggleInputs.forEach((input) => {
  input.addEventListener("change", (event) => {
    setMode(event.target.value);
  });
});

if (summaryViewToggle) {
  summaryViewToggle.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-summary-view]");
    if (!button) {
      return;
    }
    setSummaryView(button.dataset.summaryView);
  });
}

fertEditorSearchInput.addEventListener("input", (event) => {
  fertilizerEditorFilter = event.target.value || "";
  renderFertilizerEditor();
});

fertEditorAddRowButton.addEventListener("click", addFertilizerEditorRow);
fertEditorDeleteRowButton.addEventListener("click", deleteFertilizerEditorRow);
fertEditorLoadButton.addEventListener("click", reloadFertilizerEditor);
fertEditorSaveButton.addEventListener("click", saveFertilizerEditor);

if (solverAllowedSearchInput) {
  solverAllowedSearchInput.addEventListener("input", (event) => {
    solverAllowedFilter = event.target.value || "";
    renderSolverAllowedOptions();
  });
}

if (solverAllowedFromRecipeButton) {
  solverAllowedFromRecipeButton.addEventListener("click", () => {
    syncSolverAllowedWithSelection("merge");
  });
}

if (solverAllowedAllButton) {
  solverAllowedAllButton.addEventListener("click", () => {
    updateSolverAllowedFertilizers(
      fertilizerOptions.map((fert) => fert.name),
      "replace"
    );
  });
}

if (solverAllowedHideInactiveInput) {
  solverAllowedHideInactiveInput.addEventListener("change", (event) => {
    solverAllowedHideInactive = event.target.checked;
    renderSolverAllowedOptions();
  });
}

if (solverAllowedClearButton) {
  solverAllowedClearButton.addEventListener("click", () => {
    updateSolverAllowedFertilizers([], "replace");
  });
}

if (solverAutoApplyInput) {
  solverAutoApplyInput.addEventListener("change", persistSolverAutoApplyPreference);
}

bindScaleButtons(
  solverTargetScaleDownButton,
  solverTargetScaleUpButton,
  () => solverTargetScaleFactor,
  applySolverTargetScaleFactor
);
bindScaleButtons(
  calculatorScaleDownButton,
  calculatorScaleUpButton,
  () => calculatorScaleFactor,
  applyCalculatorScaleFactor
);

if (configLitersInput) {
  configLitersInput.addEventListener("input", (event) => {
    const nextLiters = parseDecimalInput(event.target.value);
    if (nextLiters === null || nextLiters <= 0) {
      return;
    }
    setCurrentLiters(nextLiters, { scaleBatch: true, recalculate: true });
    persistPreferences({ default_liters: nextLiters });
  });
  configLitersInput.addEventListener("change", () => {
    updateLitersDisplay();
  });
}

solverConfigDefinitions.forEach((definition) => {
  const input = solverConfigControls[definition.key];
  if (!input) {
    return;
  }
  const eventName =
    definition.type === "boolean" || definition.key === "nitrogen_objective_mode" ? "change" : "input";
  input.addEventListener(eventName, () => {
    if (
      definition.type !== "boolean" &&
      definition.key !== "nitrogen_objective_mode" &&
      parseDecimalInput(input.value) === null
    ) {
      return;
    }
    renderSolverResults(null);
    persistPreferences({ solver_config: buildSolverConfigPayload() });
  });
  if (definition.type !== "boolean" && definition.key !== "nitrogen_objective_mode") {
    input.addEventListener("change", () => {
      normalizeDecimalInputElement(input, parseDecimalInput(input.value));
    });
  }
});

if (solverConfigResetDefaultsButton) {
  solverConfigResetDefaultsButton.addEventListener("click", () => {
    applySolverConfig();
    renderSolverResults(null);
    persistPreferences({ solver_config: {} });
  });
}

solveButton.addEventListener("click", async () => {
  if (!solverAllowedFertilizers.length) {
    reportError(
      null,
      t("solver.noAllowed")
    );
    return;
  }
  try {
    const data = await solveRecipe();
    renderSolverResults(data);
    if (solverAutoApplyEnabled()) {
      applySolverResultToCalculator({ switchToCalculator: false });
    }
  } catch (error) {
    reportError(error, t("errors.solveFailed"));
  }
});

if (copySolverResultsButton) {
  copySolverResultsButton.addEventListener("click", () => {
    copySolverResultsToClipboard();
  });
}

const applyRecipeProfile = async (recipe, context = "") => {
  solverAllowedContext = normalizeSolverAllowedContext(context || recipe?.filename || recipe?.name);
  applyRecipe(recipe);
  if (recipe?.solver_config && Object.keys(recipe.solver_config).length) {
    applySolverConfig({ ...buildSolverConfigPayload(), ...recipe.solver_config });
  }
  const hasStoredAllowed = restoreSolverAllowedFromStorage(solverAllowedContext);
  if (!hasStoredAllowed) {
    const recipeAllowed = Array.isArray(recipe?.fertilizers_allowed)
      ? recipe.fertilizers_allowed
      : collectSelectedFertilizerNames();
    updateSolverAllowedFertilizers(recipeAllowed, "replace");
  }
  if (recipe.water_profile) {
    const filename = recipe.water_profile.endsWith(".yml")
      ? recipe.water_profile
      : `${recipe.water_profile}.yml`;
    waterProfileSelect.value = filename;
    const profile = await fetchWaterProfileData(recipe.water_profile);
    applyWaterProfile(profile);
  }
  if (recipe.osmosis_percent !== undefined && recipe.osmosis_percent !== null) {
    osmosisPercentInput.value = recipe.osmosis_percent;
  }
  profileNameInput.value = recipe.name || "";
  scheduleRecalculate();
};

loadProfileButton.addEventListener("click", async () => {
  const selection = profileSelect.value;
  if (!selection) {
    reportError(null, t("errors.profileRequired"));
    return;
  }
  try {
    if (currentProfileMode === "solver") {
      const solution = await fetchNutrientSolutionData(selection);
      applyNutrientSolution(solution);
      profileNameInput.value = solution.name || "";
    } else {
      solverAllowedContext = normalizeSolverAllowedContext(selection);
      const recipe = await fetchRecipeData(selection);
      await applyRecipeProfile(recipe, selection);
    }
  } catch (error) {
    reportError(error, t("errors.loadProfile"));
  }
});

resetProfileButton.addEventListener("click", async () => {
  try {
    if (currentProfileMode === "solver") {
      resetSolverTargets();
    } else {
      const recipe = await fetchDefaultRecipe();
      await applyRecipeProfile(recipe, "default.yml");
    }
  } catch (error) {
    reportError(error, t("errors.resetFailed"));
  }
});

saveProfileButton.addEventListener("click", async () => {
  const name = profileNameInput.value.trim();
  if (!name) {
    reportError(null, t("errors.profileNameRequired"));
    return;
  }
  try {
    if (currentProfileMode === "solver") {
      const targets = {};
      solverTargetDefinitions.forEach((field) => {
        targets[field.key] = Number(solverTargetValues[field.key]) || 0;
      });
      await saveNutrientSolutionData({
        name,
        source: "Horticalc UI",
        targets_mg_per_l: targets,
      });
      nutrientSolutions = await fetchNutrientSolutions();
    } else {
      const payload = buildRecipePayloadFromSelection(name);
      await saveRecipeData(payload);
      recipeProfiles = await fetchRecipes();
    }
    renderProfileOptions();
  } catch (error) {
    reportError(error, t("errors.saveFailed"));
  }
});

saveSolverAsRecipeButton.addEventListener("click", async () => {
  const name = profileNameInput.value.trim();
  if (!name) {
    reportError(null, t("errors.profileNameRequired"));
    return;
  }
  if (!lastSolveResult) {
    reportError(null, t("solver.noResult"));
    return;
  }
  try {
    const payload = buildRecipePayloadFromSolver(name);
    await saveRecipeData(payload);
    recipeProfiles = await fetchRecipes();
    renderProfileOptions();
  } catch (error) {
    reportError(error, t("errors.saveRecipeFailed"));
  }
});

applySolverToCalculatorButton.addEventListener("click", async () => {
  applySolverResultToCalculator({ switchToCalculator: true });
});

if (applySolverToCalculatorInlineButton) {
  applySolverToCalculatorInlineButton.addEventListener("click", async () => {
    applySolverResultToCalculator({ switchToCalculator: true });
  });
}

loadWaterProfileButton.addEventListener("click", async () => {
  const selection = waterProfileSelect.value;
  if (!selection) {
    reportError(null, t("errors.waterProfileRequired"));
    return;
  }
  try {
    const profile = await fetchWaterProfileData(selection);
    applyWaterProfile(profile);
    persistPreferences({ last_water_profile: selection });
  } catch (error) {
    reportError(error, t("errors.loadWaterProfile"));
  }
});

resetWaterProfileButton.addEventListener("click", async () => {
  try {
    const profile = await fetchWaterProfileData("default");
    waterProfileSelect.value = "default.yml";
    applyWaterProfile(profile);
    persistPreferences({ last_water_profile: "default.yml" });
  } catch (error) {
    reportError(error, t("errors.loadWaterProfile"));
  }
});

saveWaterProfileButton.addEventListener("click", async () => {
  try {
    await saveWaterProfile();
    waterProfiles = await fetchWaterProfiles();
    renderWaterProfileOptions();
  } catch (error) {
    reportError(error, t("errors.saveFailed"));
  }
});

osmosisPercentInput.addEventListener("input", () => {
  scheduleRecalculate();
});
osmosisPercentInput.addEventListener("change", () => {
  normalizeDecimalInputElement(
    osmosisPercentInput,
    parseDecimalInput(osmosisPercentInput.value)
  );
});

waterUnitToggle.addEventListener("change", (event) => {
  waterUnit = event.target.checked ? "mol_l" : "mg_l";
  renderWaterTable();
  scheduleRecalculate();
});

summaryView = lsGet(SUMMARY_VIEW_KEY, "ion");
ionNitrogenExpanded = lsGet(ION_NITROGEN_EXPANDED_KEY, false);
initializeThemeControl();
initializeLanguageControl();
setSummaryView(summaryView);

initializeFertilizerTables();
bindShellNavigation();
updateLitersDisplay();
applySolverConfig();
updateCalculatorScaleDisplay();
renderSolverTargetsTable();
showShellView("fertilizers", { scroll: false });
updateSolverResultActions();
window.addEventListener("horticalc:localechange", refreshLocalizedUi);
init();
