import {
  ION_NITROGEN_EXPANDED_KEY,
  ION_FORMATTER,
  NUTRIENT_FORMATTER,
  NUTRIENT_INTEGER_FORMATTER,
  SUMMARY_COLUMN_ORDER,
  SUMMARY_VIEW_KEY,
} from "./constants.js";
import { qs, qsa, syncSelectedOptionTitle } from "./dom.js";
import { decimalInputValue, formatNumber } from "./formatting.js";
import { createLatestRequestGate } from "../request_gate.js";
import { storageGet, storageSet } from "./storage.js";

export function createWaterController({ api, i18n, notifications, onChange }) {
  const waterTableBody = qs("#waterValuesTable tbody");
  const waterProfileSelect = qs("#waterProfileSelect");
  const waterProfileNameInput = qs("#waterProfileName");
  const loadWaterProfileButton = qs("#loadWaterProfile");
  const saveWaterProfileButton = qs("#saveWaterProfile");
  const resetWaterProfileButton = qs("#resetWaterProfile");
  const osmosisPercentInput = qs("#osmosisPercent");
  const waterUnitToggle = qs("#waterUnitToggle");
  const waterSummaryTable = qs("#waterSummaryTable");
  const oxideSummaryTable = qs("#oxideSummaryTable");
  const ionSummaryTable = qs("#ionSummaryTable");
  const waterSummaryBadge = qs("#waterSummaryBadge");
  const oxideSummaryBadge = qs("#oxideSummaryBadge");
  const ionSummaryBadge = qs("#ionSummaryBadge");
  const summaryViewToggle = qs("#summaryViewToggle");
  const summaryPanels = qsa(".summary-panel[data-summary-panel]");
  const ionMeqList = qs("#ionMeqList");
  const ionBalanceList = qs("#ionBalanceList");
  const npkAllPctValue = qs("#npkAllPct");
  const npkPNormValue = qs("#npkPNorm");
  const npkNpkPctValue = qs("#npkNpkPct");
  const caMgRatioValue = qs("#caMgRatio");
  const ionRatioList = qs("#ionRatioList");
  const ec18Value = qs("#ec18Value");
  const ec25Value = qs("#ec25Value");
  const ecWater18Value = qs("#ecWater18Value");
  const ecWater25Value = qs("#ecWater25Value");
  const nutrientFormatter = NUTRIENT_FORMATTER;
  const nutrientIntegerFormatter = NUTRIENT_INTEGER_FORMATTER;
  const ionFormatter = ION_FORMATTER;
  const summaryColumnOrder = SUMMARY_COLUMN_ORDER;
  const summaryLabelWidth = "12rem";
  const nutrientIntegerKeys = new Set(["N_total", "P", "K", "Ca", "Mg", "S"]);
  const nutrientTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "Si"]);
  const oxideIntegerKeys = new Set(["N_total", "P2O5", "K2O", "CaO", "MgO", "SO4"]);
  const oxideTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "SiO2"]);
  const carbonateHelperKeys = new Set(["CO3", "CaCO3", "KH"]);
  const waterHelperKeys = new Set(["S", ...carbonateHelperKeys]);
  const waterFieldDefinitions = [
    ["NH4", "waterField.NH4", "Ammonium as NH4"], ["NO3", "waterField.NO3", "Nitrate as NO3"],
    ["PO4", "waterField.PO4", "Phosphate as PO4"], ["P", "waterField.P", "Phosphorus as P"],
    ["K", "waterField.K", "Potassium as K"], ["Ca", "waterField.Ca", "Calcium as Ca"],
    ["Mg", "waterField.Mg", "Magnesium as Mg"], ["Na", "waterField.Na", "Sodium as Na"],
    ["SO4", "waterField.SO4", "Sulfate as SO4"], ["S", "waterField.S", "Sulfur as S"],
    ["Fe", "waterField.Fe", "Iron as Fe"], ["Mn", "waterField.Mn", "Manganese as Mn"],
    ["Cu", "waterField.Cu", "Copper as Cu"], ["Zn", "waterField.Zn", "Zinc as Zn"],
    ["B", "waterField.B", "Boron as B"], ["Mo", "waterField.Mo", "Molybdenum as Mo"],
    ["Cl", "waterField.Cl", "Chloride as Cl"], ["HCO3", "waterField.HCO3", "Bicarbonate (as HCO3)"],
    ["CO3", "waterField.CO3", "Carbonate as CO3"], ["CaCO3", "waterField.CaCO3", "Carbonate hardness (as CaCO3)"],
    ["KH", "waterField.KH", "Carbonate hardness as °KH"], ["SiO2", "waterField.SiO2", "Silicon as SiO2"],
  ].map(([key, labelKey, label]) => ({ key, labelKey, label }));
  const waterValues = Object.fromEntries(waterFieldDefinitions.map(({ key }) => [key, 0]));
  const waterProfileRequests = createLatestRequestGate();
  let molarMasses = {};
  let waterProfiles = [];
  let waterUnit = "mg_l";
  let summaryView = storageGet(SUMMARY_VIEW_KEY, "ion");
  let ionNitrogenExpanded = storageGet(ION_NITROGEN_EXPANDED_KEY, false);
  let mounted = false;

  const t = (key, params) => i18n.t(key, params);
  const scheduleRecalculate = () => onChange();
  const getMolarMass = (key) => Number.isFinite(molarMasses[key]) ? molarMasses[key] : null;
  const convertWaterUnitValue = (key, value, convert) => {
    if (!Number.isFinite(value) || key === "KH") return Number.isFinite(value) ? value : 0;
    const mass = getMolarMass(key);
    return mass ? convert(value, mass) : value;
  };
  const mgToMol = (key, value) => convertWaterUnitValue(key, value, (amount, mass) => amount / mass);
  const molToMg = (key, value) => convertWaterUnitValue(key, value, (amount, mass) => amount * mass);
  const unitLabelForKey = (key) => key === "KH" ? "°dKH" : waterUnit === "mol_l" ? "mmol/L" : "mg/L";

