function startupResourceValue(result, fallback, errorMessage, errors) {
  if (result.status === "fulfilled") {
    return result.value;
  }
  errors.push({ error: result.reason, message: errorMessage });
  return fallback;
}

async function loadStartupResources() {
  const results = await Promise.allSettled([
    fetchSolverConfigDefinitions(),
    fetchFertilizerCompKeys(),
    fetchFertilizers(),
    fetchMolarMasses(),
    fetchWaterProfiles(),
    fetchRecipes(),
    fetchNutrientSolutions(),
    fetchVolumeUnitDefinitions(),
  ]);
  const errors = [];
  return {
    solverConfigDefinitions: startupResourceValue(
      results[0],
      [...FALLBACK_SOLVER_CONFIG_DEFINITIONS],
      t("errors.loadSolverDefaults"),
      errors
    ),
    fertilizerEditorPreferredKeys: startupResourceValue(
      results[1],
      [],
      t("errors.loadFertilizerSchema"),
      errors
    ),
    fertilizerOptions: startupResourceValue(results[2], [], t("errors.loadFertilizers"), errors),
    molarMasses: startupResourceValue(results[3], {}, t("errors.loadMolarMasses"), errors),
    waterProfiles: startupResourceValue(results[4], [], t("errors.loadWaterProfiles"), errors),
    recipeProfiles: startupResourceValue(results[5], [], t("errors.loadRecipes"), errors),
    nutrientSolutions: startupResourceValue(
      results[6],
      [],
      t("errors.loadNutrientSolutions"),
      errors
    ),
    unitDefinitions: startupResourceValue(
      results[7],
      {
        volumeUnits: [...FALLBACK_VOLUME_UNITS],
        massUnits: [...FALLBACK_MASS_UNITS],
        liquidVolumeUnits: [...FALLBACK_LIQUID_VOLUME_UNITS],
      },
      t("errors.loadUnitSchema"),
      errors
    ),
    errors,
  };
}

async function init() {
  let hasStoredAllowed = false;
  setApiStatus(t("status.loadingData"), "loading");
  const [preferences, startupResources] = await Promise.all([
    loadPreferences(),
    loadStartupResources(),
  ]);
  solverConfigDefinitions = startupResources.solverConfigDefinitions;
  fertilizerEditorPreferredKeys = startupResources.fertilizerEditorPreferredKeys;
  fertilizerOptions = startupResources.fertilizerOptions;
  molarMasses = startupResources.molarMasses;
  waterProfiles = startupResources.waterProfiles;
  recipeProfiles = startupResources.recipeProfiles;
  nutrientSolutions = startupResources.nutrientSolutions;
  volumeUnitDefinitions = startupResources.unitDefinitions.volumeUnits;
  massUnitDefinitions = startupResources.unitDefinitions.massUnits;
  liquidVolumeUnitDefinitions = startupResources.unitDefinitions.liquidVolumeUnits;
  const startupErrors = startupResources.errors;
  startupErrors.forEach(({ error, message }) => reportError(error, message));

  applySolverConfig(preferences.solver_config || {});
  renderVolumeUnitOptions();
  setVolumeUnit(preferences.volume_unit || DEFAULT_VOLUME_UNIT);
  solidDoseUnit = normalizeSolidDoseUnit(preferences.solid_dose_unit || DEFAULT_SOLID_DOSE_UNIT);
  liquidDoseUnit = normalizeLiquidDoseUnit(preferences.liquid_dose_unit || DEFAULT_LIQUID_DOSE_UNIT);
  renderLinearUnitOptions(configSolidDoseUnitSelect, massUnitDefinitions, solidDoseUnit);
  renderLinearUnitOptions(configLiquidDoseUnitSelect, liquidVolumeUnitDefinitions, liquidDoseUnit);
  setCurrentLiters(preferences.default_liters || DEFAULT_LITERS, {
    scaleBatch: false,
    recalculate: false,
    invalidateSolver: false,
  });
  restoreSolverAutoApplyPreference();
  setFertilizerEditorData(fertilizerOptions);
  solverAllowedContext = normalizeSolverAllowedContext();
  hasStoredAllowed = restoreSolverAllowedFromStorage();
  if (!hasStoredAllowed) {
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  }

  renderWaterProfileOptions();
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
      startupErrors.push({ error, message: t("errors.calculateFailed") });
      reportError(error, t("errors.calculateFailed"));
    }
    finishStartupStatus(startupErrors);
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
      startupErrors.push({ error: defaultError, message: t("errors.loadWaterProfile") });
      reportError(defaultError, t("errors.loadWaterProfile"));
      renderWaterTable();
    }
  }

  try {
    const recipe = await fetchDefaultRecipe();
    applyRecipe(recipe, { applyLiters: false });
    await calculateAndRender();
  } catch (error) {
    startupErrors.push({ error, message: t("errors.loadDefaultRecipe") });
    reportError(error, t("errors.loadDefaultRecipe"));
    renderSelectionTable();
    renderCalculatorTable();
    renderWaterSummaryTable(waterSummaryTable, {});
    renderOxideSummaryTable(oxideSummaryTable, {});
    renderIonSummaryTable(ionSummaryTable, {});
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  }
  finishStartupStatus(startupErrors);
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

