let preferenceLoadPromise;
let preferenceWritePromise = Promise.resolve();
let preferences = {};

async function responseJson(response, errorMessage) {
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = data.detail;
    const error = new Error(typeof detail === "string" ? detail : errorMessage);
    error.status = response.status;
    error.detail = detail;
    throw error;
  }
  return response.json();
}

export async function getJson(url, errorMessage) {
  return responseJson(await fetch(url), errorMessage);
}

export async function postJson(url, payload, errorMessage) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return responseJson(response, errorMessage);
}

export async function putJson(url, payload, errorMessage, { keepalive = false } = {}) {
  const response = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    keepalive,
  });
  return responseJson(response, errorMessage);
}

export async function deleteJson(url, errorMessage) {
  return responseJson(await fetch(url, { method: "DELETE" }), errorMessage);
}

export function loadPreferences() {
  if (!preferenceLoadPromise) {
    preferenceLoadPromise = getJson("/preferences", "Unable to load preferences")
      .then((data) => {
        preferences = data && typeof data === "object" ? data : {};
        return preferences;
      })
      .catch(() => preferences);
  }
  return preferenceLoadPromise;
}

export function persistPreferences(updates) {
  preferences = { ...preferences, ...updates };
  preferenceWritePromise = preferenceWritePromise.then(() =>
    putJson("/preferences", updates, "Unable to save preferences", { keepalive: true })
      .then((data) => {
        preferences = data && typeof data === "object" ? data : preferences;
        return preferences;
      })
      .catch(() => preferences)
  );
  return preferenceWritePromise;
}

export const fetchFertilizers = (message) => getJson("/fertilizers", message);
export const putFertilizers = (payload, message) => putJson("/fertilizers", payload, message);
export const fetchMolarMasses = (message) => getJson("/molar-masses", message);
export const fetchWaterProfiles = (message) => getJson("/water-profiles", message);
export const fetchWaterProfileData = (filename, message) =>
  getJson(`/water-profiles/${encodeURIComponent(filename)}`, message);
export const saveWaterProfileData = (payload, message) =>
  postJson("/water-profiles", payload, message);
export const fetchDefaultRecipe = (message) => getJson("/recipes/default", message);
export const fetchRecipes = (message) => getJson("/recipes", message);
export const fetchRecipeData = (filename, message) =>
  getJson(`/recipes/${encodeURIComponent(filename)}`, message);
export const saveRecipeData = (payload, message) => postJson("/recipes", payload, message);
export const deleteRecipeData = (filename, message) =>
  deleteJson(`/recipes/${encodeURIComponent(filename)}`, message);
export const fetchNutrientSolutions = (message) => getJson("/nutrient-solutions", message);
export const fetchNutrientSolutionData = (filename, message) =>
  getJson(`/nutrient-solutions/${encodeURIComponent(filename)}`, message);
export const saveNutrientSolutionData = (payload, message) =>
  postJson("/nutrient-solutions", payload, message);
export const deleteNutrientSolutionData = (filename, message) =>
  deleteJson(`/nutrient-solutions/${encodeURIComponent(filename)}`, message);
export const calculate = (payload, message) => postJson("/calculate", payload, message);
export const solve = (payload, message) => postJson("/solve", payload, message);
export const fetchSolverHistory = (message) => getJson("/solver-history", message);
export const fetchSolverHistoryEntry = (entryId, message) =>
  getJson(`/solver-history/${encodeURIComponent(entryId)}`, message);
export const setSolverHistoryPinned = (entryId, pinned, message) =>
  putJson(`/solver-history/${encodeURIComponent(entryId)}`, { pinned }, message);
export const clearSolverHistory = (message) => deleteJson("/solver-history", message);

export async function fetchAppVersion() {
  const data = await getJson("/health", "Unable to load application version");
  return typeof data?.version === "string" ? data.version : "";
}

export async function fetchFertilizerCompKeys(message) {
  const data = await getJson("/schema/fertilizer-comp-keys", message);
  return Array.isArray(data) ? data : Array.isArray(data?.keys) ? data.keys : [];
}

export async function fetchSolverConfigDefinitions(message) {
  const data = await getJson("/schema/solver-config", message);
  return data?.definitions || [];
}

export async function fetchPreferenceOptions(message) {
  const data = await getJson("/schema/preferences", message);
  return {
    defaultTheme: data?.default_theme,
    defaultUiScale: data?.default_ui_scale,
    themes: Array.isArray(data?.themes) ? data.themes : [],
    uiScales: Array.isArray(data?.ui_scales) ? data.ui_scales : [],
    locales: Array.isArray(data?.locales) ? data.locales : [],
  };
}

function normalizeDefinitions(entries, factorKey, canonicalKey, message) {
  if (!Array.isArray(entries) || !entries.length) throw new Error(message);
  const definitions = entries.filter((definition) => definition
    && typeof definition.key === "string"
    && typeof definition.symbol === "string"
    && Number.isFinite(Number(definition[factorKey]))
    && Number(definition[factorKey]) > 0
  ).map((definition) => ({ ...definition, [factorKey]: Number(definition[factorKey]) }));
  if (!definitions.some((definition) => definition.key === canonicalKey)) throw new Error(message);
  return definitions;
}

export async function fetchUnitDefinitions(message) {
  const data = await getJson("/schema/units", message);
  return {
    volumeUnits: normalizeDefinitions(data.volume_units, "liters_per_unit", "liter", message),
    massUnits: normalizeDefinitions(data.mass_units, "grams_per_unit", "gram", message),
    liquidVolumeUnits: normalizeDefinitions(
      data.liquid_volume_units,
      "milliliters_per_unit",
      "milliliter",
      message,
    ),
  };
}