function applyWaterHelpers(values) {
  const updatedKeys = new Set();
  if (!values || typeof values !== "object") {
    return updatedKeys;
  }

  const mm = (key) => getMolarMass(key) || null;
  const hco3FromCo3 = (mgPerL) => {
    const mmCo3 = mm("CO3");
    const mmHco3 = mm("HCO3");
    return mgPerL && mmCo3 && mmHco3 ? (mgPerL * mmHco3) / mmCo3 : 0;
  };
  const hco3FromCaco3 = (mgPerL) => {
    const mmCaco3 = mm("CaCO3");
    const mmHco3 = mm("HCO3");
    return mgPerL && mmCaco3 && mmHco3 ? (mgPerL * mmHco3) / (mmCaco3 / 2) : 0;
  };
  const hco3FromKh = (dkh) => (dkh ? hco3FromCaco3(dkh * 17.848) : 0);
  const so4FromS = (mgPerL) => {
    const mmSo4 = mm("SO4");
    const mmS = mm("S");
    return mgPerL && mmSo4 && mmS ? (mgPerL * mmSo4) / mmS : 0;
  };

  const helperHco3 = hco3FromCo3(values.CO3) + hco3FromCaco3(values.CaCO3) + hco3FromKh(values.KH);
  if (helperHco3 > 0) {
    values.HCO3 = helperHco3;
    values.CO3 = 0;
    values.CaCO3 = 0;
    values.KH = 0;
    updatedKeys.add("HCO3");
    updatedKeys.add("CO3");
    updatedKeys.add("CaCO3");
    updatedKeys.add("KH");
  }

  const so4Value = so4FromS(values.S || 0);
  if (so4Value > 0) {
    values.SO4 = so4Value;
    values.S = 0;
    updatedKeys.add("SO4");
    updatedKeys.add("S");
  }

  return updatedKeys;
}

function handleWaterValueInput(key, rawValue, { updateCurrent = false, invalidate = true } = {}) {
  if (invalidate) waterProfileRequests.invalidate();
  const parsed = decimalInputValue(rawValue);
  waterValues[key] = waterUnit === "mol_l" ? molToMg(key, parsed) : parsed;
  const updatedKeys = applyWaterHelpers(waterValues, getMolarMass);
  updatedKeys
    .filter((updatedKey) => updateCurrent || updatedKey !== key)
    .forEach((updatedKey) => updateWaterInputValue(updatedKey));
  scheduleRecalculate();
}

