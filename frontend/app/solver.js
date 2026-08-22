import {
  FALLBACK_SOLVER_CONFIG_DEFINITIONS,
  LAST_FERTILIZERS_ALLOWED_CONTEXT_KEY_PREFIX,
  NUTRIENT_FORMATTER,
  SOLVER_AUTO_APPLY_KEY,
  SUMMARY_COLUMN_ORDER,
} from "./constants.js";
import { appendDoseInput, qs } from "./dom.js";
import {
  decimalInputValue,
  formatNumber,
  normalizeDecimalInputElement,
  parseDecimalInput,
  roundScaledValue,
} from "./formatting.js";
import { applyScaledValues, bindScaleButtons, scaleAmountsByVolume } from "./scaling.js";
import {
  applySolverConfig,
  buildSolverConfigPayload,
  normalizeSolverConfigDefinitions,
} from "./solver_config.js";
import {
  activeFixedAmountCount,
  buildSolvePayload as createSolvePayload,
  solverResultDisplayKeys,
} from "./solver_payload.js";
import { renderSolverTables } from "./solver_rendering.js";
import { buildSolverPrintableText } from "./solver_printable.js";
import {
  DEFAULT_TARGET_PRIORITY,
  HIERARCHICAL_MODEL,
  NNLS_TUNING_MODEL,
  normalizedPriority,
  solverModelLabel,
  targetPrioritySummary,
} from "./solver_presentation.js";
import { storageGet, storageSet } from "./storage.js";
import { createLatestRequestGate } from "../request_gate.js";

