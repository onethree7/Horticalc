import {
  FALLBACK_SOLVER_CONFIG_DEFINITIONS,
  LAST_FERTILIZERS_ALLOWED_CONTEXT_KEY_PREFIX,
  NUTRIENT_FORMATTER,
  SOLVER_AUTO_APPLY_KEY,
  SUMMARY_COLUMN_ORDER,
} from "./constants.js";
import { qs } from "./dom.js";
import {
  buildAlignedRows,
  decimalInputValue,
  formatNumber,
  normalizeDecimalInputElement,
  parseDecimalInput,
  roundScaledValue,
} from "./formatting.js";
import { bindScaleButtons, scaledValues } from "./scaling.js";
import { storageGet, storageSet } from "./storage.js";
import { createLatestRequestGate } from "../request_gate.js";

export function createSolverController({
  api, i18n, notifications, units, water, getSelectedFertilizers,
  onApplyResult, isActive,
}) {
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
const solverAutoApplyInput = qs("#solverAutoApply");
const applySolverToCalculatorInlineButton = qs("#applySolverToCalculatorInline");
const saveSolverAsRecipeButton = qs("#saveSolverAsRecipe");
const applySolverToCalculatorButton = qs("#applySolverToCalculator");
const solverUreaToggle = qs("#solverUreaToggle");
const solverConfigResetDefaultsButton = qs("#solverConfigResetDefaults");
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
const solverTargetDefinitions = [
  "N_total", "N_NH4", "N_NO3", "N_UREA", "P", "K", "Ca", "Mg", "S",
  "Fe", "Mn", "Cu", "Zn", "B", "Mo", "Si", "Cl", "Na", "HCO3",
].map((key) => ({ key, label: key }));
const solverTargetValues = Object.fromEntries(solverTargetDefinitions.map(({ key }) => [key, 0]));
const solverTargetBaseValues = { ...solverTargetValues };
const solverAllowedFertilizers = [];
const solverFixedGrams = {};
const solveRequests = createLatestRequestGate();
const t = (key, params) => i18n.t(key, params);
const nutrientFormatter = NUTRIENT_FORMATTER;
const summaryColumnOrder = SUMMARY_COLUMN_ORDER;
const NITROGEN_OBJECTIVE_TOTAL_ONLY = "n_total_only";
const NITROGEN_OBJECTIVE_FORMS_ONLY = "n_forms_only";
let solverConfigDefinitions = [...FALLBACK_SOLVER_CONFIG_DEFINITIONS];
let fertilizerOptions = [];
let lastSolveResult = null;
let solverTargetScaleFactor = 1;
let solverAllowedContext = "global";
let solverAllowedFilter = "";
let solverAllowedHideInactive = false;
let searchTimer;
let mounted = false;

const buildClipboardRows = buildAlignedRows;
const formatClipboardIonLabel = (key) => key === "N_total" ? "N" : key;
const formatDoseInput = (...args) => units.formatDoseInput(...args);
const formatDoseDisplay = (...args) => units.formatDoseDisplay(...args);
const displayDoseToCanonical = (...args) => units.displayDoseToCanonical(...args);
const doseUnitDefinition = (...args) => units.doseUnitDefinition(...args);
const getVolumeUnitDefinition = (...args) => units.getVolumeUnitDefinition(...args);
const litersToDisplayVolume = (...args) => units.litersToDisplayVolume(...args);
const formatVolumeValue = (...args) => units.formatVolumeValue(...args);
const appendDoseInput = (cell, input, fertilizer) => {
  const wrapper = document.createElement("span");
  wrapper.className = "dose-input";
  const unit = document.createElement("span");
  unit.className = "dose-input-unit";
  unit.textContent = doseUnitDefinition(fertilizer).symbol;
  wrapper.append(input, unit);
  cell.appendChild(wrapper);
};
const reportError = (...args) => notifications.reportError(...args);
const copyTextWithFallback = (...args) => notifications.copyText(...args);
const setCopySolverStatus = (...args) => notifications.setCopySolverStatus(...args);

function updateSolverTargetScaleDisplay() {
  if (solverTargetScaleValue) solverTargetScaleValue.textContent = `${solverTargetScaleFactor.toFixed(2)}x`;
}

function applySolverTargetScaleFactor(nextFactor) {
  const scaled = scaledValues(solverTargetDefinitions, nextFactor, (field) => solverTargetBaseValues[field.key]);
  solverTargetScaleFactor = scaled.factor;
  solverTargetDefinitions.forEach((field, index) => { solverTargetValues[field.key] = scaled.values[index]; });
  updateSolverTargetScaleDisplay();
  renderSolverTargetsTable();
}

function buildSolvePayload() {
  const targets = Object.fromEntries(Object.entries(solverTargetValues).filter(([, value]) => Number(value) > 0));
  const fixed = Object.fromEntries(Object.entries(solverFixedGrams).filter(([, value]) => Number(value) > 0));
  return {
    liters: units.liters,
    targets,
    water_profile: { mg_per_l: water.buildWaterPayload(), osmosis_percent: water.osmosisPercent },
    fertilizers_allowed: solverAllowedFertilizers,
    fixed_grams: fixed,
    urea_as_nh4: solverUreaToggle.checked,
    solver_config: buildSolverConfigPayload(),
  };
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
      renderSolverResults(null);
    });
    input.addEventListener("change", () => {
      normalizeDecimalInputElement(input, solverTargetValues[field.key]);
    });
    valueCell.appendChild(input);

    row.append(labelCell, valueCell);
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
    input.value = formatDoseInput(solverFixedGrams[name] || 0, name);
    input.addEventListener("input", (event) => {
      const canonicalValue = displayDoseToCanonical(event.target.value, name);
      if (canonicalValue === null || canonicalValue < 0) {
        return;
      }
      solverFixedGrams[name] = canonicalValue;
      syncSolverOverridePanel({ forceOpen: solverFixedGrams[name] > 0 });
      renderSolverResults(null);
    });
    input.addEventListener("change", () => {
      input.value = formatDoseInput(solverFixedGrams[name] || 0, name);
    });
    appendDoseInput(valueCell, input, name);

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
  if (!data) {
    solveRequests.invalidate();
  }
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
      const amountCell = document.createElement("td");
      amountCell.textContent = `${formatDoseDisplay(Number(fert.grams), fert.name)} ${doseUnitDefinition(fert.name).symbol}`;
      row.append(nameCell, amountCell);
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
    N_total: t("solver.nTotal"),
    N_NO3: t("solver.nNo3"),
    N_NH4: t("solver.nNh4"),
    N_UREA: t("solver.nUrea"),
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
  const lines = [t("solver.clipboardTitle")];
  lines.push(
    ...buildClipboardRows(null, [
      [
        t("solver.clipboardBatchVolume", { unit: getVolumeUnitDefinition().symbol }),
        formatVolumeValue(litersToDisplayVolume(units.liters)),
      ],
      [t("solver.clipboardOsmosis"), formatNumber(water.osmosisPercent)],
    ], [1])
  );
  lines.push("");
  lines.push(
    ...buildClipboardRows(
      [t("common.fertilizer"), t("common.amount"), t("common.unit")],
      fertilizers.map((fert) => [
        fert.name || "",
        formatDoseDisplay(Number(fert.grams), fert.name),
        doseUnitDefinition(fert.name).symbol,
      ]),
      [1]
    )
  );

  const calculateData = {
    liters: units.liters,
    fertilizers,
    water_mg_l: water.buildWaterPayload(),
    osmosis_percent: water.osmosisPercent,
  };

  return api.calculate(calculateData, t("errors.calculateFailed")).then((data) => {
    const npkMetrics = data?.npk_metrics || {};
    const ecValues = data?.ec?.ec_mS_per_cm || {};
    const ionValues = data?.elements_mg_per_l || {};

    lines.push("");
    lines.push(t("solver.clipboardNpk"));
    lines.push(
      ...buildClipboardRows(null, [
        [t("live.npkTotal"), npkMetrics.npk_all_pct || "-"],
        [t("live.npkPNorm"), npkMetrics.npk_p_norm || "-"],
        [t("live.npkRatio"), npkMetrics.npk_npk_pct || "-"],
      ], [1])
    );

    lines.push("");
    lines.push(t("live.ec"));
    lines.push(
      ...buildClipboardRows(null, [
        [t("common.ec") + " 25°C", formatNumber(Number(ecValues["25.0"]))],
        [t("common.ec") + " 18°C", formatNumber(Number(ecValues["18.0"]))],
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
  const factor = nextLiters / previousLiters;
  Object.keys(solverFixedGrams).forEach((key) => {
    solverFixedGrams[key] = roundScaledValue((Number(solverFixedGrams[key]) || 0) * factor);
  });
  renderSolverFixedTable();
}

function bindConfigEvents() {
  solverConfigDefinitions.forEach((definition) => {
    const input = solverConfigControls[definition.key];
    if (!input || input.dataset.solverBound === "true") return;
    input.dataset.solverBound = "true";
    const eventName = definition.type === "boolean" || definition.key === "nitrogen_objective_mode"
      ? "change"
      : "input";
    input.addEventListener(eventName, () => {
      if (definition.type !== "boolean"
        && definition.key !== "nitrogen_objective_mode"
        && parseDecimalInput(input.value) === null) return;
      renderSolverResults(null);
      api.persistPreferences({ solver_config: buildSolverConfigPayload() });
    });
    if (definition.type !== "boolean" && definition.key !== "nitrogen_objective_mode") {
      input.addEventListener("change", () => {
        normalizeDecimalInputElement(input, parseDecimalInput(input.value));
      });
    }
  });
}

function mount({ configDefinitions = [], config = {} } = {}) {
  solverConfigDefinitions = normalizeSolverConfigDefinitions(configDefinitions);
  applySolverConfig(config);
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
    applySolverConfig();
    renderSolverResults(null);
    api.persistPreferences({ solver_config: {} });
    notifications.setSolverApplyStatus(t("solver.configResetDone"));
  });
  solverUreaToggle.addEventListener("change", () => renderSolverResults(null));
  solveButton.addEventListener("click", async () => {
    if (!solverAllowedFertilizers.length) {
      reportError(null, t("solver.noAllowed"));
      return;
    }
    const version = solveRequests.reserve();
    try {
      const data = await solveRecipe();
      if (!solveRequests.isCurrent(version)) return;
      renderSolverResults(data);
      if (solverAutoApplyEnabled()) onApplyResult({ switchToCalculator: false });
    } catch (error) {
      if (solveRequests.isCurrent(version)) reportError(error, t("errors.solveFailed"));
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
  applyConfig: applySolverConfig,
  applyNutrientSolution,
  buildConfigPayload: buildSolverConfigPayload,
  deactivate,
  get allowedFertilizers() { return [...solverAllowedFertilizers]; },
  get lastResult() { return lastSolveResult; },
  get targets() { return { ...solverTargetValues }; },
  get ureaAsNh4() { return solverUreaToggle.checked; },
  mount,
  refreshDoseUnits() { renderSolverFixedTable(); if (lastSolveResult) renderSolverResults(lastSolveResult); },
  refreshLocalized,
  renderResults: renderSolverResults,
  resetTargets: resetSolverTargets,
  restoreAllowed: restoreSolverAllowedFromStorage,
  scaleFixedAmounts,
  setAllowedContext,
  setAllowedFertilizers: updateSolverAllowedFertilizers,
  setFertilizers,
};
}