function renderWaterTable() {
  waterTableBody.innerHTML = "";
  waterFieldDefinitions.forEach((field) => {
    const row = document.createElement("tr");

    const labelCell = document.createElement("td");
    labelCell.textContent = field.labelKey ? t(field.labelKey) : field.label;

    const valueCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.min = "0";
    input.step = waterUnit === "mol_l" && field.key !== "KH" ? "0.001" : "0.01";
    const rawValue = waterValues[field.key] || 0;
    const displayValue = waterUnit === "mol_l" ? mgToMol(field.key, rawValue) : rawValue;
    input.value = formatWaterDisplayValue(displayValue);
    input.dataset.waterKey = field.key;
    if (waterHelperKeys.has(field.key)) {
      input.classList.add("is-helper");
    }
    input.addEventListener("input", (event) => {
      handleWaterValueInput(field.key, event.target.value);
    });
    input.addEventListener("change", () => {
      updateWaterInputValue(field.key);
    });
    input.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") {
        return;
      }
      event.preventDefault();
      handleWaterValueInput(field.key, event.target.value, { updateCurrent: true, invalidate: false });
    });
    valueCell.appendChild(input);

    const unitCell = document.createElement("td");
    unitCell.textContent = unitLabelForKey(field.key);

    row.append(labelCell, valueCell, unitCell);
    waterTableBody.appendChild(row);
  });
}

function updateWaterInputValue(key) {
  const input = qs(`input[data-water-key="${key}"]`, waterTableBody);
  if (!input) {
    return;
  }
  const rawValue = waterValues[key] || 0;
  const displayValue = waterUnit === "mol_l" ? mgToMol(key, rawValue) : rawValue;
  input.value = formatWaterDisplayValue(displayValue);
}

function formatWaterDisplayValue(value) {
  if (!Number.isFinite(value)) {
    return "0";
  }

  const absValue = Math.abs(value);
  if (absValue >= 0.1 || absValue === 0) {
    return value.toFixed(1);
  }

  let decimals = 2;
  if (absValue < 0.01) {
    decimals = 3;
  }
  if (absValue < 0.001) {
    decimals = 4;
  }
  if (absValue < 0.0001) {
    decimals = 5;
  }
  if (absValue < 0.00001) {
    decimals = 6;
  }

  const formatted = value.toFixed(decimals);
  return formatted.replace(/(\.\d*?[1-9])0+$/, "$1").replace(/\.0+$/, "");
}

function renderIonCompactList(container, entries) {
  container.innerHTML = "";
  const cations = [];
  const anions = [];

  entries.forEach(([key, value]) => {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
      return;
    }
    const item = { key, value: numericValue };
    if (numericValue >= 0) {
      cations.push(item);
    } else {
      anions.push(item);
    }
  });

  const maxCols = Math.max(cations.length, anions.length, 1);
  const table = document.createElement("table");
  table.classList.add("compact-ion-table");
  table.style.setProperty("--ion-cols", `${maxCols}`);

  const colgroup = document.createElement("colgroup");
  const labelCol = document.createElement("col");
  labelCol.classList.add("compact-ion-label-col");
  colgroup.appendChild(labelCol);
  for (let i = 0; i < maxCols; i += 1) {
    const col = document.createElement("col");
    col.classList.add("compact-ion-value-col");
    colgroup.appendChild(col);
  }
  table.appendChild(colgroup);

  const tbody = document.createElement("tbody");
  tbody.appendChild(buildIonRow(t("chem.cations"), cations, maxCols));
  tbody.appendChild(buildIonRow(t("chem.anions"), anions, maxCols));
  table.appendChild(tbody);
  container.appendChild(table);
}

function buildIonRow(label, items, maxCols) {
  const row = document.createElement("tr");

  const labelCell = document.createElement("th");
  labelCell.classList.add("compact-label");
  labelCell.textContent = label;
  row.appendChild(labelCell);

  for (let i = 0; i < maxCols; i += 1) {
    const cell = document.createElement("td");
    cell.classList.add("compact-ion-cell");
    const item = items[i];
    if (item) {
      cell.textContent = `${item.key} ${ionFormatter.format(Math.abs(item.value))}`;
    } else {
      cell.textContent = "";
    }
    row.appendChild(cell);
  }

  return row;
}