if (copyCalculatorResultsButton) {
  copyCalculatorResultsButton.addEventListener("click", () => {
    copyCalculatorResultsToClipboard();
  });
}

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
  if (fertilizerEditorSearchTimer) {
    clearTimeout(fertilizerEditorSearchTimer);
  }
  fertilizerEditorSearchTimer = window.setTimeout(() => {
    fertilizerEditorSearchTimer = null;
    applyFertilizerEditorFilter();
  }, FERTILIZER_EDITOR_SEARCH_DELAY_MS);
});

fertEditorAddRowButton.addEventListener("click", addFertilizerEditorRow);
fertEditorDeleteRowButton.addEventListener("click", deleteFertilizerEditorRow);
fertEditorLoadButton.addEventListener("click", reloadFertilizerEditor);
fertEditorSaveButton.addEventListener("click", saveFertilizerEditor);

if (solverAllowedSearchInput) {
  solverAllowedSearchInput.addEventListener("input", (event) => {
    solverAllowedFilter = event.target.value || "";
    if (solverAllowedSearchTimer) {
      clearTimeout(solverAllowedSearchTimer);
    }
    solverAllowedSearchTimer = window.setTimeout(() => {
      solverAllowedSearchTimer = null;
      renderSolverAllowedOptions();
    }, SOLVER_ALLOWED_SEARCH_DELAY_MS);
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
    const nextLiters = displayVolumeToLiters(event.target.value);
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
    setSolverApplyStatus(t("solver.configResetDone"));
  });
}

if (configVolumeUnitSelect) {
  configVolumeUnitSelect.addEventListener("change", (event) => {
    setVolumeUnit(event.target.value);
    persistPreferences({ volume_unit: volumeUnit });
  });
}

if (configSolidDoseUnitSelect) {
  configSolidDoseUnitSelect.addEventListener("change", (event) => {
    setSolidDoseUnit(event.target.value, { refresh: true });
    persistPreferences({ solid_dose_unit: solidDoseUnit });
  });
}

if (configLiquidDoseUnitSelect) {
  configLiquidDoseUnitSelect.addEventListener("change", (event) => {
    setLiquidDoseUnit(event.target.value, { refresh: true });
    persistPreferences({ liquid_dose_unit: liquidDoseUnit });
  });
}

solverUreaToggle.addEventListener("change", () => renderSolverResults(null));

solveButton.addEventListener("click", async () => {
  if (!solverAllowedFertilizers.length) {
    reportError(
      null,
      t("solver.noAllowed")
    );
    return;
  }
  const requestVersion = solveRequests.reserve();
  try {
    const data = await solveRecipe();
    if (!solveRequests.isCurrent(requestVersion)) {
      return;
    }
    renderSolverResults(data);
    if (solverAutoApplyEnabled()) {
      applySolverResultToCalculator({ switchToCalculator: false });
    }
  } catch (error) {
    if (!solveRequests.isCurrent(requestVersion)) {
      return;
    }
    reportError(error, t("errors.solveFailed"));
  }
});

