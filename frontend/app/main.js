import * as api from "./api.js";
import * as i18n from "../i18n/runtime.js";
import {
  DEFAULT_LITERS,
  FALLBACK_LIQUID_VOLUME_UNITS,
  FALLBACK_MASS_UNITS,
  FALLBACK_SOLVER_CONFIG_DEFINITIONS,
  FALLBACK_VOLUME_UNITS,
  LAST_SOLUTION_CALCULATED_KEY,
} from "./constants.js";
import { createCalculatorController } from "./calculator.js";
import { createEditorController } from "./editor.js";
import { createNotifications } from "./notifications.js";
import { createProfilesController } from "./profiles.js";
import { createSettingsController } from "./settings.js";
import { createShellController } from "./shell.js";
import { createSolverController } from "./solver.js";
import { storageGet } from "./storage.js";
import { createUnitService } from "./units.js";
import { createWaterController } from "./water.js";

const notifications = createNotifications(i18n);
let calculator;
let editor;
let profiles;
let settings;
let shell;
let solver;
let water;

const units = createUnitService({
  onLitersChange({ previousLiters, nextLiters, scaleBatch, recalculate, invalidateSolver }) {
    if (scaleBatch && previousLiters > 0 && previousLiters !== nextLiters) {
      calculator.scaleBatch(previousLiters, nextLiters);
      solver.scaleFixedAmounts(previousLiters, nextLiters);
    }
    if (invalidateSolver) solver.renderResults(null);
    if (recalculate) calculator.scheduleRecalculate();
    settings?.render();
  },
  onDoseUnitsChange() {
    calculator.refreshDoseUnits();
    solver.refreshDoseUnits();
  },
});

water = createWaterController({
  api,
  i18n,
  notifications,
  onChange: () => calculator.scheduleRecalculate(),
});

solver = createSolverController({
  api,
  i18n,
  notifications,
  units,
  water,
  getSelectedFertilizers: () => calculator.collectSelectedFertilizerNames(),
  onApplyResult: (options) => calculator.applySolverResult(options),
  isActive: () => shell?.isActive("solver") || false,
});

calculator = createCalculatorController({
  api,
  i18n,
  notifications,
  units,
  water,
  getSolverResult: () => solver.lastResult,
  getSolverAllowed: () => solver.allowedFertilizers,
  getSolverUrea: () => solver.ureaAsNh4,
  onCalculation: (data) => shell.updateLiveResult(data),
  onShowCalculator: () => shell.show("fertilizers"),
});

editor = createEditorController({
  api,
  i18n,
  notifications,
  isActive: () => shell?.isActive("editor") || false,
  onCatalogChange(fertilizers) {
    calculator.setFertilizers(fertilizers);
    solver.setFertilizers(fertilizers);
    calculator.scheduleRecalculate();
  },
});

async function applyRecipeProfile(recipe, context, isCurrent = () => true) {
  let profile = null;
  let filename = "";
  if (recipe.water_profile) {
    filename = recipe.water_profile.endsWith(".yml") ? recipe.water_profile : `${recipe.water_profile}.yml`;
    profile = await water.loadProfile(recipe.water_profile);
  }
  if (!isCurrent()) return false;
  const allowedContext = context || recipe?.filename || recipe?.name || "global";
  calculator.applyRecipe(recipe);
  if (recipe?.solver_config && Object.keys(recipe.solver_config).length) {
    solver.applyConfig({ ...solver.buildConfigPayload(), ...recipe.solver_config });
  }
  const restored = solver.setAllowedContext(allowedContext);
  if (!restored) {
    solver.setAllowedFertilizers(
      Array.isArray(recipe?.fertilizers_allowed)
        ? recipe.fertilizers_allowed
        : calculator.collectSelectedFertilizerNames(),
      "replace",
    );
  }
  if (profile) {
    water.setSelectedProfile(filename);
    water.applyProfile(profile);
  }
  if (recipe.osmosis_percent !== undefined && recipe.osmosis_percent !== null) {
    water.setOsmosisPercent(recipe.osmosis_percent);
  }
  calculator.scheduleRecalculate();
  return true;
}

profiles = createProfilesController({
  api,
  i18n,
  notifications,
  actions: {
    applyNutrientSolution: (solution) => solver.applyNutrientSolution(solution),
    applyRecipeProfile,
    applySolverResult: (options) => calculator.applySolverResult(options),
    buildCalculatorRecipe: (name) => calculator.buildRecipePayloadFromSelection(name),
    buildNutrientSolution: (name) => ({
      name,
      source: "Horticalc UI",
      targets_mg_per_l: solver.targets,
    }),
    buildSolverRecipe: (name) => calculator.buildRecipePayloadFromSolver(name),
    hasSolverResult: () => Boolean(solver.lastResult),
    resetSolverTargets: () => solver.resetTargets(),
  },
});

shell = createShellController({
  i18n,
  onViewChange(nextView, previousView) {
    if (previousView === "editor") editor.deactivate();
    if (previousView === "solver") solver.deactivate();
    profiles.setMode(nextView === "solver" ? "solver" : "calculator");
    if (nextView === "editor") editor.activate();
    if (nextView === "solver") solver.activate();
  },
});

function refreshLocalizedUi() {
  notifications.refreshApiStatus();
  settings.render();
  shell.refreshLocalized();
  profiles.refreshLocalized();
  water.refreshLocalized();
  if (shell.isActive("editor")) editor.refreshLocalized();
  else if (shell.isActive("solver")) solver.refreshLocalized();
  else if (shell.isActive("fertilizers")) calculator.refreshLocalized();
}