function renderIonBalanceCompact(container, entries) {
  container.innerHTML = "";
  const labelMap = {
    cations_meq_per_l: t("calculator.ionBalance.cations"),
    anions_meq_per_l: t("calculator.ionBalance.anions"),
    raw_cbe_percent_signed: t("calculator.ionBalance.cbeRaw"),
    din_38402_62_percent_signed: t("calculator.ionBalance.dinRaw"),
  };
  const unitMap = {
    cations_meq_per_l: "meq/L",
    anions_meq_per_l: "meq/L",
    raw_cbe_percent_signed: "%",
    din_38402_62_percent_signed: "%",
  };
  const rows = [
    ["cations_meq_per_l", "anions_meq_per_l"],
    ["raw_cbe_percent_signed", "din_38402_62_percent_signed"],
  ];
  const values = new Map(entries.map(([key, value]) => [key, value]));
  if (!values.has("raw_cbe_percent_signed") && values.has("error_percent_signed")) {
    values.set("raw_cbe_percent_signed", values.get("error_percent_signed"));
  }
  if (!values.has("din_38402_62_percent_signed")) {
    const rawCbe = Number(values.get("raw_cbe_percent_signed"));
    if (Number.isFinite(rawCbe)) {
      values.set("din_38402_62_percent_signed", rawCbe * 2.0);
    }
  }

  const table = document.createElement("table");
  table.classList.add("compact-ion-table", "compact-balance-table");
  table.style.setProperty("--ion-cols", "2");

  const colgroup = document.createElement("colgroup");
  const labelCol = document.createElement("col");
  labelCol.classList.add("compact-ion-label-col");
  colgroup.appendChild(labelCol);
  for (let i = 0; i < 2; i += 1) {
    const col = document.createElement("col");
    col.classList.add("compact-ion-value-col");
    colgroup.appendChild(col);
  }
  table.appendChild(colgroup);

  const tbody = document.createElement("tbody");
  rows.forEach((rowKeys) => {
    const row = document.createElement("tr");
    const unit = unitMap[rowKeys[0]];
    const labelCell = document.createElement("th");
    labelCell.classList.add("compact-label");
    labelCell.textContent = unit.toUpperCase();
    row.appendChild(labelCell);

    rowKeys.forEach((key) => {
      const cell = document.createElement("td");
      cell.classList.add("compact-ion-cell");
      const value = Number(values.get(key));
      cell.textContent = Number.isFinite(value)
        ? `${labelMap[key]} ${ionFormatter.format(value)} ${unitMap[key]}`
        : "";
      row.appendChild(cell);
    });
    tbody.appendChild(row);
  });
  table.appendChild(tbody);

  container.appendChild(table);
}

function buildSummaryColumns(extraColumns = []) {
  const columns = [];
  summaryColumnOrder.forEach((column) => {
    columns.push({ type: "base", column });
    if (column.element === "N_total" && extraColumns.length) {
      extraColumns.forEach((extra) => {
        columns.push({ type: "extra", column: extra });
      });
    }
  });
  return columns;
}

function buildSummaryColgroup(summaryColumns) {
  const colgroup = document.createElement("colgroup");
  const labelCol = document.createElement("col");
  labelCol.classList.add("col-row-label");
  labelCol.style.width = summaryLabelWidth;
  colgroup.appendChild(labelCol);
  summaryColumns.forEach((columnGroup) => {
    const col = document.createElement("col");
    if (columnGroup.type === "extra") {
      const key = columnGroup.column.key;
      col.classList.add(`col-${normalizeColumnKey(key)}`, "ion-n-extra");
    } else {
      col.classList.add(`col-${normalizeColumnKey(columnGroup.column.oxide)}`);
    }
    colgroup.appendChild(col);
  });
  return colgroup;
}