export function createSolverController({
  api, i18n, notifications, units, water, getSelectedFertilizers,
  onApplyResult, onFixedAmountsChange = () => {}, onSolved = () => {}, isActive,
}) {
const solverTargetsTableEl = qs("#solverTargetsTable");
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
const solverModelUsed = qs("#solverModelUsed");
const solverMassModelHint = qs("#solverMassModelHint");
const solverTargetScaleDownButton = qs("#solverTargetScaleDown");
const solverTargetScaleUpButton = qs("#solverTargetScaleUp");
const solverTargetScaleValue = qs("#solverTargetScaleValue");
const solverPriorityLegend = qs("#solverPriorityLegend");
const solveButton = qs("#solveBtn");
const copySolverResultsButton = qs("#copySolverResults");
const solverAutoApplyInput = qs("#solverAutoApply");
const applySolverToCalculatorInlineButton = qs("#applySolverToCalculatorInline");
const saveSolverAsRecipeButton = qs("#saveSolverAsRecipe");
const applySolverToCalculatorButton = qs("#applySolverToCalculator");
const solverUreaToggle = qs("#solverUreaToggle");
const solverConfigResetDefaultsButton = qs("#solverConfigResetDefaults");
const solverConfigControls = {
  solver_model: qs("#solverConfigModel"),
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
const solverTargetDefinitions = [
  "N_total", "N_NH4", "N_NO3", "N_UREA", "P", "K", "Ca", "Mg", "S",
  "Fe", "Mn", "Cu", "Zn", "B", "Mo", "Si", "Cl", "Na", "HCO3",
].map((key) => ({ key, label: key }));
const solverTargetValues = Object.fromEntries(solverTargetDefinitions.map(({ key }) => [key, 0]));
const solverTargetBaseValues = { ...solverTargetValues };
const solverTargetPriorities = {};
const solverAllowedFertilizers = [];
const solverFixedGrams = {};
const solveRequests = createLatestRequestGate();
const t = (key, params) => i18n.t(key, params);
const nutrientFormatter = NUTRIENT_FORMATTER;
const summaryColumnOrder = SUMMARY_COLUMN_ORDER;
let solverConfigDefinitions = [...FALLBACK_SOLVER_CONFIG_DEFINITIONS];
let fertilizerOptions = [];
let lastSolveResult = null;
let solverTargetScaleFactor = 1;
let solverAllowedContext = "global";
let solverAllowedFilter = "";
let solverAllowedHideInactive = false;
let searchTimer;
let mounted = false;

const MASS_MODEL = "mass_nnls";
const REPORT_ONLY_TARGETS = new Set(["Na", "Cl"]);
const TARGET_PRIORITY_LEVELS = [1, 2, 3, 4, 0];

function setTargetPriorities(priorities = {}, ignoredElements = []) {
  const ignored = new Set(Array.isArray(ignoredElements) ? ignoredElements : []);
  solverTargetDefinitions.forEach(({ key }) => {
    const reportOnly = REPORT_ONLY_TARGETS.has(key) || ignored.has(key);
    const configured = priorities?.[key] || {};
    solverTargetPriorities[key] = {
      under: reportOnly ? 0 : normalizedPriority(configured.under),
      over: reportOnly ? 0 : normalizedPriority(configured.over),
    };
  });
}

function serializedTargetPriorities() {
  return Object.fromEntries(solverTargetDefinitions.flatMap(({ key }) => {
    if (REPORT_ONLY_TARGETS.has(key)) return [];
    const priorities = solverTargetPriorities[key] || {
      under: DEFAULT_TARGET_PRIORITY,
      over: DEFAULT_TARGET_PRIORITY,
    };
    if (priorities.under === DEFAULT_TARGET_PRIORITY && priorities.over === DEFAULT_TARGET_PRIORITY) return [];
    return [[key, { ...priorities }]];
  }));
}

function buildCurrentSolverConfig() {
  return {
    ...buildSolverConfigPayload(solverConfigDefinitions, solverConfigControls),
    target_priorities: serializedTargetPriorities(),
  };
}

function persistCurrentSolverConfig() {
  api.persistPreferences({ solver_config: buildCurrentSolverConfig() });
}

function syncSolverModelControls() {
  const model = solverConfigControls.solver_model?.value || MASS_MODEL;
  const tuningEnabled = model === NNLS_TUNING_MODEL;
  Object.entries(solverConfigControls).forEach(([key, input]) => {
    if (input && key !== "solver_model") input.disabled = !tuningEnabled;
  });
  if (solverMassModelHint) {
    const hintKey = model === HIERARCHICAL_MODEL
      ? "solver.modelHierarchicalHint"
      : model === NNLS_TUNING_MODEL
        ? "solver.modelNnlsTuningHint"
        : "solver.modelMassHint";
    solverMassModelHint.dataset.i18n = hintKey;
    solverMassModelHint.textContent = t(hintKey);
  }
  solverPriorityLegend?.classList.toggle("is-hidden", model !== HIERARCHICAL_MODEL);
}

function applyConfig(config = {}) {
  setTargetPriorities(config.target_priorities, config.ignored_elements);
  applySolverConfig(solverConfigDefinitions, solverConfigControls, config);
  syncSolverModelControls();
  renderSolverTargetsTable();
  renderSolverResults(null);
}

function updateSolverTargetScaleDisplay() {
  if (solverTargetScaleValue) solverTargetScaleValue.textContent = `${solverTargetScaleFactor.toFixed(2)}x`;
}

function applySolverTargetScaleFactor(nextFactor) {
  solverTargetScaleFactor = applyScaledValues(
    solverTargetDefinitions,
    nextFactor,
    (field) => solverTargetBaseValues[field.key],
    (field, value) => { solverTargetValues[field.key] = value; },
  );
  updateSolverTargetScaleDisplay();
  renderSolverTargetsTable();
}

function buildSolvePayload() {
  return createSolvePayload({
    liters: units.liters,
    targetValues: solverTargetValues,
    waterMgPerL: water.buildWaterPayload(),
    osmosisPercent: water.osmosisPercent,
    allowedFertilizers: solverAllowedFertilizers,
    fixedGrams: solverFixedGrams,
    ureaAsNh4: solverUreaToggle.checked,
    solverConfig: buildCurrentSolverConfig(),
  });
}

function renderSolverTargetsTable() {
  const priorityEnabled = solverConfigControls.solver_model?.value === HIERARCHICAL_MODEL;
  solverTargetsTableEl?.classList.toggle("solver-priorities-active", priorityEnabled);
  solverTargetsTableEl
    ?.closest(".solver-comparison-grid")
    ?.classList.toggle("solver-comparison-grid--priorities", priorityEnabled);
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
      renderSolverResults(null);
    });
    input.addEventListener("change", () => {
      normalizeDecimalInputElement(input, solverTargetValues[field.key]);
    });
    valueCell.appendChild(input);

    const reportOnly = REPORT_ONLY_TARGETS.has(field.key);
    const priorities = solverTargetPriorities[field.key] || {
      under: reportOnly ? 0 : DEFAULT_TARGET_PRIORITY,
      over: reportOnly ? 0 : DEFAULT_TARGET_PRIORITY,
    };
    const createPriorityCell = (direction) => {
      const cell = document.createElement("td");
      cell.className = "solver-priority-cell";
      const select = document.createElement("select");
      select.className = "solver-priority-select";
      TARGET_PRIORITY_LEVELS.forEach((priority) => {
        const option = document.createElement("option");
        option.value = String(priority);
        option.textContent = priority === 0
          ? t("solver.priority.reportOnly")
          : t(`solver.priority.level${priority}`);
        select.appendChild(option);
      });
      select.value = String(priorities[direction]);
      select.disabled = reportOnly || !priorityEnabled;
      select.setAttribute(
        "aria-label",
        t(`solver.priority.${direction}Aria`, { element: field.label }),
      );
      select.title = reportOnly
        ? t("solver.reportOnlyHint")
        : priorityEnabled
          ? t(`solver.priority.${direction}Hint`, { element: field.label })
          : t("solver.priority.selectHierarchicalHint");
      select.addEventListener("change", () => {
        solverTargetPriorities[field.key][direction] = normalizedPriority(select.value);
        const current = solverTargetPriorities[field.key];
        row.classList.toggle("solver-target-report-only", current.under === 0 && current.over === 0);
        renderSolverResults(null);
        persistCurrentSolverConfig();
      });
      cell.appendChild(select);
      return cell;
    };
    row.classList.toggle("solver-target-report-only", priorities.under === 0 && priorities.over === 0);

    row.append(labelCell, valueCell, createPriorityCell("under"), createPriorityCell("over"));
    solverTargetsTable.appendChild(row);
  });
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
  if (!isActive()) {
    updateSolverAllowedCount();
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
  return activeFixedAmountCount(solverFixedGrams);
}

