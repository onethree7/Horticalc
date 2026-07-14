import { qs } from "./dom.js";
import { createLatestRequestGate } from "../request_gate.js";

export function createProfilesController({ api, i18n, notifications, actions }) {
  const sectionTitle = qs("#profileSectionTitle");
  const sectionHint = qs("#profileSectionHint");
  const select = qs("#profileSelect");
  const loadButton = qs("#loadProfile");
  const resetButton = qs("#resetProfile");
  const nameInput = qs("#profileName");
  const saveButton = qs("#saveProfile");
  const solverActions = qs("#solverProfileActions");
  const saveSolverAsRecipeButton = qs("#saveSolverAsRecipe");
  const applySolverButton = qs("#applySolverToCalculator");
  const requests = createLatestRequestGate();
  let mode = "calculator";
  let recipes = [];
  let nutrientSolutions = [];
  let mounted = false;
  const t = (key, params) => i18n.t(key, params);

  function renderOptions() {
    const profiles = mode === "solver" ? nutrientSolutions : recipes;
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = t("common.selectEmpty");
    select.replaceChildren(empty, ...profiles.map((profile) => {
      const option = document.createElement("option");
      option.value = profile.filename;
      option.textContent = profile.name || profile.filename;
      return option;
    }));
  }

  function setMode(nextMode) {
    const normalized = nextMode === "solver" ? "solver" : "calculator";
    if (normalized !== mode) requests.invalidate();
    mode = normalized;
    const titleKey = mode === "solver" ? "profile.targetTitle" : "profile.recipeTitle";
    const hintKey = mode === "solver" ? "profile.targetHint" : "profile.recipeHint";
    sectionTitle.dataset.i18n = titleKey;
    sectionHint.dataset.i18n = hintKey;
    sectionTitle.textContent = t(titleKey);
    sectionHint.textContent = t(hintKey);
    solverActions.classList.toggle("is-hidden", mode !== "solver");
    renderOptions();
  }

  async function loadSelected() {
    if (!select.value) {
      notifications.reportError(null, t("errors.profileRequired"));
      return;
    }
    const version = requests.reserve();
    const activeMode = mode;
    try {
      if (activeMode === "solver") {
        const solution = await api.fetchNutrientSolutionData(select.value, t("errors.loadNutrientSolution"));
        if (!requests.isCurrent(version) || mode !== activeMode) return;
        actions.applyNutrientSolution(solution);
        nameInput.value = solution.name || "";
      } else {
        const recipe = await api.fetchRecipeData(select.value, t("errors.loadRecipe"));
        if (!requests.isCurrent(version) || mode !== activeMode) return;
        await actions.applyRecipeProfile(recipe, select.value, () => requests.isCurrent(version));
        nameInput.value = recipe.name || "";
      }
    } catch (error) {
      if (requests.isCurrent(version) && mode === activeMode) {
        notifications.reportError(error, t("errors.loadProfile"));
      }
    }
  }

  async function reset() {
    const version = requests.reserve();
    const activeMode = mode;
    try {
      if (activeMode === "solver") {
        actions.resetSolverTargets();
      } else {
        const recipe = await api.fetchDefaultRecipe(t("errors.loadDefaultRecipe"));
        if (!requests.isCurrent(version) || mode !== activeMode) return;
        await actions.applyRecipeProfile(recipe, "default.yml", () => requests.isCurrent(version));
      }
    } catch (error) {
      if (requests.isCurrent(version) && mode === activeMode) {
        notifications.reportError(error, t("errors.resetFailed"));
      }
    }
  }

  async function save() {
    const name = nameInput.value.trim();
    if (!name) {
      notifications.reportError(null, t("errors.profileNameRequired"));
      return;
    }
    try {
      if (mode === "solver") {
        await api.saveNutrientSolutionData(actions.buildNutrientSolution(name), t("errors.saveNutrientSolutionFailed"));
        nutrientSolutions = await api.fetchNutrientSolutions(t("errors.loadNutrientSolutions"));
      } else {
        await api.saveRecipeData(actions.buildCalculatorRecipe(name), t("errors.saveRecipeFailed"));
        recipes = await api.fetchRecipes(t("errors.loadRecipes"));
      }
      renderOptions();
    } catch (error) {
      notifications.reportError(error, t("errors.saveFailed"));
    }
  }

  async function saveSolverRecipe() {
    const name = nameInput.value.trim();
    if (!name) {
      notifications.reportError(null, t("errors.profileNameRequired"));
      return;
    }
    if (!actions.hasSolverResult()) {
      notifications.reportError(null, t("solver.noResult"));
      return;
    }
    try {
      await api.saveRecipeData(actions.buildSolverRecipe(name), t("errors.saveRecipeFailed"));
      recipes = await api.fetchRecipes(t("errors.loadRecipes"));
      renderOptions();
    } catch (error) {
      notifications.reportError(error, t("errors.saveRecipeFailed"));
    }
  }

  function mount() {
    if (mounted) return;
    mounted = true;
    loadButton.addEventListener("click", loadSelected);
    resetButton.addEventListener("click", reset);
    saveButton.addEventListener("click", save);
    saveSolverAsRecipeButton.addEventListener("click", saveSolverRecipe);
    applySolverButton.addEventListener("click", () => actions.applySolverResult({ switchToCalculator: true }));
    setMode("calculator");
  }

  return {
    mount,
    refreshLocalized() { setMode(mode); },
    setMode,
    setProfiles({ recipeProfiles = [], solutions = [] } = {}) {
      recipes = recipeProfiles;
      nutrientSolutions = solutions;
      renderOptions();
    },
  };
}