function renderSummaryTable({
  table,
  headerLabels,
  rowLabel,
  rowLabelClass,
  valueMap,
  valueKey,
  formatter,
  extraColumns = [],
  extraFormatter,
}) {
  table.innerHTML = "";
  const summaryColumns = buildSummaryColumns(extraColumns);
  table.appendChild(buildSummaryColgroup(summaryColumns));

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const spacer = document.createElement("th");
  spacer.textContent = "";
  headerRow.appendChild(spacer);
  summaryColumns.forEach((columnGroup) => {
    const th = document.createElement("th");
    if (columnGroup.type === "extra") {
      const key = columnGroup.column.key;
      th.textContent = columnGroup.column.labelKey ? t(columnGroup.column.labelKey) : columnGroup.column.label;
      th.classList.add(`col-${normalizeColumnKey(key)}`, "ion-n-extra");
    } else {
      const column = columnGroup.column;
      const label = document.createElement("span");
      label.textContent = headerLabels(column);
      th.appendChild(label);
      th.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
      if (column.element === "N_total" && extraColumns.length) {
        th.classList.add("has-expander");
        const toggleButton = document.createElement("button");
        toggleButton.type = "button";
        toggleButton.classList.add("column-expander");
        toggleButton.dataset.ionNToggle = "true";
        toggleButton.setAttribute("aria-label", t("aria.toggleNDetails"));
        toggleButton.setAttribute("aria-expanded", ionNitrogenExpanded ? "true" : "false");
        toggleButton.textContent = ionNitrogenExpanded ? "‹" : "›";
        th.appendChild(toggleButton);
      }
    }
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const tr = document.createElement("tr");
  const labelCell = document.createElement("th");
  labelCell.textContent = rowLabel;
  labelCell.classList.add("row-label");
  if (rowLabelClass) {
    labelCell.classList.add(rowLabelClass);
  }
  labelCell.scope = "row";
  tr.appendChild(labelCell);

  summaryColumns.forEach((columnGroup) => {
    if (columnGroup.type === "extra") {
      const key = columnGroup.column.key;
      const rawValue = valueMap.get(key);
      const formatted = extraFormatter
        ? extraFormatter(key, Number(rawValue))
        : formatter({ element: key }, Number(rawValue));
      const extraCell = document.createElement("td");
      extraCell.textContent = formatted;
      extraCell.classList.add(`col-${normalizeColumnKey(key)}`, "ion-n-extra");
      tr.appendChild(extraCell);
      return;
    }
    const column = columnGroup.column;
    const rawValue = valueMap.get(valueKey(column));
    const td = document.createElement("td");
    const formatted = formatter(column, Number(rawValue));
    td.textContent = formatted;
    td.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
    tr.appendChild(td);
  });
  tbody.appendChild(tr);
  table.appendChild(tbody);
}

function renderWaterSummaryTable(table, waterElements) {
  const waterMap = new Map(Object.entries(waterElements || {}));
  if (waterSummaryBadge) {
    waterSummaryBadge.textContent = waterUnit === "mol_l" ? "mmol/L" : "mg/L";
  }
  renderSummaryTable({
    table,
    headerLabels: (column) => t(column.ionHeaderLabelKey || column.ionHeaderLabel),
    valueKey: (column) => column.element,
    rowLabel: t("water.rowWaterValues"),
    valueMap: waterMap,
    formatter: (column, value) =>
      waterUnit === "mol_l" ? formatTraceValue(value) : formatNutrientValue(column.element, value),
  });
}

function renderOxideSummaryTable(table, oxides) {
  const oxideMap = new Map(Object.entries(oxides || {}));
  if (oxideSummaryBadge) {
    oxideSummaryBadge.textContent = t("unit.mgLoxide");
  }
  renderSummaryTable({
    table,
    headerLabels: (column) => t(column.oxideHeaderLabelKey || column.oxideHeaderLabel),
    valueKey: (column) => column.oxide,
    rowLabel: t("calculator.oxideForms"),
    valueMap: oxideMap,
    formatter: (column, value) => formatOxideValue(column.oxide, value),
  });
}

function renderIonSummaryTable(table, elements) {
  const elementMap = new Map(Object.entries(elements || {}));
  if (ionSummaryBadge) {
    ionSummaryBadge.textContent = "mg/L";
  }
  const nitrogenColumns = [
    { key: "N_NO3", label: "NO3", labelKey: "solver.nNo3" },
    { key: "N_NH4", label: "NH4", labelKey: "solver.nNh4" },
    { key: "N_UREA", label: "UREA", labelKey: "solver.nUrea" },
  ];
  renderSummaryTable({
    table,
    headerLabels: (column) => t(column.ionHeaderLabelKey || column.ionHeaderLabel),
    valueKey: (column) => column.element,
    rowLabel: t("water.rowDissolvedIons"),
    rowLabelClass: "row-label--ion",
    valueMap: elementMap,
    formatter: (column, value) => formatNutrientValue(column.element, value),
    extraColumns: nitrogenColumns,
    extraFormatter: (key, value) => formatNutrientValue(key, value),
  });
  table.classList.toggle("is-n-expanded", ionNitrogenExpanded);
  table.classList.toggle("is-n-collapsed", !ionNitrogenExpanded);
  const toggleButton = qs("[data-ion-n-toggle]", table);
  if (toggleButton) {
    toggleButton.addEventListener("click", () => {
      ionNitrogenExpanded = !ionNitrogenExpanded;
      storageSet(ION_NITROGEN_EXPANDED_KEY, ionNitrogenExpanded);
      table.classList.toggle("is-n-expanded", ionNitrogenExpanded);
      table.classList.toggle("is-n-collapsed", !ionNitrogenExpanded);
      toggleButton.textContent = ionNitrogenExpanded ? "‹" : "›";
      toggleButton.setAttribute("aria-expanded", ionNitrogenExpanded ? "true" : "false");
    });
  }
}

function setSummaryView(nextView) {
  const allowed = new Set(["water", "oxide", "ion"]);
  const view = allowed.has(nextView) ? nextView : "ion";
  summaryView = view;
  storageSet(SUMMARY_VIEW_KEY, view);

  if (summaryViewToggle) {
    qsa("button[data-summary-view]", summaryViewToggle).forEach((button) => {
      const isActive = button.dataset.summaryView === view;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
      button.tabIndex = isActive ? 0 : -1;
    });
  }

  summaryPanels.forEach((panel) => {
    const panelView = panel.dataset.summaryPanel;
    panel.hidden = panelView !== view;
  });

  if (summaryViewToggle) {
    const activePanel = qs(`.summary-panel[data-summary-panel="${view}"]`);
    const activeTitle = activePanel ? qs(".table-card-title", activePanel) : null;
    if (activeTitle && !activeTitle.contains(summaryViewToggle)) {
      activeTitle.prepend(summaryViewToggle);
    }
  }

  const summaryScroll = qs("#summaryScroll");
  if (summaryScroll) {
    summaryScroll.scrollLeft = 0;
  }
}

function normalizeColumnKey(key) {
  return key.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function formatTraceValue(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }

  const absValue = Math.abs(value);
  let maxDecimals = 2;
  if (absValue < 0.01) {
    maxDecimals = 4;
  } else if (absValue < 1) {
    maxDecimals = 3;
  }

  const formatter = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxDecimals,
    useGrouping: false,
  });
  return formatter.format(value);
}

