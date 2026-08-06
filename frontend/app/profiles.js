import { qs } from "./dom.js";
import { createLatestRequestGate } from "../request_gate.js";

export function sortFavoriteProfiles(profiles = [], favorites = []) {
  const favoriteSet = new Set(favorites);
  return [...profiles].sort((left, right) =>
    Number(favoriteSet.has(right.filename)) - Number(favoriteSet.has(left.filename))
  );
}

export function createProfilesController({ api, i18n, notifications, actions }) {
  const sectionTitle = qs("#profileSectionTitle");
  const sectionHint = qs("#profileSectionHint");
  const select = qs("#profileSelect");
  const favoriteButton = qs("#favoriteProfile");
  const loadButton = qs("#loadProfile");
  const resetButton = qs("#resetProfile");
  const nameInput = qs("#profileName");
  const saveButton = qs("#saveProfile");
  const solverSetupOption = qs("#solverSetupOption");
  const includeSolverSetupInput = qs("#includeSolverSetup");
  const solverSetupWarning = qs("#solverSetupSaveWarning");
  const solverActions = qs("#solverProfileActions");
  const saveSolverAsRecipeButton = qs("#saveSolverAsRecipe");
  const applySolverButton = qs("#applySolverToCalculator");
  const requests = createLatestRequestGate();
  let mode = "calculator";
  let recipes = [];
  let nutrientSolutions = [];
  let favoriteRecipes = new Set();
  let favoriteNutrientSolutions = new Set();
  let mounted = false;
  const t = (key, params) => i18n.t(key, params);

  function activeFavorites() {
    return mode === "solver" ? favoriteNutrientSolutions : favoriteRecipes;
  }

  function refreshFavoriteButton() {
    const selected = select.value;
    const favorite = Boolean(selected) && activeFavorites().has(selected);
    const label = t(favorite ? "profile.removeFavorite" : "profile.addFavorite");
    favoriteButton.disabled = !selected;
    favoriteButton.textContent = favorite ? "★" : "☆";
    favoriteButton.setAttribute("aria-pressed", String(favorite));
    favoriteButton.setAttribute("aria-label", label);
    favoriteButton.title = label;
  }

  function refreshSetupWarning() {
    const activeCount = actions.getActiveFixedAmountCount();
    const visible = mode === "solver" && !includeSolverSetupInput.checked && activeCount > 0;
    solverSetupWarning.classList.toggle("is-hidden", !visible);
    solverSetupWarning.textContent = visible
      ? t("profile.solverSetupFixedWarning", { count: activeCount })
      : "";
  }

  function setSetupIncluded(included) {
    includeSolverSetupInput.checked = Boolean(included);
    refreshSetupWarning();
  }

  function renderOptions() {
    const profiles = mode === "solver" ? nutrientSolutions : recipes;
    const favorites = activeFavorites();
    const selected = select.value;
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = t("common.selectEmpty");
    select.replaceChildren(empty, ...sortFavoriteProfiles(profiles, favorites).map((profile) => {
      const option = document.createElement("option");
      option.value = profile.filename;
      const label = profile.name || profile.filename;
      option.textContent = favorites.has(profile.filename) ? `★ ${label}` : label;
      return option;
    }));
    select.value = selected;
    refreshFavoriteButton();
  }

  async function toggleFavorite() {
    const filename = select.value;
    if (!filename) return;
    const favorites = activeFavorites();
    if (favorites.has(filename)) favorites.delete(filename);
    else favorites.add(filename);
    const preferenceKey = mode === "solver" ? "favorite_nutrient_solutions" : "favorite_recipes";
    renderOptions();
    select.value = filename;
    refreshFavoriteButton();
    await api.persistPreferences({ [preferenceKey]: [...favorites] });
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
    solverSetupOption.classList.toggle("is-hidden", mode !== "solver");
    refreshSetupWarning();
    renderOptions();
  }

  async function loadSelected() {
    if (!select.value) {
      notifications.reportError(null, t("errors.profileRequired"));
      return;
    }
    const version = requests.reserve();
    const activeMode = mode;
    const includeSolverSetup = includeSolverSetupInput.checked;
    try {
      if (activeMode === "solver") {
        const solution = await api.fetchNutrientSolutionData(select.value, t("errors.loadNutrientSolution"));
        if (!requests.isCurrent(version) || mode !== activeMode) return;
        await actions.applyNutrientSolution(solution, {
          includeSetup: includeSolverSetup,
          isCurrent: () => requests.isCurrent(version),
        });
        if (!requests.isCurrent(version) || mode !== activeMode) return;
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
        setSetupIncluded(false);
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
        const includeSetup = includeSolverSetupInput.checked;
        if (!includeSetup) {
          const activeCount = actions.getActiveFixedAmountCount();
          if (activeCount > 0 && !window.confirm(t("profile.confirmOmitFixedAmounts", { count: activeCount }))) {
            return;
          }
        }
        const targetPayload = actions.buildNutrientSolution(name, includeSetup);
        try {
          await api.saveNutrientSolutionData(
            targetPayload,
            t("errors.saveNutrientSolutionFailed"),
          );
        } catch (error) {
          const conflict = error?.status === 409
            && error?.detail?.code === "nutrient_solution_exists"
            ? error.detail
            : null;
          if (!conflict) throw error;

          const existingName = String(conflict.name || conflict.filename || "").trim();
          const nameCollision = existingName && existingName !== name;
          const confirmKey = nameCollision
            ? "profile.confirmOverwriteCollision"
            : !includeSetup && conflict.has_solver_setup
              ? "profile.confirmRemoveSolverSetup"
              : "profile.confirmOverwrite";
          if (!window.confirm(t(confirmKey, { name: existingName || name }))) return;
          await api.saveNutrientSolutionData(
            { ...targetPayload, overwrite: true },
            t("errors.saveNutrientSolutionFailed"),
          );
        }
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
    select.addEventListener("change", refreshFavoriteButton);
    favoriteButton.addEventListener("click", toggleFavorite);
    includeSolverSetupInput.addEventListener("change", refreshSetupWarning);
    saveSolverAsRecipeButton.addEventListener("click", saveSolverRecipe);
    applySolverButton.addEventListener("click", () => actions.applySolverResult({ switchToCalculator: true }));
    setMode("calculator");
  }

  return {
    mount,
    refreshLocalized() { setMode(mode); },
    refreshSetupWarning,
    setMode,
    setProfiles({ recipeProfiles = [], solutions = [] } = {}) {
      recipes = recipeProfiles;
      nutrientSolutions = solutions;
      renderOptions();
    },
    setFavorites(preferences = {}) {
      favoriteRecipes = new Set(Array.isArray(preferences.favorite_recipes) ? preferences.favorite_recipes : []);
      favoriteNutrientSolutions = new Set(
        Array.isArray(preferences.favorite_nutrient_solutions)
          ? preferences.favorite_nutrient_solutions
          : []
      );
      renderOptions();
    },
  };
}
