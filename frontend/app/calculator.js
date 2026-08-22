import {
  ION_FORMATTER,
  LAST_SOLUTION_CALCULATED_KEY,
  NUTRIENT_FORMATTER,
  SUMMARY_COLUMN_ORDER,
} from "./constants.js";
import {
  appendDoseInput,
  createSearchableCombobox,
  createTable,
  qs,
  qsa,
  renderTableRows,
} from "./dom.js";
import { buildAlignedRows, formatNumber, roundScaledValue } from "./formatting.js";
import { applyScaledValues, bindScaleButtons } from "./scaling.js";
import { createLatestRequestGate } from "../request_gate.js";
import { storageSet } from "./storage.js";

export function createCalculatorController({
  api, i18n, notifications, units, water, getSolverResult, getSolverAllowed,
  getSolverUrea, onCalculation, onShowCalculator,
}) {
const fertilizerSelectTableWrap = qs("#fertilizerSelectTableWrap");
const calculatorTableWrap = qs("#calculatorTableWrap");
const calculateButton = qs("#calculateBtn");
const copyCalculatorResultsButton = qs("#copyCalculatorResults");
const addRowButton = qs("#addFertilizerRow");
const removeRowButton = qs("#removeFertilizerRow");
const calculatorScaleDownButton = qs("#calculatorScaleDown");
const calculatorScaleUpButton = qs("#calculatorScaleUp");
const calculatorScaleValue = qs("#calculatorScaleValue");
const t = (key, params) => i18n.t(key, params);
const nutrientFormatter = NUTRIENT_FORMATTER;
const ionFormatter = ION_FORMATTER;
const summaryColumnOrder = SUMMARY_COLUMN_ORDER;
const calculationRequests = createLatestRequestGate();
let fertilizerOptions = [];
let calculatorRows = [createCalculatorRow()];
let calculatorSelectedIndex = 0;
let calculatorScaleFactor = 1;
let lastCalculation = null;
let calculatorResultCurrent = false;
let recalculateTimer;
let fertilizerSelectTable;
let calculatorTable;
let fertilizerComboboxes = [];
let mounted = false;

const setCalculatorResultCurrent = (current) => {
  calculatorResultCurrent = Boolean(current && lastCalculation);
  notifications.setCalculatorResultCurrent(calculatorResultCurrent);
};

function createCalculatorRow(name = "", grams = 0) {
  const normalizedGrams = Math.max(0, Number(grams) || 0);
  return {
    name,
    grams: normalizedGrams,
    baseGrams: roundScaledValue(normalizedGrams),
  };
}

function updateCalculatorScaleDisplay() {
  if (calculatorScaleValue) {
    calculatorScaleValue.textContent = `${calculatorScaleFactor.toFixed(2)}x`;
  }
}

function applyCalculatorScaleFactor(nextFactor) {
  calculatorScaleFactor = applyScaledValues(
    calculatorRows,
    nextFactor,
    (row) => row.baseGrams,
    (row, value) => {
      row.grams = value;
    },
  );
  updateCalculatorScaleDisplay();
  renderCalculatorTable();
  scheduleRecalculate();
}

function applySolverResultToCalculator({ switchToCalculator = false } = {}) {
  const lastSolveResult = getSolverResult();
  if (!lastSolveResult) {
    notifications.reportError(null, t("solver.noResult"));
    return false;
  }
  const fertilizers = (lastSolveResult.fertilizers || []).map((fert) => ({
    name: fert.name,
    grams: Number(fert.grams || 0),
  }));
  const recipe = {
    liters: units.liters,
    fertilizers,
  };
  applyRecipe(recipe);
  scheduleRecalculate();
  notifications.setSolverApplyStatus(t("status.appliedCalculator"));

  if (switchToCalculator) {
    onShowCalculator();
  }
  return true;
}

function buildCalculatorClipboardText() {
  const fertilizers = buildSelectedFertilizerEntries();
  const lines = [t("calculator.clipboardTitle")];
  lines.push(
    ...buildAlignedRows(null, [
      [
        t("solver.clipboardBatchVolume", { unit: units.getVolumeUnitDefinition().symbol }),
        units.formatVolumeValue(units.litersToDisplayVolume(units.liters)),
      ],
      [t("solver.clipboardOsmosis"), formatNumber(water.osmosisPercent)],
    ], [1])
  );
  lines.push("");
  lines.push(
    ...buildAlignedRows(
      [t("common.fertilizer"), t("common.amount"), t("common.unit")],
      fertilizers.map((fertilizer) => [
        fertilizer.name,
        units.formatDoseDisplay(fertilizer.grams, fertilizer.name),
        units.doseUnitDefinition(fertilizer.name).symbol,
      ]),
      [1]
    )
  );

  const npkMetrics = lastCalculation?.npk_metrics || {};
  lines.push("");
  lines.push(t("solver.clipboardNpk"));
  lines.push(
    ...buildAlignedRows(null, [
      [t("live.npkTotal"), npkMetrics.npk_all_pct || "-"],
      [t("live.npkPNorm"), npkMetrics.npk_p_norm || "-"],
      [t("live.npkRatio"), npkMetrics.npk_npk_pct || "-"],
    ], [1])
  );

  const solutionEc = lastCalculation?.ec?.ec_mS_per_cm || {};
  const waterEc = lastCalculation?.ec_water?.ec_mS_per_cm || {};
  lines.push("");
  lines.push(t("live.ec"));
  lines.push(
    ...buildAlignedRows(null, [
      [`${t("live.solution")} 25°C`, formatNumber(Number(solutionEc["25.0"]))],
      [`${t("live.solution")} 18°C`, formatNumber(Number(solutionEc["18.0"]))],
      [`${t("live.water")} 25°C`, formatNumber(Number(waterEc["25.0"]))],
      [`${t("live.water")} 18°C`, formatNumber(Number(waterEc["18.0"]))],
    ], [1])
  );

  const elementValues = lastCalculation?.elements_mg_per_l || {};
  lines.push("");
  lines.push(t("solver.clipboardIons"));
  lines.push(
    ...buildAlignedRows(
      null,
      summaryColumnOrder.map((column) => [
        t(column.ionHeaderLabelKey || column.ionHeaderLabel),
        formatNumber(Number(elementValues[column.element]), nutrientFormatter),
      ]),
      [1]
    )
  );

  const oxideValues = lastCalculation?.oxides_mg_per_l || {};
  lines.push("");
  lines.push(`${t("calculator.oxideForms")} (mg/L)`);
  lines.push(
    ...buildAlignedRows(
      null,
      summaryColumnOrder.map((column) => [
        t(column.oxideHeaderLabelKey || column.oxideHeaderLabel),
        water.formatOxideValue(column.oxide, Number(oxideValues[column.oxide])),
      ]),
      [1]
    )
  );

  const ionValues = lastCalculation?.ions_meq_per_l || {};
  lines.push("");
  lines.push(`${t("calculator.ions")} (meq/L)`);
  lines.push(
    ...buildAlignedRows(
      null,
      Object.entries(ionValues)
        .filter(([, value]) => Number.isFinite(Number(value)))
        .map(([key, value]) => [key, formatNumber(Number(value), ionFormatter)]),
      [1]
    )
  );

  const balance = lastCalculation?.ion_balance || {};
  const rawCbe = Number(balance.raw_cbe_percent_signed ?? balance.error_percent_signed);
  const dinCbe = Number.isFinite(Number(balance.din_38402_62_percent_signed))
    ? Number(balance.din_38402_62_percent_signed)
    : rawCbe * 2;
  lines.push("");
  lines.push(t("calculator.ionBalance"));
  lines.push(
    ...buildAlignedRows(
      [t("common.parameter"), t("common.value"), t("common.unit")],
      [
        [t("calculator.ionBalance.cations"), formatNumber(Number(balance.cations_meq_per_l), ionFormatter), "meq/L"],
        [t("calculator.ionBalance.anions"), formatNumber(Number(balance.anions_meq_per_l), ionFormatter), "meq/L"],
        [t("calculator.ionBalance.cbeRaw"), formatNumber(rawCbe, ionFormatter), "%"],
        [t("calculator.ionBalance.dinRaw"), formatNumber(dinCbe, ionFormatter), "%"],
      ],
      [1]
    )
  );

  return lines.join("\n");
}

function destroyFertilizerComboboxes() {
  fertilizerComboboxes.forEach((combobox) => combobox.destroy());
  fertilizerComboboxes = [];
}

function syncSelectedCalculatorRows() {
  qsa("#fertilizerSelectTable tbody tr, #calculatorTable tbody tr").forEach((row) => {
    const selected = Number(row.dataset.calculatorIndex) === calculatorSelectedIndex;
    row.classList.toggle("is-selected", selected);
    row.setAttribute("aria-selected", selected ? "true" : "false");
  });
}

function setSelectedCalculatorRow(index) {
  calculatorSelectedIndex = Math.min(Math.max(0, index), calculatorRows.length - 1);
  syncSelectedCalculatorRows();
}

function prepareSelectableCalculatorRow(row, index) {
  row.dataset.calculatorIndex = String(index);
  row.addEventListener("pointerdown", () => setSelectedCalculatorRow(index));
  row.addEventListener("focusin", () => setSelectedCalculatorRow(index));
  const selected = index === calculatorSelectedIndex;
  row.classList.toggle("is-selected", selected);
  row.setAttribute("aria-selected", selected ? "true" : "false");
}

async function copyCalculatorResultsToClipboard() {
  if (!lastCalculation || !calculatorResultCurrent) {
    notifications.reportError(null, t("calculator.noResult"));
    return;
  }

  try {
    await notifications.copyText(buildCalculatorClipboardText());
    notifications.setCopyCalculatorStatus(t("status.copied"));
  } catch (error) {
    notifications.reportError(error, t("errors.copyFailed"));
    notifications.setCopyCalculatorStatus(t("status.copyFailed"));
  }
}

function renderSelectionTable() {
  destroyFertilizerComboboxes();
  renderTableRows(fertilizerSelectTable, calculatorRows.length, (i) => {
    const calculatorRow = calculatorRows[i];
    const row = document.createElement("tr");
    prepareSelectableCalculatorRow(row, i);

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const selectCell = document.createElement("td");
    const combobox = createSearchableCombobox({
      id: `fertilizer-select-${i}`,
      options: fertilizerOptions,
      value: calculatorRow.name,
      onCommit: (value) => {
        if (calculatorRow.name === value) return;
        calculatorRow.name = value;
        renderSelectionTable();
        renderCalculatorTable();
        scheduleRecalculate();
      },
      accessibleLabel: t("aria.searchFertilizerRow", { row: i + 1 }),
      emptyLabel: t("common.selectEmpty"),
      noResultsLabel: t("calculator.noFertilizersFound"),
      placeholder: t("calculator.fertilizerSearchPlaceholder"),
    });
    fertilizerComboboxes.push(combobox);
    selectCell.appendChild(combobox.element);

    const selectedOption = fertilizerOptions.find((option) => option.name === calculatorRow.name);

    const liquidCell = document.createElement("td");
    liquidCell.textContent = calculatorRow.name
      ? selectedOption?.liquid
        ? t("common.liquid")
        : t("common.solid")
      : "-";

    const weightCell = document.createElement("td");
    if (!selectedOption) {
      weightCell.textContent = "-";
    } else if (selectedOption.liquid) {
      weightCell.textContent = `${formatNumber(selectedOption.weight_factor, nutrientFormatter)} g/mL`;
    } else if (Number(selectedOption.weight_factor) !== 1) {
      weightCell.textContent = `${formatNumber(selectedOption.weight_factor, nutrientFormatter)}×`;
    } else {
      weightCell.textContent = "—";
    }

    row.append(indexCell, selectCell, liquidCell, weightCell);
    return row;
  });
}

function renderCalculatorTable() {
  renderTableRows(calculatorTable, calculatorRows.length, (i) => {
    const calculatorRow = calculatorRows[i];
    const row = document.createElement("tr");
    prepareSelectableCalculatorRow(row, i);
    if (calculatorRow.baseGrams === undefined) {
      const currentAmount = Math.max(0, Number(calculatorRow.grams) || 0);
      calculatorRow.baseGrams =
        calculatorScaleFactor > 0 ? roundScaledValue(currentAmount / calculatorScaleFactor) : 0;
    }

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const nameCell = document.createElement("td");
    nameCell.textContent = calculatorRow.name || "-";
    nameCell.colSpan = 2;

    const amountCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.min = "0";
    input.step = "any";
    input.value = units.formatDoseInput(calculatorRow.grams, calculatorRow.name);
    input.addEventListener("input", (event) => {
      const canonicalValue = units.displayDoseToCanonical(event.target.value, calculatorRow.name);
      if (canonicalValue === null || canonicalValue < 0) {
        return;
      }
      calculatorRow.grams = canonicalValue;
      calculatorRow.baseGrams =
        calculatorScaleFactor > 0 ? roundScaledValue(canonicalValue / calculatorScaleFactor) : 0;
      scheduleRecalculate();
    });
    input.addEventListener("change", () => {
      input.value = units.formatDoseInput(calculatorRow.grams, calculatorRow.name);
    });
    appendDoseInput(amountCell, input, units.doseUnitDefinition(calculatorRow.name).symbol);

    row.append(indexCell, nameCell, amountCell);
    return row;
  });
}

function scheduleRecalculate() {
  const requestVersion = calculationRequests.reserve();
  setCalculatorResultCurrent(false);
  if (recalculateTimer) {
    clearTimeout(recalculateTimer);
  }
  recalculateTimer = setTimeout(async () => {
    try {
      await calculateAndRender(null, requestVersion);
    } catch (error) {
      notifications.reportError(error, t("errors.calculateFailed"));
    }
  }, 250);
}

function buildPayload() {
  return {
    liters: units.liters,
    fertilizers: buildSelectedFertilizerEntries(),
    water_mg_l: water.buildWaterPayload(),
    osmosis_percent: water.osmosisPercent,
  };
}

async function calculateAndRender(payloadOverride = null, requestVersion = null) {
  const activeVersion = requestVersion ?? calculationRequests.reserve();
  if (!calculationRequests.isCurrent(activeVersion)) return null;
  setCalculatorResultCurrent(false);
  const data = await api.calculate(payloadOverride || buildPayload(), t("errors.calculateFailed"));
  if (!calculationRequests.isCurrent(activeVersion)) return null;
  renderCalculation(data);
  return data;
}


function buildSelectedFertilizerEntries({ allowZeroGrams = false } = {}) {
  return calculatorRows
    .map((row) => ({
      name: row.name,
      grams: Number(row.grams) || 0,
    }))
    .filter((entry) => entry.name && (allowZeroGrams || entry.grams > 0));
}

function renderCalculation(data, { resultCurrent = true } = {}) {
  lastCalculation = data;
  water.renderCalculation(data);
  onCalculation(data);
  setCalculatorResultCurrent(resultCurrent);
}

function applyRecipe(recipe, { applyLiters = true } = {}) {
  if (applyLiters && recipe && recipe.liters !== undefined && recipe.liters !== null) {
    units.setLiters(recipe.liters, { scaleBatch: false, recalculate: false, invalidateSolver: false });
  }
  const fertilizers = Array.isArray(recipe.fertilizers) ? recipe.fertilizers : [];
  calculatorRows.length = 0;
  calculatorScaleFactor = 1.0;

  fertilizers.forEach((entry) => {
    const name = entry.name || "";
    const grams = Math.max(0, Number(entry.grams) || 0);
    calculatorRows.push(createCalculatorRow(name, grams));
  });

  if (!calculatorRows.length) {
    calculatorRows.push(createCalculatorRow());
  }
  calculatorSelectedIndex = 0;

  updateCalculatorScaleDisplay();
  renderSelectionTable();
  renderCalculatorTable();
}

function collectSelectedFertilizerNames() {
  const names = calculatorRows.map((row) => row.name).filter(Boolean);
  return Array.from(new Set(names));
}

function addFertilizerRow() {
  calculatorRows.push(createCalculatorRow());
  calculatorSelectedIndex = calculatorRows.length - 1;
  renderSelectionTable();
  renderCalculatorTable();
}

function removeFertilizerRow() {
  if (calculatorRows.length <= 1) {
    return;
  }

  const [removedRow] = calculatorRows.splice(calculatorSelectedIndex, 1);
  calculatorSelectedIndex = Math.min(calculatorSelectedIndex, calculatorRows.length - 1);
  renderSelectionTable();
  renderCalculatorTable();
  if (removedRow.name || removedRow.grams > 0) scheduleRecalculate();
}

function buildRecipePayloadFromSelection(name) {
  const fertilizers = buildSelectedFertilizerEntries();
  return buildRecipePayload(name, fertilizers, false);
}

function buildRecipePayloadFromSolver(name) {
  const lastSolveResult = getSolverResult();
  const fertilizers = Array.isArray(lastSolveResult?.fertilizers) ? lastSolveResult.fertilizers : [];
  return buildRecipePayload(name, fertilizers, getSolverUrea());
}

function buildRecipePayload(name, fertilizers, ureaAsNh4) {
  const payload = {
    name,
    liters: units.liters,
    fertilizers,
    fertilizers_allowed: getSolverAllowed(),
    urea_as_nh4: ureaAsNh4,
  };
  if (water.selectedProfile) payload.water_profile = water.selectedProfile.replace(/\.yml$/, "");
  if (Number.isFinite(water.osmosisPercent)) payload.osmosis_percent = water.osmosisPercent;
  return payload;
}

function buildSolutionSnapshot() {
  const fertilizers = buildSelectedFertilizerEntries({ allowZeroGrams: true });
  return {
    ...water.getSnapshot(),
    liters: units.liters,
    fertilizers,
  };
}

function initializeTables() {
  destroyFertilizerComboboxes();
  const selectTable = createTable({
    id: "fertilizerSelectTable",
    className: "grid grid--form grid--fertilizer",
    colgroupClasses: ["col-index", "col-name", "col-liquid", "col-weight"],
    headerCells: [
      { label: "#" },
      { labelKey: "calculator.fertilizerDropdown", label: t("calculator.fertilizerDropdown") },
      { labelKey: "common.productType", label: t("common.productType") },
      { labelKey: "editor.densityFactor", label: t("editor.densityFactor") },
    ],
  });
  fertilizerSelectTableWrap.replaceChildren(selectTable.table);
  fertilizerSelectTable = selectTable.tbody;
  const calculator = createTable({
    id: "calculatorTable",
    className: "grid grid--form grid--fertilizer",
    colgroupClasses: ["col-index", "col-name", "col-form", "col-amount"],
    headerCells: [
      { label: "#" },
      { labelKey: "editor.fertilizerName", label: t("editor.fertilizerName"), colSpan: 2 },
      { labelKey: "common.amount", label: t("common.amount") },
    ],
  });
  calculatorTableWrap.replaceChildren(calculator.table);
  calculatorTable = calculator.tbody;
}

function scaleBatch(previousLiters, nextLiters) {
  const factor = nextLiters / previousLiters;
  calculatorRows.forEach((row) => {
    const scaled = roundScaledValue((Number(row.grams) || 0) * factor);
    row.grams = scaled;
    row.baseGrams = calculatorScaleFactor > 0
      ? roundScaledValue(scaled / calculatorScaleFactor)
      : scaled;
  });
  renderCalculatorTable();
}

function setFertilizers(fertilizers) {
  fertilizerOptions = fertilizers || [];
  const available = new Set(fertilizerOptions.map(({ name }) => name));
  calculatorRows.forEach((row, index) => {
    if (row.name && !available.has(row.name)) calculatorRows[index] = createCalculatorRow();
  });
  if (!calculatorRows.length) calculatorRows.push(createCalculatorRow());
  calculatorSelectedIndex = Math.min(calculatorSelectedIndex, calculatorRows.length - 1);
  units.setFertilizers(fertilizerOptions);
  if (fertilizerSelectTable) renderSelectionTable();
  if (calculatorTable) renderCalculatorTable();
}

function mount() {
  if (mounted) return;
  mounted = true;
  initializeTables();
  addRowButton.addEventListener("click", addFertilizerRow);
  removeRowButton.addEventListener("click", removeFertilizerRow);
  calculateButton.addEventListener("click", async () => {
    try {
      await calculateAndRender();
      storageSet(LAST_SOLUTION_CALCULATED_KEY, buildSolutionSnapshot());
    } catch (error) {
      notifications.reportError(error, t("errors.calculateFailed"));
    }
  });
  copyCalculatorResultsButton?.addEventListener("click", copyCalculatorResultsToClipboard);
  bindScaleButtons(
    calculatorScaleDownButton,
    calculatorScaleUpButton,
    () => calculatorScaleFactor,
    applyCalculatorScaleFactor,
  );
  renderSelectionTable();
  renderCalculatorTable();
}

function refreshLocalized() {
  initializeTables();
  renderSelectionTable();
  renderCalculatorTable();
  if (lastCalculation) renderCalculation(lastCalculation, { resultCurrent: calculatorResultCurrent });
  else water.renderEmptyCalculation();
}

return {
  applyRecipe,
  applySolverResult: applySolverResultToCalculator,
  buildRecipePayloadFromSelection,
  buildRecipePayloadFromSolver,
  buildSolutionSnapshot,
  calculateAndRender,
  collectSelectedFertilizerNames,
  get lastCalculation() { return lastCalculation; },
  get resultCurrent() { return calculatorResultCurrent; },
  mount,
  refreshDoseUnits() { renderSelectionTable(); renderCalculatorTable(); },
  refreshLocalized,
  render: renderCalculation,
  scaleBatch,
  scheduleRecalculate,
  setFertilizers,
};
}