function formatNutrientValue(key, value) {
  if (!Number.isFinite(value)) {
    return "-";
  }

  if (nutrientIntegerKeys.has(key)) {
    return nutrientIntegerFormatter.format(value);
  }

  if (nutrientTraceKeys.has(key)) {
    return formatTraceValue(value);
  }

  return nutrientFormatter.format(value);
}

function formatOxideValue(key, value) {
  if (!Number.isFinite(value)) {
    return "-";
  }

  if (oxideIntegerKeys.has(key)) {
    return nutrientIntegerFormatter.format(value);
  }

  if (oxideTraceKeys.has(key)) {
    return formatTraceValue(value);
  }

  return nutrientFormatter.format(value);
}

function buildWaterPayloadForApi(rawValues) {
  const values = { ...rawValues };
  applyWaterHelpers(values, getMolarMass);
  return values;
}

function waterElementsForDisplay(elements) {
  if (waterUnit !== "mol_l") {
    return elements;
  }
  const converted = {};
  const mm = (key) => getMolarMass(key) || null;
  Object.entries(elements).forEach(([key, value]) => {
    let molKey = key;
    if (key === "N_total") {
      molKey = "N";
    }
    const molarMass = mm(molKey);
    converted[key] = molarMass ? value / molarMass : value;
  });
  return converted;
}

function renderEcPair(ecValues, el18, el25) {
  const ec18 = Number(ecValues["18.0"]);
  const ec25 = Number(ecValues["25.0"]);
  el18.textContent = Number.isFinite(ec18) ? formatNumber(ec18) : "-";
  el25.textContent = Number.isFinite(ec25) ? formatNumber(ec25) : "-";
}

function ratioValueText(value) {
  const text = String(value || "").trim();
  if (!text) {
    return "-";
  }
  const markerIndex = text.indexOf("=");
  return markerIndex >= 0 ? text.slice(markerIndex + 1) : text;
}

function formatRatioNumber(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  const rounded = Math.round(value * 10) / 10;
  return rounded.toFixed(1).replace(/\.0$/, "");
}

