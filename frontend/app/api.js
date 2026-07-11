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
  preferenceWritePromise = preferenceWritePromise.then(() =>
    fetch(`${apiBase()}/preferences`, {
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
      .catch(() => userPreferences)
  );
  return preferenceWritePromise;
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

async function calculateAndRender(payloadOverride = null, requestVersion = null) {
  const activeVersion = requestVersion ?? calculationRequests.reserve();
  if (!calculationRequests.isCurrent(activeVersion)) {
    return null;
  }
  setCalculatorResultCurrent(false);
  let data;
  try {
    data = await calculate(payloadOverride);
  } catch (error) {
    if (!calculationRequests.isCurrent(activeVersion)) {
      return null;
    }
    throw error;
  }
  if (!calculationRequests.isCurrent(activeVersion)) {
    return null;
  }
  renderCalculation(data);
  return data;
}

async function fetchVolumeUnitDefinitions() {
  const data = await fetchJson(`${apiBase()}/schema/units`, t("errors.loadUnitSchema"));
  const normalizeDefinitions = (entries, factorKey, canonicalKey) => {
    if (!Array.isArray(entries) || !entries.length) {
      throw new Error(t("errors.loadUnitSchema"));
    }
    const definitions = entries.filter(
      (definition) => definition
        && typeof definition.key === "string"
        && typeof definition.symbol === "string"
        && Number.isFinite(Number(definition[factorKey]))
        && Number(definition[factorKey]) > 0
    ).map((definition) => ({
      ...definition,
      [factorKey]: Number(definition[factorKey]),
    }));
    if (!definitions.some((definition) => definition.key === canonicalKey)) {
      throw new Error(t("errors.loadUnitSchema"));
    }
    return definitions;
  };
  return {
    volumeUnits: normalizeDefinitions(data.volume_units, "liters_per_unit", DEFAULT_VOLUME_UNIT),
    massUnits: normalizeDefinitions(data.mass_units, "grams_per_unit", DEFAULT_SOLID_DOSE_UNIT),
    liquidVolumeUnits: normalizeDefinitions(
      data.liquid_volume_units,
      "milliliters_per_unit",
      DEFAULT_LIQUID_DOSE_UNIT
    ),
  };
}

function buildRecipePayload(name, fertilizers, liters, ureaAsNh4) {
  const payload = {
    name,
    liters,
    fertilizers,
    fertilizers_allowed: solverAllowedFertilizers,
    urea_as_nh4: ureaAsNh4,
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
