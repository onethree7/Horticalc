/*
 * Horticalc final WebView bridge (migration-only).
 *
 * Add this module to the last legacy frontend release and expose
 * exportUiState() from a visible "Export native state" action. It reads only
 * localStorage, validates/normalizes the values, and downloads the canonical
 * user/ui_state.json envelope. The native application does not ship or
 * execute this JavaScript.
 */

export const UI_STATE_SCHEMA_VERSION = 1;
export const SUPPORTED_LOCALES = new Set(["de", "en", "nl", "es", "zh"]);
export const ALLOWED_CONTEXT_PREFIX = "last_fertilizers_allowed::";

// Keep this list explicit: it is the migration contract between the final
// browser release and the typed native UiState envelope. Theme, units, and
// solver preferences are deliberately not listed because they already live in
// the durable preferences file and do not require browser-state export.
export const BRIDGE_STATE_FIELDS = Object.freeze([
  "schema_version",
  "last_calculation",
  "last_calculation_input",
  "summary_tab",
  "summary_view",
  "expanded_nitrogen",
  "solver_auto_apply",
  "solver_allowed_fertilizers",
  "solver_allowed_fertilizers_by_context",
  "locale",
  "result_tab_index",
]);

export const STORAGE_KEYS = Object.freeze({
  lastCalculation: "last_solution_calculated",
  summaryView: "horticalc.summary_view",
  expandedNitrogen: "horticalc.ion_n_expanded",
  solverAutoApply: "horticalc.solver_auto_apply",
  locale: "horticalc.locale",
});

const RESULT_TAB_INDEX = Object.freeze({
  summary: 0,
  overview: 0,
  nutrient: 1,
  nutrients: 1,
  form: 1,
  forms: 1,
  ion: 2,
  ions: 2,
  balance: 2,
  ec: 3,
  metrics: 3,
  component: 4,
  components: 4,
  npk: 5,
  sluijsmann: 5,
});