function ratioToOneText(value, leftLabel, rightLabel) {
  const parts = ratioValueText(value).split(":").map((part) => Number(part));
  if (parts.length !== 2 || !Number.isFinite(parts[0]) || !Number.isFinite(parts[1])) {
    return "-";
  }
  const [left, right] = parts;
  if (left <= 0 && right <= 0) {
    return `0 ${leftLabel} : 0 ${rightLabel}`;
  }
  if (right <= 0) {
    return `${formatRatioNumber(left)} ${leftLabel} : 0 ${rightLabel}`;
  }
  return `${formatRatioNumber(left / right)} ${leftLabel} : 1 ${rightLabel}`;
}

function renderIonRatios(metrics) {
  const ratios = metrics?.npk_ratios_ion || {};
  if (caMgRatioValue) {
    caMgRatioValue.textContent = ratioToOneText(ratios["Ca:Mg"], "Ca", "Mg");
  }
  if (!ionRatioList) {
    return;
  }

  ionRatioList.innerHTML = "";
  ["N:K", "Ca:K", "Na:Mg", "SO4:P", "P:K", "Fe:Mg"].forEach((key) => {
    const item = document.createElement("div");
    item.className = "ion-ratio-pill";

    const label = document.createElement("span");
    label.textContent = key;
    const value = document.createElement("strong");
    value.textContent = ratioValueText(ratios[key]);

    item.append(label, value);
    ionRatioList.appendChild(item);
  });
}

function applyWaterProfile(profile) {
  waterProfileRequests.invalidate();
  const mg = profile.normalized_mg_per_l || profile.mg_per_l || {};
  waterFieldDefinitions.forEach((field) => {
    waterValues[field.key] = Number(mg[field.key]) || 0;
  });
  applyWaterHelpers(waterValues, getMolarMass);

  waterProfileNameInput.value = profile.name || "";
  osmosisPercentInput.value = profile.osmosis_percent ?? 0;
  renderWaterTable();
  scheduleRecalculate();
}