function syncSolverOverridePanel({ forceOpen = false } = {}) {
  const activeCount = activeSolverOverrideCount();
  if (solverOverrideSummary) {
    solverOverrideSummary.textContent = t("status.activeCount", { count: activeCount });
  }
  if (solverOverridesDetails && (forceOpen || activeCount > 0)) {
    solverOverridesDetails.open = true;
  }
  onFixedAmountsChange(activeCount);
}

function renderSolverFixedTable() {
  if (!isActive()) {
    return;
  }
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
    input.value = units.formatDoseInput(solverFixedGrams[name] || 0, name);
    input.addEventListener("input", (event) => {
      const canonicalValue = units.displayDoseToCanonical(event.target.value, name);
      if (canonicalValue === null || canonicalValue < 0) {
        return;
      }
      solverFixedGrams[name] = canonicalValue;
      syncSolverOverridePanel({ forceOpen: solverFixedGrams[name] > 0 });
      renderSolverResults(null);
    });
    input.addEventListener("change", () => {
      input.value = units.formatDoseInput(solverFixedGrams[name] || 0, name);
    });
    appendDoseInput(valueCell, input, units.doseUnitDefinition(name).symbol);

    row.append(nameCell, valueCell);
    solverFixedTable.appendChild(row);
  });
  syncSolverOverridePanel();
}