settings = createSettingsController({
  units,
  i18n,
  persistPreferences: api.persistPreferences,
  onLocaleChange: refreshLocalizedUi,
});

function resourceValue(result, fallback, message, errors) {
  if (result.status === "fulfilled") return result.value;
  errors.push({ error: result.reason, message });
  return fallback;
}

async function loadStartupResources() {
  const results = await Promise.allSettled([
    api.fetchSolverConfigDefinitions(i18n.t("errors.loadSolverConfig")),
    api.fetchFertilizerCompKeys(i18n.t("errors.loadFertilizerSchema")),
    api.fetchFertilizers(i18n.t("errors.loadFertilizers")),
    api.fetchMolarMasses(i18n.t("errors.loadMolarMasses")),
    api.fetchWaterProfiles(i18n.t("errors.loadWaterProfiles")),
    api.fetchRecipes(i18n.t("errors.loadRecipes")),
    api.fetchNutrientSolutions(i18n.t("errors.loadNutrientSolutions")),
    api.fetchUnitDefinitions(i18n.t("errors.loadUnitSchema")),
  ]);
  const errors = [];
  return {
    solverConfigDefinitions: resourceValue(
      results[0],
      [...FALLBACK_SOLVER_CONFIG_DEFINITIONS],
      i18n.t("errors.loadSolverDefaults"),
      errors,
    ),
    fertilizerKeys: resourceValue(results[1], [], i18n.t("errors.loadFertilizerSchema"), errors),
    fertilizers: resourceValue(results[2], [], i18n.t("errors.loadFertilizers"), errors),
    molarMasses: resourceValue(results[3], {}, i18n.t("errors.loadMolarMasses"), errors),
    waterProfiles: resourceValue(results[4], [], i18n.t("errors.loadWaterProfiles"), errors),
    recipes: resourceValue(results[5], [], i18n.t("errors.loadRecipes"), errors),
    solutions: resourceValue(results[6], [], i18n.t("errors.loadNutrientSolutions"), errors),
    unitDefinitions: resourceValue(results[7], {
      volumeUnits: [...FALLBACK_VOLUME_UNITS],
      massUnits: [...FALLBACK_MASS_UNITS],
      liquidVolumeUnits: [...FALLBACK_LIQUID_VOLUME_UNITS],
    }, i18n.t("errors.loadUnitSchema"), errors),
    errors,
  };
}

async function loadInitialWater(preferences, errors) {
  const preferred = preferences.last_water_profile || "default.yml";
  try {
    const profile = await water.loadProfile(preferred);
    water.setSelectedProfile(preferred.endsWith(".yml") ? preferred : `${preferred}.yml`);
    water.applyProfile(profile);
  } catch (error) {
    try {
      const profile = await water.loadProfile("default");
      water.setSelectedProfile("default.yml");
      water.applyProfile(profile);
    } catch (defaultError) {
      errors.push({ error: defaultError, message: i18n.t("errors.loadWaterProfile") });
      notifications.reportError(defaultError, i18n.t("errors.loadWaterProfile"));
      water.renderTable();
    }
  }
}

async function init() {
  notifications.setApiStatus(i18n.t("status.loadingData"), "loading");
  const [preferences, resources] = await Promise.all([api.loadPreferences(), loadStartupResources()]);
  resources.errors.forEach(({ error, message }) => notifications.reportError(error, message));

  settings.mount(preferences, resources.unitDefinitions);
  water.setResources({ profiles: resources.waterProfiles, masses: resources.molarMasses });
  water.mount();
  calculator.mount();
  calculator.setFertilizers(resources.fertilizers);
  solver.setFertilizers(resources.fertilizers);
  solver.mount({ configDefinitions: resources.solverConfigDefinitions, config: preferences.solver_config || {} });
  editor.setData(resources.fertilizers, resources.fertilizerKeys);
  editor.mount();
  profiles.setProfiles({ recipeProfiles: resources.recipes, solutions: resources.solutions });
  profiles.mount();
  shell.mount();
  solver.setAllowedContext("global");

  const snapshot = storageGet(LAST_SOLUTION_CALCULATED_KEY, null);
  if (snapshot) {
    water.restoreSnapshot(snapshot);
    units.setLiters(snapshot.liters || DEFAULT_LITERS, {
      scaleBatch: false,
      recalculate: false,
      invalidateSolver: false,
    });
    calculator.applyRecipe({ fertilizers: snapshot.fertilizers || [] }, { applyLiters: false });
    try {
      await calculator.calculateAndRender();
    } catch (error) {
      resources.errors.push({ error, message: i18n.t("errors.calculateFailed") });
      notifications.reportError(error, i18n.t("errors.calculateFailed"));
    }
    notifications.finishStartup(resources.errors);
    return;
  }

  await loadInitialWater(preferences, resources.errors);
  try {
    const recipe = await api.fetchDefaultRecipe(i18n.t("errors.loadDefaultRecipe"));
    calculator.applyRecipe(recipe, { applyLiters: false });
    await calculator.calculateAndRender();
  } catch (error) {
    resources.errors.push({ error, message: i18n.t("errors.loadDefaultRecipe") });
    notifications.reportError(error, i18n.t("errors.loadDefaultRecipe"));
    calculator.refreshLocalized();
  }
  notifications.finishStartup(resources.errors);
}

init().catch((error) => {
  notifications.reportError(error, i18n.t("errors.unknown"));
  notifications.setApiStatus(i18n.t("status.dataIncomplete"), "error");
});