function finiteNumber(value, fallback = 0) {
  const number = typeof value === "number" ? value : Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function nonNegativeNumber(value, fallback = 0) {
  const number = finiteNumber(value, fallback);
  return number >= 0 ? number : fallback;
}

function readJson(storage, key, fallback) {
  try {
    const raw = storage?.getItem(key);
    if (!raw) return fallback;
    const value = JSON.parse(raw);
    return value === null || value === undefined ? fallback : value;
  } catch {
    return fallback;
  }
}

function readString(storage, key, fallback) {
  try {
    const raw = storage?.getItem(key);
    if (raw === null || raw === undefined || raw === "") return fallback;
    try {
      const parsed = JSON.parse(raw);
      return typeof parsed === "string" ? parsed : String(raw);
    } catch {
      // The legacy locale writer stored its value as a raw string while the
      // other browser settings use JSON.stringify.
      return String(raw);
    }
  } catch {
    return fallback;
  }
}

function uniqueStrings(values) {
  if (!Array.isArray(values)) return [];
  return Array.from(new Set(values
    .map((value) => String(value || "").trim())
    .filter(Boolean)));
}

function orderedObject(values) {
  return Object.fromEntries(Object.entries(values).sort(([left], [right]) => left.localeCompare(right)));
}

function normalizeWaterSnapshot(snapshot) {
  const rawValues = snapshot && typeof snapshot.water_values === "object"
    ? snapshot.water_values
    : {};
  const ions = {};
  Object.entries(rawValues).forEach(([key, value]) => {
    const name = String(key || "").trim();
    if (!name) return;
    ions[name] = nonNegativeNumber(value);
  });
  const ro = Math.min(100, Math.max(0, nonNegativeNumber(snapshot?.osmosis_percent)));
  const profileName = String(snapshot?.water_profile_value || "").trim();
  return {
    name: profileName || "legacy-local-storage",
    volume_l: 0,
    ions_mg_l: orderedObject(ions),
    ro_percent: ro,
  };
}

function normalizeCalculationSnapshot(value) {
  if (!value || typeof value !== "object") return null;
  const liters = finiteNumber(value.liters, 0);
  if (!(liters > 0)) return null;
  const doses = {};
  if (Array.isArray(value.fertilizers)) {
    value.fertilizers.forEach((entry) => {
      const name = String(entry?.name || "").trim();
      const grams = nonNegativeNumber(entry?.grams, -1);
      if (name && grams >= 0) doses[name] = grams;
    });
  }
  const water = normalizeWaterSnapshot(value);
  return {
    volume_l: liters,
    doses_g: orderedObject(doses),
    water,
    urea_mode: false,
    osmosis_percent: water.ro_percent,
  };
}

function readAllowedByContext(storage) {
  const contexts = {};
  const count = Number(storage?.length) || 0;
  for (let index = 0; index < count; index += 1) {
    const key = storage.key(index);
    if (!key || !key.startsWith(ALLOWED_CONTEXT_PREFIX)) continue;
    const context = key.slice(ALLOWED_CONTEXT_PREFIX.length).trim() || "global";
    const values = uniqueStrings(readJson(storage, key, []));
    contexts[context] = values;
  }
  const ordered = {};
  Object.keys(contexts).sort().forEach((key) => { ordered[key] = contexts[key]; });
  return ordered;
}

function readResultTabIndex(storage) {
  // Older builds wrote this setting as a raw localStorage string while newer
  // builds JSON-encoded it. Use the tolerant string reader for both forms so
  // the migration does not silently reset the selected result tab.
  const value = String(readString(storage, STORAGE_KEYS.summaryView, "summary") || "")
    .trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(RESULT_TAB_INDEX, value)
    ? RESULT_TAB_INDEX[value]
    : 0;
}

export function buildUiState(storage = globalThis.localStorage) {
  const contexts = readAllowedByContext(storage);
  const globalAllowed = contexts.global || [];
  const localeValue = String(readString(storage, STORAGE_KEYS.locale, "en") || "")
    .trim().toLowerCase();
  const locale = SUPPORTED_LOCALES.has(localeValue) ? localeValue : "en";
  const snapshot = normalizeCalculationSnapshot(
    readJson(storage, STORAGE_KEYS.lastCalculation, null),
  );
  return {
    schema_version: UI_STATE_SCHEMA_VERSION,
    last_calculation: null,
    last_calculation_input: snapshot,
    summary_tab: "calculator",
    summary_view: String(readString(storage, STORAGE_KEYS.summaryView, "ion") || "ion")
      .trim().toLowerCase() || "ion",
    expanded_nitrogen: readJson(storage, STORAGE_KEYS.expandedNitrogen, false) === true,
    solver_auto_apply: readJson(storage, STORAGE_KEYS.solverAutoApply, true) !== false,
    solver_allowed_fertilizers: globalAllowed,
    solver_allowed_fertilizers_by_context: contexts,
    locale,
    result_tab_index: readResultTabIndex(storage),
  };
}

export function downloadUiState(state, {
  documentRef = globalThis.document,
  filename = "ui_state.json",
} = {}) {
  if (!documentRef || typeof Blob === "undefined" || !globalThis.URL?.createObjectURL) {
    return false;
  }
  const blob = new Blob([`${JSON.stringify(state, null, 2)}\n`], {
    type: "application/json",
  });
  const url = globalThis.URL.createObjectURL(blob);
  const anchor = documentRef.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.hidden = true;
  documentRef.body?.appendChild(anchor);
  anchor.click();
  anchor.remove();
  globalThis.URL.revokeObjectURL(url);
  return true;
}

export function exportUiState({
  storage = globalThis.localStorage,
  download = true,
  documentRef = globalThis.document,
  filename = "ui_state.json",
} = {}) {
  const state = buildUiState(storage);
  if (download) downloadUiState(state, { documentRef, filename });
  return state;
}