function renderSolverResults(data) {
  if (!data) solveRequests.invalidate();
  lastSolveResult = data || null;
  updateSolverResultActions();
  solverTargetsResultsTableEl?.classList.toggle("is-hidden", !data);
  solverTargetsResultsEmpty?.classList.toggle("is-hidden", Boolean(data));
  if (solverModelUsed) {
    solverModelUsed.textContent = data?.solver_model
      ? `${t("solver.modelLabel")}: ${solverModelLabel(data.solver_model, t)}`
      : "";
  }
  renderSolverTables({
    data,
    fertilizersTable: solverFertilizersTable,
    targetsTable: solverTargetsResultsTable,
    noFertilizersLabel: t("solver.noFertilizersCalculated"),
    formatAmount: (fertilizer) =>
      `${units.formatDoseDisplay(Number(fertilizer.grams), fertilizer.name)} ${units.doseUnitDefinition(fertilizer.name).symbol}`,
    displayKeys: data ? solverResultDisplayKeys(data, summaryColumnOrder) : [],
    labels: {
      N_total: t("solver.nTotal"),
      N_NO3: t("solver.nNo3"),
      N_NH4: t("solver.nNh4"),
      N_UREA: t("solver.nUrea"),
      prioritySummary: (key) => targetPrioritySummary(data, key, t),
    },
    formatNutrient: (value) => formatNumber(value, nutrientFormatter),
  });
}

function solverAutoApplyEnabled() {
  return !solverAutoApplyInput || solverAutoApplyInput.checked;
}

function restoreSolverAutoApplyPreference() {
  if (!solverAutoApplyInput) {
    return;
  }
  const stored = storageGet(SOLVER_AUTO_APPLY_KEY, true);
  solverAutoApplyInput.checked = stored !== false;
}

function persistSolverAutoApplyPreference() {
  if (!solverAutoApplyInput) {
    return;
  }
  storageSet(SOLVER_AUTO_APPLY_KEY, solverAutoApplyInput.checked);
}

function buildSolverClipboardText() {
  const fertilizers = Array.isArray(lastSolveResult?.fertilizers) ? lastSolveResult.fertilizers : [];
  const calculateData = {
    liters: units.liters,
    fertilizers,
    urea_as_nh4: solverUreaToggle.checked,
    water_mg_l: water.buildWaterPayload(),
    osmosis_percent: water.osmosisPercent,
  };

  return api.calculate(calculateData, t("errors.calculateFailed")).then((calculation) =>
    buildSolverPrintableText({
      result: lastSolveResult,
      calculation,
      liters: units.liters,
      osmosisPercent: water.osmosisPercent,
      t,
      units,
    }));
}

async function copySolverResultsToClipboard() {
  if (!lastSolveResult || !Array.isArray(lastSolveResult.fertilizers) || !lastSolveResult.fertilizers.length) {
    notifications.reportError(null, t("solver.noResult"));
    return;
  }

  try {
    const text = await buildSolverClipboardText();
    await notifications.copyText(text);
    notifications.setCopySolverStatus(t("status.copied"));
  } catch (error) {
    notifications.reportError(error, t("errors.copyFailed"));
    notifications.setCopySolverStatus(t("status.copyFailed"));
  }
}