function renderWaterProfileOptions() {
  waterProfileSelect.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = t("common.selectEmpty");
  waterProfileSelect.appendChild(empty);

  waterProfiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.filename;
    option.textContent = profile.name || profile.filename;
    waterProfileSelect.appendChild(option);
  });
  syncSelectedOptionTitle(waterProfileSelect);
}

  function setResources({ profiles = [], masses = {} } = {}) {
    waterProfiles = profiles;
    molarMasses = masses;
    renderWaterProfileOptions();
  }

  function setProfiles(profiles) {
    waterProfiles = profiles || [];
    renderWaterProfileOptions();
  }

  function getPayload() {
    return buildWaterPayloadForApi(waterValues);
  }

  function getSnapshot() {
    return {
      water_profile_value: waterProfileSelect.value || "",
      osmosis_percent: decimalInputValue(osmosisPercentInput.value),
      water_unit: waterUnit,
      water_values: { ...waterValues },
    };
  }

  function restoreSnapshot(snapshot = {}) {
    waterUnit = snapshot.water_unit === "mol_l" ? "mol_l" : "mg_l";
    waterUnitToggle.checked = waterUnit === "mol_l";
    osmosisPercentInput.value = Number(snapshot.osmosis_percent) || 0;
    waterProfileSelect.value = snapshot.water_profile_value || "";
    syncSelectedOptionTitle(waterProfileSelect);
    waterFieldDefinitions.forEach(({ key }) => {
      waterValues[key] = Number(snapshot.water_values?.[key]) || 0;
    });
    applyWaterHelpers(waterValues);
    renderWaterTable();
  }

  function renderCalculation(data) {
    const oxides = data.oxides_mg_per_l || {};
    const elements = data.elements_mg_per_l || {};
    const metrics = data.npk_metrics || {};
    renderWaterSummaryTable(waterSummaryTable, waterElementsForDisplay(data.water_elements_mg_per_l || {}));
    renderOxideSummaryTable(oxideSummaryTable, oxides);
    renderIonSummaryTable(ionSummaryTable, elements);
    renderIonCompactList(ionMeqList, Object.entries(data.ions_meq_per_l || {}));
    renderIonBalanceCompact(ionBalanceList, Object.entries(data.ion_balance || {}));
    npkAllPctValue.textContent = metrics.npk_all_pct || "-";
    npkPNormValue.textContent = metrics.npk_p_norm || "-";
    npkNpkPctValue.textContent = metrics.npk_npk_pct || "-";
    renderIonRatios(metrics);
    renderEcPair(data.ec?.ec_mS_per_cm || {}, ec18Value, ec25Value);
    renderEcPair(data.ec_water?.ec_mS_per_cm || {}, ecWater18Value, ecWater25Value);
  }

  function renderEmptyCalculation() {
    renderWaterSummaryTable(waterSummaryTable, {});
    renderOxideSummaryTable(oxideSummaryTable, {});
    renderIonSummaryTable(ionSummaryTable, {});
  }

  async function loadSelectedProfile() {
    if (!waterProfileSelect.value) {
      notifications.reportError(null, t("errors.waterProfileRequired"));
      return;
    }
    const version = waterProfileRequests.reserve();
    try {
      const profile = await api.fetchWaterProfileData(waterProfileSelect.value, t("errors.loadWaterProfile"));
      if (!waterProfileRequests.isCurrent(version)) return;
      applyWaterProfile(profile);
      api.persistPreferences({ last_water_profile: waterProfileSelect.value });
    } catch (error) {
      if (waterProfileRequests.isCurrent(version)) notifications.reportError(error, t("errors.loadWaterProfile"));
    }
  }

  async function resetProfile() {
    const version = waterProfileRequests.reserve();
    try {
      const profile = await api.fetchWaterProfileData("default", t("errors.loadWaterProfile"));
      if (!waterProfileRequests.isCurrent(version)) return;
      waterProfileSelect.value = "default.yml";
      syncSelectedOptionTitle(waterProfileSelect);
      applyWaterProfile(profile);
      api.persistPreferences({ last_water_profile: "default.yml" });
    } catch (error) {
      if (waterProfileRequests.isCurrent(version)) notifications.reportError(error, t("errors.loadWaterProfile"));
    }
  }

  async function saveProfile() {
    const name = waterProfileNameInput.value.trim();
    if (!name) {
      notifications.reportError(null, t("errors.profileNameRequired"));
      return;
    }
    try {
      await api.saveWaterProfileData({
        name,
        source: "Horticalc UI",
        mg_per_l: getPayload(),
        osmosis_percent: decimalInputValue(osmosisPercentInput.value),
      }, t("errors.saveFailed"));
      setProfiles(await api.fetchWaterProfiles(t("errors.loadWaterProfiles")));
    } catch (error) {
      notifications.reportError(error, t("errors.saveFailed"));
    }
  }

  function mount() {
    if (mounted) return;
    mounted = true;
    loadWaterProfileButton.addEventListener("click", loadSelectedProfile);
    waterProfileSelect.addEventListener("change", () => syncSelectedOptionTitle(waterProfileSelect));
    resetWaterProfileButton.addEventListener("click", resetProfile);
    saveWaterProfileButton.addEventListener("click", saveProfile);
    osmosisPercentInput.addEventListener("input", () => {
      waterProfileRequests.invalidate();
      scheduleRecalculate();
    });
    osmosisPercentInput.addEventListener("change", () => {
      osmosisPercentInput.value = String(decimalInputValue(osmosisPercentInput.value));
    });
    waterUnitToggle.addEventListener("change", (event) => {
      waterUnit = event.target.checked ? "mol_l" : "mg_l";
      renderWaterTable();
      scheduleRecalculate();
    });
    summaryViewToggle?.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-summary-view]");
      if (button) setSummaryView(button.dataset.summaryView);
    });
    setSummaryView(summaryView);
  }

  function refreshLocalized() {
    renderWaterProfileOptions();
    renderWaterTable();
  }

  return {
    applyProfile: applyWaterProfile,
    buildWaterPayload: getPayload,
    formatOxideValue,
    get osmosisPercent() { return decimalInputValue(osmosisPercentInput.value); },
    get selectedProfile() { return waterProfileSelect.value || ""; },
    getSnapshot,
    loadProfile: (filename) => api.fetchWaterProfileData(filename, t("errors.loadWaterProfile")),
    mount,
    refreshLocalized,
    renderCalculation,
    renderEmptyCalculation,
    renderTable: renderWaterTable,
    restoreSnapshot,
    setProfiles,
    setResources,
    setOsmosisPercent(value) { osmosisPercentInput.value = Number(value) || 0; },
    setSelectedProfile(filename) {
      waterProfileSelect.value = filename || "";
      syncSelectedOptionTitle(waterProfileSelect);
    },
  };
}