if (copySolverResultsButton) {
  copySolverResultsButton.addEventListener("click", () => {
    copySolverResultsToClipboard();
  });
}

const applyRecipeProfile = async (recipe, context = "", requestVersion = null) => {
  let waterProfile = null;
  let waterProfileFilename = "";
  if (recipe.water_profile) {
    waterProfileFilename = recipe.water_profile.endsWith(".yml")
      ? recipe.water_profile
      : `${recipe.water_profile}.yml`;
    waterProfile = await fetchWaterProfileData(recipe.water_profile);
  }
  if (requestVersion !== null && !profileRequests.isCurrent(requestVersion)) {
    return false;
  }
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
  if (waterProfile) {
    waterProfileSelect.value = waterProfileFilename;
    applyWaterProfile(waterProfile);
  }
  if (recipe.osmosis_percent !== undefined && recipe.osmosis_percent !== null) {
    osmosisPercentInput.value = recipe.osmosis_percent;
  }
  profileNameInput.value = recipe.name || "";
  scheduleRecalculate();
  return true;
};

loadProfileButton.addEventListener("click", async () => {
  const selection = profileSelect.value;
  if (!selection) {
    reportError(null, t("errors.profileRequired"));
    return;
  }
  const requestVersion = profileRequests.reserve();
  const profileMode = currentProfileMode;
  try {
    if (profileMode === "solver") {
      const solution = await fetchNutrientSolutionData(selection);
      if (!profileRequests.isCurrent(requestVersion) || currentProfileMode !== profileMode) {
        return;
      }
      applyNutrientSolution(solution);
      profileNameInput.value = solution.name || "";
    } else {
      const recipe = await fetchRecipeData(selection);
      if (currentProfileMode !== profileMode) {
        return;
      }
      await applyRecipeProfile(recipe, selection, requestVersion);
    }
  } catch (error) {
    if (!profileRequests.isCurrent(requestVersion) || currentProfileMode !== profileMode) {
      return;
    }
    reportError(error, t("errors.loadProfile"));
  }
});

resetProfileButton.addEventListener("click", async () => {
  const requestVersion = profileRequests.reserve();
  const profileMode = currentProfileMode;
  try {
    if (profileMode === "solver") {
      resetSolverTargets();
    } else {
      const recipe = await fetchDefaultRecipe();
      if (currentProfileMode !== profileMode) {
        return;
      }
      await applyRecipeProfile(recipe, "default.yml", requestVersion);
    }
  } catch (error) {
    if (!profileRequests.isCurrent(requestVersion) || currentProfileMode !== profileMode) {
      return;
    }
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
  const requestVersion = waterProfileRequests.reserve();
  try {
    const profile = await fetchWaterProfileData(selection);
    if (!waterProfileRequests.isCurrent(requestVersion)) {
      return;
    }
    applyWaterProfile(profile);
    persistPreferences({ last_water_profile: selection });
  } catch (error) {
    if (!waterProfileRequests.isCurrent(requestVersion)) {
      return;
    }
    reportError(error, t("errors.loadWaterProfile"));
  }
});

resetWaterProfileButton.addEventListener("click", async () => {
  const requestVersion = waterProfileRequests.reserve();
  try {
    const profile = await fetchWaterProfileData("default");
    if (!waterProfileRequests.isCurrent(requestVersion)) {
      return;
    }
    waterProfileSelect.value = "default.yml";
    applyWaterProfile(profile);
    persistPreferences({ last_water_profile: "default.yml" });
  } catch (error) {
    if (!waterProfileRequests.isCurrent(requestVersion)) {
      return;
    }
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
  waterProfileRequests.invalidate();
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