async function solveRecipe() {
  const payload = buildSolvePayload();
  return api.solve(payload, t("errors.solveFailed"));
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
  if (solution && Object.prototype.hasOwnProperty.call(solution, "solver_config")) {
    applyConfig({ ...buildCurrentSolverConfig(), ...solution.solver_config });
  } else {
    renderSolverTargetsTable();
  }
  renderSolverResults(null);
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

function pruneSolverFixedGrams() {
  Object.keys(solverFixedGrams).forEach((key) => {
    if (!solverAllowedFertilizers.includes(key)) {
      delete solverFixedGrams[key];
    }
  });
}

function setSolverFixedGrams(values = {}) {
  Object.keys(solverFixedGrams).forEach((key) => delete solverFixedGrams[key]);
  Object.entries(values).forEach(([name, value]) => {
    const numeric = Number(value);
    if (solverAllowedFertilizers.includes(name) && Number.isFinite(numeric) && numeric > 0) {
      solverFixedGrams[name] = numeric;
    }
  });
  renderSolverFixedTable();
  renderSolverResults(null);
}

function setSolverUreaAsNh4(value) {
  solverUreaToggle.checked = Boolean(value);
  renderSolverResults(null);
}

function missingFertilizers(names = []) {
  const available = new Set(fertilizerOptions.map((fertilizer) => fertilizer.name));
  return names.filter((name) => !available.has(name));
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
  renderSolverResults(null);
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
  storageSet(solverAllowedStorageKey(context), solverAllowedFertilizers);
}

function syncSolverAllowedWithSelection(mode = "merge") {
  const names = getSelectedFertilizers();
  if (!names.length) {
    return false;
  }
  updateSolverAllowedFertilizers(names, mode);
  return true;
}

function restoreSolverAllowedFromStorage(context = solverAllowedContext) {
  const contextKey = solverAllowedStorageKey(context);
  const storedContextAllowed = storageGet(contextKey, null);
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

function setFertilizers(fertilizers) {
  fertilizerOptions = fertilizers || [];
  const available = new Set(fertilizerOptions.map(({ name }) => name));
  updateSolverAllowedFertilizers(
    solverAllowedFertilizers.filter((name) => available.has(name)),
    "replace",
  );
}

function setAllowedContext(context) {
  solverAllowedContext = normalizeSolverAllowedContext(context);
  return restoreSolverAllowedFromStorage(solverAllowedContext);
}

function scaleFixedAmounts(previousLiters, nextLiters) {
  Object.assign(
    solverFixedGrams,
    scaleAmountsByVolume(solverFixedGrams, previousLiters, nextLiters),
  );
  renderSolverFixedTable();
}

function bindConfigEvents() {
  solverConfigDefinitions.forEach((definition) => {
    const input = solverConfigControls[definition.key];
    if (!input || input.dataset.solverBound === "true") return;
    input.dataset.solverBound = "true";
    const eventName = definition.type === "boolean"
      || definition.type === "string"
      || definition.key === "nitrogen_objective_mode"
      ? "change"
      : "input";
    input.addEventListener(eventName, () => {
      if (definition.type !== "boolean"
        && definition.type !== "string"
        && definition.key !== "nitrogen_objective_mode"
        && parseDecimalInput(input.value) === null) return;
      if (definition.key === "solver_model") {
        syncSolverModelControls();
        renderSolverTargetsTable();
      }
      renderSolverResults(null);
      api.persistPreferences({
        solver_config: buildCurrentSolverConfig(),
      });
    });
    if (definition.type !== "boolean"
      && definition.type !== "string"
      && definition.key !== "nitrogen_objective_mode") {
      input.addEventListener("change", () => {
        normalizeDecimalInputElement(input, parseDecimalInput(input.value));
      });
    }
  });
}

function mount({ configDefinitions = [], config = {} } = {}) {
  solverConfigDefinitions = normalizeSolverConfigDefinitions(
    configDefinitions,
    FALLBACK_SOLVER_CONFIG_DEFINITIONS,
    (key) => Boolean(solverConfigControls[key]),
  );
  setTargetPriorities(config.target_priorities, config.ignored_elements);
  applySolverConfig(solverConfigDefinitions, solverConfigControls, config);
  syncSolverModelControls();
  bindConfigEvents();
  if (mounted) return;
  mounted = true;
  restoreSolverAutoApplyPreference();
  renderSolverTargetsTable();
  updateSolverTargetScaleDisplay();
  updateSolverResultActions();
  bindScaleButtons(
    solverTargetScaleDownButton,
    solverTargetScaleUpButton,
    () => solverTargetScaleFactor,
    applySolverTargetScaleFactor,
  );
  solverAllowedSearchInput?.addEventListener("input", (event) => {
    solverAllowedFilter = event.target.value || "";
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = window.setTimeout(renderSolverAllowedOptions, 150);
  });
  solverAllowedFromRecipeButton?.addEventListener("click", () => syncSolverAllowedWithSelection("merge"));
  solverAllowedAllButton?.addEventListener("click", () => {
    updateSolverAllowedFertilizers(fertilizerOptions.map(({ name }) => name), "replace");
  });
  solverAllowedHideInactiveInput?.addEventListener("change", (event) => {
    solverAllowedHideInactive = event.target.checked;
    renderSolverAllowedOptions();
  });
  solverAllowedClearButton?.addEventListener("click", () => updateSolverAllowedFertilizers([], "replace"));
  solverAutoApplyInput?.addEventListener("change", persistSolverAutoApplyPreference);
  solverConfigResetDefaultsButton?.addEventListener("click", () => {
    setTargetPriorities();
    applySolverConfig(solverConfigDefinitions, solverConfigControls);
    syncSolverModelControls();
    renderSolverTargetsTable();
    renderSolverResults(null);
    api.persistPreferences({ solver_config: {} });
    notifications.setSolverApplyStatus(t("solver.configResetDone"));
  });
  solverUreaToggle.addEventListener("change", () => renderSolverResults(null));
  solveButton.addEventListener("click", async () => {
    if (!solverAllowedFertilizers.length) {
      notifications.reportError(null, t("solver.noAllowed"));
      return;
    }
    const version = solveRequests.reserve();
    try {
      const data = await solveRecipe();
      if (!solveRequests.isCurrent(version)) return;
      renderSolverResults(data);
      onSolved(data);
      if (solverAutoApplyEnabled()) onApplyResult({ switchToCalculator: false });
    } catch (error) {
      if (solveRequests.isCurrent(version)) notifications.reportError(error, t("errors.solveFailed"));
    }
  });
  copySolverResultsButton?.addEventListener("click", copySolverResultsToClipboard);
  applySolverToCalculatorInlineButton?.addEventListener("click", () => onApplyResult({ switchToCalculator: true }));
}

function activate() {
  renderSolverAllowedOptions();
  renderSolverFixedTable();
}

function deactivate() {
  solverAllowedFertilizersSelect.replaceChildren();
  solverFixedTable.replaceChildren();
}

function refreshLocalized() {
  renderSolverAllowedOptions();
  renderSolverFixedTable();
  renderSolverTargetsTable();
  renderSolverResults(lastSolveResult);
}

return {
  activate,
  applyConfig,
  applyNutrientSolution,
  buildConfigPayload: buildCurrentSolverConfig,
  deactivate,
  get allowedFertilizers() { return [...solverAllowedFertilizers]; },
  get fixedGrams() { return { ...solverFixedGrams }; },
  get lastResult() { return lastSolveResult; },
  get targets() { return { ...solverTargetValues }; },
  get ureaAsNh4() { return solverUreaToggle.checked; },
  get activeFixedAmountCount() { return activeSolverOverrideCount(); },
  missingFertilizers,
  mount,
  refreshDoseUnits() { renderSolverFixedTable(); if (lastSolveResult) renderSolverResults(lastSolveResult); },
  refreshLocalized,
  renderResults: renderSolverResults,
  resetTargets: resetSolverTargets,
  restoreAllowed: restoreSolverAllowedFromStorage,
  scaleFixedAmounts,
  setAllowedContext,
  setAllowedFertilizers: updateSolverAllowedFertilizers,
  setFixedGrams: setSolverFixedGrams,
  setFertilizers,
  setUreaAsNh4: setSolverUreaAsNh4,
};
}
