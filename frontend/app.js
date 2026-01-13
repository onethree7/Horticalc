const fertilizerSelectTableWrap = document.querySelector("#fertilizerSelectTableWrap");
const calculatorTableWrap = document.querySelector("#calculatorTableWrap");
const reloadButton = document.querySelector("#reloadData");
const calculateButton = document.querySelector("#calculateBtn");
const apiBaseInput = document.querySelector("#apiBase");
const addRowButton = document.querySelector("#addFertilizerRow");
const removeRowButton = document.querySelector("#removeFertilizerRow");
const waterTableBody = document.querySelector("#waterValuesTable tbody");
const waterProfileSelect = document.querySelector("#waterProfileSelect");
const waterProfileNameInput = document.querySelector("#waterProfileName");
const loadWaterProfileButton = document.querySelector("#loadWaterProfile");
const saveWaterProfileButton = document.querySelector("#saveWaterProfile");
const resetWaterProfileButton = document.querySelector("#resetWaterProfile");
const osmosisPercentInput = document.querySelector("#osmosisPercent");
const waterUnitToggle = document.querySelector("#waterUnitToggle");
const toggleWaterValuesButton = document.querySelector("#toggleWaterValues");
const waterContent = document.querySelector("#waterContent");
const npkAllPctValue = document.querySelector("#npkAllPct");
const npkPNormValue = document.querySelector("#npkPNorm");
const npkNpkPctValue = document.querySelector("#npkNpkPct");
const ec18Value = document.querySelector("#ec18Value");
const ec25Value = document.querySelector("#ec25Value");
const ecWater18Value = document.querySelector("#ecWater18Value");
const ecWater25Value = document.querySelector("#ecWater25Value");

const summaryTable = document.querySelector("#summaryTable");
const ionMeqList = document.querySelector("#ionMeqList");
const ionBalanceList = document.querySelector("#ionBalanceList");

let fertilizerOptions = [];
const selectedFertilizers = [{ name: "", form: "", weight: "" }];
const fertilizerAmounts = [0];
let molarMasses = {};
let waterProfiles = [];
let waterUnit = "mg_l";
let lastCalculation = null;
let recalculateTimer = null;
let fertilizerSelectTable;
let calculatorTable;

const waterFieldDefinitions = [
  { key: "NH4", label: "Ammonium in NH4" },
  { key: "NH3", label: "Ammoniak in NH3" },
  { key: "NO3", label: "Nitrat in NO3" },
  { key: "NO2", label: "Nitrit in NO2" },
  { key: "PO4", label: "Phosphat in PO4" },
  { key: "P", label: "Phosphor in P" },
  { key: "K", label: "Kalium in K" },
  { key: "Ca", label: "Calcium in Ca" },
  { key: "Mg", label: "Magnesium in Mg" },
  { key: "Na", label: "Natrium in Na" },
  { key: "SO4", label: "Sulfat in SO4" },
  { key: "S", label: "Schwefel in S" },
  { key: "Fe", label: "Eisen in Fe" },
  { key: "Mn", label: "Mangan in Mn" },
  { key: "Cu", label: "Kupfer in Cu" },
  { key: "Zn", label: "Zink in Zn" },
  { key: "B", label: "Bor in B" },
  { key: "Mo", label: "Molybdän in Mo" },
  { key: "Cl", label: "Chlor in Cl" },
  { key: "HCO3", label: "Carbonate in HCO3" },
  { key: "CO3", label: "Carbonat in CO3" },
  { key: "CaCO3", label: "Gesamtcarbonathärte in CaCO3" },
  { key: "KH", label: "Carbonathärte in °KH" },
  { key: "SiO2", label: "Silicium in SiO2" },
];

const waterValues = Object.fromEntries(waterFieldDefinitions.map((field) => [field.key, 0]));
const numberFormatter = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});
const nutrientFormatter = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});
const ionFormatter = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});
const nutrientIntegerFormatter = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});
const nutrientIntegerKeys = new Set(["N_total", "P", "K", "Ca", "Mg", "S"]);
const nutrientTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "Si"]);
const oxideIntegerKeys = new Set([
  "N_total",
  "P2O5",
  "K2O",
  "CaO",
  "MgO",
  "SO4",
]);
const oxideTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "SiO2"]);
const carbonateHelperKeys = new Set(["CO3", "CaCO3", "KH"]);
const summaryColumnOrder = [
  { oxide: "N_total", element: "N_total", label: "N_total" },
  { oxide: "P2O5", element: "P", label: "P2O5/P" },
  { oxide: "K2O", element: "K", label: "K2O/K" },
  { oxide: "CaO", element: "Ca", label: "CaO/Ca" },
  { oxide: "MgO", element: "Mg", label: "MgO/Mg" },
  { oxide: "SO4", element: "S", label: "SO4/S" },
  { oxide: "Fe", element: "Fe", label: "Fe" },
  { oxide: "Mn", element: "Mn", label: "Mn" },
  { oxide: "Cu", element: "Cu", label: "Cu" },
  { oxide: "Zn", element: "Zn", label: "Zn" },
  { oxide: "B", element: "B", label: "B" },
  { oxide: "Mo", element: "Mo", label: "Mo" },
  { oxide: "SiO2", element: "Si", label: "SiO2/Si" },
  { oxide: "Na2O", element: "Na", label: "Na2O/Na" },
  { oxide: "Cl", element: "Cl", label: "Cl" },
  { oxide: "HCO3", element: "HCO3", label: "HCO3" },
];

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}

function createSelect(options, onChange) {
  const select = document.createElement("select");
  const emptyOption = document.createElement("option");
  emptyOption.value = "";
  emptyOption.textContent = "-- auswählen --";
  select.appendChild(emptyOption);

  options.forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt.name;
    option.textContent = opt.name;
    select.appendChild(option);
  });

  select.addEventListener("change", (event) => onChange(event.target.value));
  return select;
}

function createTable({ id, className, colgroupClasses, headerCells }) {
  const table = document.createElement("table");
  table.id = id;
  table.className = className;

  const colgroup = document.createElement("colgroup");
  colgroupClasses.forEach((colClass) => {
    const col = document.createElement("col");
    col.className = colClass;
    colgroup.appendChild(col);
  });
  table.appendChild(colgroup);

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headerCells.forEach((cell) => {
    const th = document.createElement("th");
    th.textContent = cell.label;
    if (cell.colSpan) {
      th.colSpan = cell.colSpan;
    }
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  table.appendChild(tbody);

  return { table, tbody };
}

function initializeFertilizerTables() {
  const selectTable = createTable({
    id: "fertilizerSelectTable",
    className: "grid grid--form grid--fertilizer",
    colgroupClasses: ["col-index", "col-name", "col-form", "col-weight"],
    headerCells: [
      { label: "#" },
      { label: "Dünger (Dropdown)" },
      { label: "Form" },
      { label: "Gewicht" },
    ],
  });
  fertilizerSelectTableWrap.appendChild(selectTable.table);
  fertilizerSelectTable = selectTable.tbody;

  const calculator = createTable({
    id: "calculatorTable",
    className: "grid grid--form grid--fertilizer",
    colgroupClasses: ["col-index", "col-name", "col-form", "col-amount"],
    headerCells: [
      { label: "#" },
      { label: "Düngername", colSpan: 2 },
      { label: "Menge (g)" },
    ],
  });
  calculatorTableWrap.appendChild(calculator.table);
  calculatorTable = calculator.tbody;
}

function renderTableRows(tableBody, rowCount, buildRow) {
  tableBody.innerHTML = "";
  for (let i = 0; i < rowCount; i += 1) {
    tableBody.appendChild(buildRow(i));
  }
}

function renderSelectionTable() {
  renderTableRows(fertilizerSelectTable, selectedFertilizers.length, (i) => {
    const row = document.createElement("tr");

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const selectCell = document.createElement("td");
    const select = createSelect(fertilizerOptions, (value) => {
      const match = fertilizerOptions.find((opt) => opt.name === value);
      selectedFertilizers[i] = {
        name: value,
        form: match ? match.form : "",
        weight: match ? match.weight_factor : "",
      };
      renderSelectionTable();
      renderCalculatorTable();
      scheduleRecalculate();
    });
    select.value = selectedFertilizers[i].name;
    selectCell.appendChild(select);

    const formCell = document.createElement("td");
    formCell.textContent = selectedFertilizers[i].form || "-";

    const weightCell = document.createElement("td");
    weightCell.textContent = selectedFertilizers[i].weight || "-";

    row.append(indexCell, selectCell, formCell, weightCell);
    return row;
  });
}

function renderCalculatorTable() {
  renderTableRows(calculatorTable, selectedFertilizers.length, (i) => {
    const row = document.createElement("tr");

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const nameCell = document.createElement("td");
    nameCell.textContent = selectedFertilizers[i].name || "-";
    nameCell.colSpan = 2;

    const amountCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.step = "0.01";
    input.value = fertilizerAmounts[i];
    input.addEventListener("input", (event) => {
      fertilizerAmounts[i] = Number(event.target.value) || 0;
      scheduleRecalculate();
    });
    amountCell.appendChild(input);

    row.append(indexCell, nameCell, amountCell);
    return row;
  });
}

function renderWaterTable() {
  waterTableBody.innerHTML = "";
  waterFieldDefinitions.forEach((field) => {
    const row = document.createElement("tr");

    const labelCell = document.createElement("td");
    labelCell.textContent = field.label;

    const valueCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.step = waterUnit === "mol_l" && field.key !== "KH" ? "0.0001" : "0.01";
    const rawValue = waterValues[field.key] || 0;
    const displayValue = waterUnit === "mol_l" ? mgToMol(field.key, rawValue) : rawValue;
    input.value = formatWaterDisplayValue(displayValue);
    input.dataset.waterKey = field.key;
    if (carbonateHelperKeys.has(field.key)) {
      input.classList.add("is-helper");
    }
    input.addEventListener("input", (event) => {
      const parsed = Number(event.target.value) || 0;
      waterValues[field.key] = waterUnit === "mol_l" ? molToMg(field.key, parsed) : parsed;
      if (field.key === "CO3") {
        waterValues.HCO3 = hco3FromCo3Value(waterValues.CO3 || 0);
        updateWaterInputValue("HCO3");
      } else if (field.key === "CaCO3") {
        waterValues.HCO3 = hco3FromCaco3Value(waterValues.CaCO3 || 0);
        updateWaterInputValue("HCO3");
      } else if (field.key === "KH") {
        waterValues.HCO3 = hco3FromKhValue(waterValues.KH || 0);
        updateWaterInputValue("HCO3");
      }
      scheduleRecalculate();
    });
    valueCell.appendChild(input);

    const unitCell = document.createElement("td");
    unitCell.textContent = unitLabelForKey(field.key);

    row.append(labelCell, valueCell, unitCell);
    waterTableBody.appendChild(row);
  });
}

function updateWaterInputValue(key) {
  const input = waterTableBody.querySelector(`input[data-water-key="${key}"]`);
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

function formatNumber(value, formatter = numberFormatter) {
  if (Number.isFinite(value)) {
    return formatter.format(value);
  }
  return "-";
}

function getMolarMass(key) {
  const value = molarMasses[key];
  return Number.isFinite(value) ? value : null;
}

function getMolarMassOrOne(key) {
  return getMolarMass(key) || 1;
}

function mgToMol(key, value) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  if (key === "KH") {
    return value;
  }
  const mm = getMolarMass(key);
  if (!mm) {
    return value;
  }
  return value / 1000 / mm;
}

function molToMg(key, value) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  if (key === "KH") {
    return value;
  }
  const mm = getMolarMass(key);
  if (!mm) {
    return value;
  }
  return value * 1000 * mm;
}

function unitLabelForKey(key) {
  if (key === "KH") {
    return "°dKH";
  }
  return waterUnit === "mol_l" ? "mol/L" : "mg/L";
}

function scheduleRecalculate() {
  if (recalculateTimer) {
    clearTimeout(recalculateTimer);
  }
  recalculateTimer = setTimeout(async () => {
    try {
      const data = await calculate();
      renderCalculation(data);
    } catch (error) {
      alert(error.message);
    }
  }, 250);
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
  tbody.appendChild(buildIonRow("CATIONS", cations, maxCols));
  tbody.appendChild(buildIonRow("ANIONS", anions, maxCols));
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
    cations_meq_per_l: "Σ+",
    anions_meq_per_l: "Σ−",
    error_percent_signed: "Δ",
  };
  const order = ["cations_meq_per_l", "anions_meq_per_l", "error_percent_signed"];
  const values = new Map(entries.map(([key, value]) => [key, value]));

  const table = document.createElement("table");
  table.classList.add("compact-balance-table");
  const tbody = document.createElement("tbody");
  const row = document.createElement("tr");

  order.forEach((key) => {
    if (!values.has(key)) {
      return;
    }
    const value = Number(values.get(key));
    if (!Number.isFinite(value)) {
      return;
    }
    const cell = document.createElement("td");
    cell.classList.add("compact-item");
    cell.textContent = `${labelMap[key]} ${ionFormatter.format(value)}`;
    row.appendChild(cell);
  });

  tbody.appendChild(row);
  table.appendChild(tbody);
  container.appendChild(table);
}

function renderSummaryTable(table, oxides, elements, waterElements = null) {
  table.innerHTML = "";
  const oxideMap = new Map(Object.entries(oxides));
  const elementMap = new Map(Object.entries(elements));
  const waterMap = waterElements ? new Map(Object.entries(waterElements)) : null;

  const colgroup = document.createElement("colgroup");
  const labelCol = document.createElement("col");
  labelCol.classList.add("col-row-label");
  colgroup.appendChild(labelCol);
  summaryColumnOrder.forEach((column) => {
    const col = document.createElement("col");
    col.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
    colgroup.appendChild(col);
  });
  table.appendChild(colgroup);

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const spacer = document.createElement("th");
  spacer.textContent = "";
  headerRow.appendChild(spacer);
  summaryColumnOrder.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = column.label;
    th.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const rows = [];
  if (waterMap) {
    rows.push({
      label: "Wasserwerte (nur Wasser)",
      valueMap: waterMap,
      formatter: waterUnit === "mol_l" ? formatTraceValue : formatNutrientValue,
    });
  }
  rows.push(
    {
      label: "Oxide (Wasser + Dünger)",
      valueMap: oxideMap,
      formatter: formatOxideValue,
    },
    {
      label: "Ionen (Wasser + Dünger)",
      valueMap: elementMap,
      formatter: formatNutrientValue,
    }
  );

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    const labelCell = document.createElement("th");
    labelCell.textContent = row.label;
    labelCell.classList.add("row-label");
    labelCell.scope = "row";
    tr.appendChild(labelCell);

    summaryColumnOrder.forEach((column) => {
      const key = row.valueMap === oxideMap ? column.oxide : column.element;
      const rawValue = row.valueMap.get(key);
      const td = document.createElement("td");
      const formatted = row.formatter(key, Number(rawValue));
      td.textContent = formatted;
      td.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
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

  const formatter = new Intl.NumberFormat("de-DE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxDecimals,
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

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function hco3FromCaco3Value(mgCaCO3) {
  if (!mgCaCO3) {
    return 0;
  }
  const equiv = getMolarMassOrOne("CaCO3") / 2;
  return (mgCaCO3 * getMolarMassOrOne("HCO3")) / equiv;
}

function hco3FromCo3Value(mgCo3) {
  if (!mgCo3) {
    return 0;
  }
  return (mgCo3 * getMolarMassOrOne("HCO3")) / getMolarMassOrOne("CO3");
}

function hco3FromKhValue(dKh) {
  if (!dKh) {
    return 0;
  }
  return hco3FromCaco3Value(dKh * 17.848);
}

function p2o5FromP(mgP) {
  return mgP ? (mgP * getMolarMassOrOne("P2O5")) / (2 * getMolarMassOrOne("P")) : 0;
}

function p2o5FromPo4(mgPO4) {
  if (!mgPO4) {
    return 0;
  }
  const mgP = (mgPO4 * getMolarMassOrOne("P")) / getMolarMassOrOne("PO4");
  return p2o5FromP(mgP);
}

function so4FromS(mgS) {
  return mgS ? (mgS * getMolarMassOrOne("SO4")) / getMolarMassOrOne("S") : 0;
}

function k2oFromK(mgK) {
  return mgK ? (mgK * getMolarMassOrOne("K2O")) / (2 * getMolarMassOrOne("K")) : 0;
}

function na2oFromNa(mgNa) {
  return mgNa ? (mgNa * getMolarMassOrOne("Na2O")) / (2 * getMolarMassOrOne("Na")) : 0;
}

function caoFromCa(mgCa) {
  return mgCa ? (mgCa * getMolarMassOrOne("CaO")) / getMolarMassOrOne("Ca") : 0;
}

function mgoFromMg(mgMg) {
  return mgMg ? (mgMg * getMolarMassOrOne("MgO")) / getMolarMassOrOne("Mg") : 0;
}

function po4FromP2o5(mgP2o5) {
  return mgP2o5 ? (mgP2o5 * 2 * getMolarMassOrOne("PO4")) / getMolarMassOrOne("P2O5") : 0;
}

function kFromK2o(mgK2O) {
  return mgK2O ? (mgK2O * 2 * getMolarMassOrOne("K")) / getMolarMassOrOne("K2O") : 0;
}

function caFromCao(mgCaO) {
  return mgCaO ? (mgCaO * getMolarMassOrOne("Ca")) / getMolarMassOrOne("CaO") : 0;
}

function mgFromMgo(mgMgO) {
  return mgMgO ? (mgMgO * getMolarMassOrOne("Mg")) / getMolarMassOrOne("MgO") : 0;
}

function naFromNa2o(mgNa2O) {
  return mgNa2O ? (mgNa2O * 2 * getMolarMassOrOne("Na")) / getMolarMassOrOne("Na2O") : 0;
}

function normalizeWaterValues(rawValues, osmosisPercent) {
  const factor = 1 - clamp(osmosisPercent, 0, 100) / 100;
  return normalizeWaterValuesWithFactor(rawValues, factor);
}

function normalizeWaterValuesWithFactor(rawValues, factor) {
  const normalized = {};
  const hco3Direct = rawValues.HCO3 || 0;
  const useDerivedHco3 = hco3Direct === 0;

  const add = (key, value) => {
    if (!Number.isFinite(value) || value === 0) {
      return;
    }
    normalized[key] = (normalized[key] || 0) + value * factor;
  };

  const hco3FromCaco3 = hco3FromCaco3Value;
  const hco3FromKh = hco3FromKhValue;

  add("NH4", (rawValues.NH4 || 0) + (rawValues.NH3 || 0));
  add("NO3", (rawValues.NO3 || 0) + (rawValues.NO2 || 0));
  add("P2O5", p2o5FromPo4(rawValues.PO4 || 0));
  add("P2O5", p2o5FromP(rawValues.P || 0));
  add("SO4", (rawValues.SO4 || 0) + so4FromS(rawValues.S || 0));
  add("K2O", k2oFromK(rawValues.K || 0));
  add("Na2O", na2oFromNa(rawValues.Na || 0));
  add("CaO", caoFromCa(rawValues.Ca || 0));
  add("MgO", mgoFromMg(rawValues.Mg || 0));
  add("Cl", rawValues.Cl || 0);
  add("Fe", rawValues.Fe || 0);
  add("Mn", rawValues.Mn || 0);
  add("Cu", rawValues.Cu || 0);
  add("Zn", rawValues.Zn || 0);
  add("B", rawValues.B || 0);
  add("Mo", rawValues.Mo || 0);
  if (useDerivedHco3) {
    add("HCO3", hco3FromCaco3(rawValues.CaCO3 || 0) + hco3FromKh(rawValues.KH || 0));
  } else {
    add("HCO3", hco3Direct);
  }
  add("SiO2", rawValues.SiO2 || 0);

  return normalized;
}

function buildWaterPayloadFromValues(rawValues) {
  return normalizeWaterValuesWithFactor(rawValues, 1);
}

function buildWaterPayloadForApi(rawValues) {
  const waterPayload = { ...buildWaterPayloadFromValues(rawValues) };
  delete waterPayload.KH;
  delete waterPayload.CaCO3;
  delete waterPayload.CO3;
  return waterPayload;
}

function computeWaterElements(normalizedWater) {
  const elements = {};

  const nh4 = normalizedWater.NH4 || 0;
  const no3 = normalizedWater.NO3 || 0;
  const nFromNh4 = nh4 ? (nh4 * getMolarMassOrOne("N")) / getMolarMassOrOne("NH4") : 0;
  const nFromNo3 = no3 ? (no3 * getMolarMassOrOne("N")) / getMolarMassOrOne("NO3") : 0;
  elements.N_total = nFromNh4 + nFromNo3;

  const p2o5 = normalizedWater.P2O5 || 0;
  if (p2o5) {
    elements.P = (p2o5 * 2 * getMolarMassOrOne("P")) / getMolarMassOrOne("P2O5");
  }

  const k2o = normalizedWater.K2O || 0;
  if (k2o) {
    elements.K = (k2o * 2 * getMolarMassOrOne("K")) / getMolarMassOrOne("K2O");
  }

  const cao = normalizedWater.CaO || 0;
  if (cao) {
    elements.Ca = (cao * getMolarMassOrOne("Ca")) / getMolarMassOrOne("CaO");
  }

  const mgo = normalizedWater.MgO || 0;
  if (mgo) {
    elements.Mg = (mgo * getMolarMassOrOne("Mg")) / getMolarMassOrOne("MgO");
  }

  const na2o = normalizedWater.Na2O || 0;
  if (na2o) {
    elements.Na = (na2o * 2 * getMolarMassOrOne("Na")) / getMolarMassOrOne("Na2O");
  }

  const so4 = normalizedWater.SO4 || 0;
  if (so4) {
    elements.S = (so4 * getMolarMassOrOne("S")) / getMolarMassOrOne("SO4");
  }

  ["Cl", "Fe", "Mn", "Cu", "Zn", "B", "Mo"].forEach((key) => {
    if (normalizedWater[key]) {
      elements[key] = normalizedWater[key];
    }
  });

  if (normalizedWater.HCO3) {
    elements.HCO3 = normalizedWater.HCO3;
  }

  const sio2 = normalizedWater.SiO2 || 0;
  if (sio2) {
    elements.Si = (sio2 * getMolarMassOrOne("Si")) / getMolarMassOrOne("SiO2");
  }

  return elements;
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
    converted[key] = molarMass ? value / 1000 / molarMass : value;
  });
  return converted;
}

function buildPayload() {
  const fertilizers = selectedFertilizers
    .map((fert, index) => ({ name: fert.name, grams: fertilizerAmounts[index] }))
    .filter((entry) => entry.name && entry.grams > 0);

  const waterPayload = buildWaterPayloadForApi(waterValues);

  return {
    liters: 10.0,
    fertilizers,
    water_mg_l: waterPayload,
    osmosis_percent: Number(osmosisPercentInput.value) || 0,
  };
}

async function fetchJson(url, errorMessage) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(errorMessage);
  }
  return response.json();
}

function fetchFertilizers() {
  return fetchJson(`${apiBase()}/fertilizers`, "Fehler beim Laden der Dünger-Liste");
}

function fetchMolarMasses() {
  return fetchJson(`${apiBase()}/molar-masses`, "Fehler beim Laden der Molmassen");
}

function fetchWaterProfiles() {
  return fetchJson(`${apiBase()}/water-profiles`, "Fehler beim Laden der Wasserprofile");
}

function fetchWaterProfileData(filename) {
  return fetchJson(
    `${apiBase()}/water-profiles/${encodeURIComponent(filename)}`,
    "Fehler beim Laden des Wasserprofils"
  );
}

async function saveWaterProfile() {
  const name = waterProfileNameInput.value.trim();
  if (!name) {
    alert("Bitte einen Profilnamen angeben.");
    return;
  }
  const waterPayload = buildWaterPayloadForApi(waterValues);
  const payload = {
    name,
    source: "Horticalc UI",
    mg_per_l: waterPayload,
    osmosis_percent: Number(osmosisPercentInput.value) || 0,
  };
  const response = await fetch(`${apiBase()}/water-profiles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Speichern fehlgeschlagen");
  }
}

function fetchDefaultRecipe() {
  return fetchJson(`${apiBase()}/recipes/default`, "Fehler beim Laden des Default-Rezepts");
}

async function calculate() {
  const payload = buildPayload();
  const response = await fetch(`${apiBase()}/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Berechnung fehlgeschlagen");
  }

  return response.json();
}

function renderCalculation(data) {
  lastCalculation = data;
  const oxides = data.oxides_mg_per_l || {};
  const elements = data.elements_mg_per_l || {};
  const npkMetrics = data.npk_metrics || {};
  const waterElements = data.water_elements_mg_per_l || {};
  const waterDisplay = waterElementsForDisplay(waterElements);
  renderSummaryTable(summaryTable, oxides, elements, waterDisplay);

  const ionMeqEntries = Object.entries(data.ions_meq_per_l || {});
  renderIonCompactList(ionMeqList, ionMeqEntries);

  const ionBalanceEntries = Object.entries(data.ion_balance || {});
  renderIonBalanceCompact(ionBalanceList, ionBalanceEntries);

  npkAllPctValue.textContent = npkMetrics.npk_all_pct || "-";
  npkPNormValue.textContent = npkMetrics.npk_p_norm || "-";
  npkNpkPctValue.textContent = npkMetrics.npk_npk_pct || "-";

  const ec = data.ec || {};
  const ecValues = ec.ec_mS_per_cm || {};
  const ec18 = Number(ecValues["18.0"]);
  const ec25 = Number(ecValues["25.0"]);
  ec18Value.textContent = Number.isFinite(ec18) ? formatNumber(ec18) : "-";
  ec25Value.textContent = Number.isFinite(ec25) ? formatNumber(ec25) : "-";

  const waterEc = data.ec_water || {};
  const waterEcValues = waterEc.ec_mS_per_cm || {};
  const water18 = Number(waterEcValues["18.0"]);
  const water25 = Number(waterEcValues["25.0"]);
  ecWater18Value.textContent = Number.isFinite(water18) ? formatNumber(water18) : "-";
  ecWater25Value.textContent = Number.isFinite(water25) ? formatNumber(water25) : "-";
}

function applyRecipe(recipe) {
  const fertilizers = Array.isArray(recipe.fertilizers) ? recipe.fertilizers : [];
  selectedFertilizers.length = 0;
  fertilizerAmounts.length = 0;

  fertilizers.forEach((entry) => {
    const name = entry.name || "";
    const match = fertilizerOptions.find((opt) => opt.name === name);
    selectedFertilizers.push({
      name,
      form: match ? match.form : "",
      weight: match ? match.weight_factor : "",
    });
    fertilizerAmounts.push(Number(entry.grams) || 0);
  });

  if (!selectedFertilizers.length) {
    selectedFertilizers.push({ name: "", form: "", weight: "" });
    fertilizerAmounts.push(0);
  }

  renderSelectionTable();
  renderCalculatorTable();
}

function applyWaterProfile(profile) {
  const mg = profile.mg_per_l || {};
  const hco3Direct = mg.HCO3 || 0;
  const derivedHco3 = hco3Direct ? 0 : hco3FromCaco3Value(mg.CaCO3 || 0) + hco3FromKhValue(mg.KH || 0);

  waterFieldDefinitions.forEach((field) => {
    waterValues[field.key] = 0;
  });

  waterValues.NH4 = mg.NH4 || 0;
  waterValues.NH3 = mg.NH3 || 0;
  waterValues.NO3 = mg.NO3 || 0;
  waterValues.NO2 = mg.NO2 || 0;

  if (mg.PO4) {
    waterValues.PO4 = mg.PO4;
  } else if (mg.P2O5) {
    waterValues.PO4 = po4FromP2o5(mg.P2O5);
  }
  waterValues.P = mg.P || 0;

  waterValues.SO4 = mg.SO4 || 0;
  waterValues.S = mg.S || 0;

  waterValues.K = mg.K || kFromK2o(mg.K2O || 0);
  waterValues.Ca = mg.Ca || caFromCao(mg.CaO || 0);
  waterValues.Mg = mg.Mg || mgFromMgo(mg.MgO || 0);
  waterValues.Na = mg.Na || naFromNa2o(mg.Na2O || 0);

  waterValues.Cl = mg.Cl || 0;
  waterValues.HCO3 = hco3Direct || derivedHco3;
  waterValues.CO3 = 0;
  waterValues.Fe = mg.Fe || 0;
  waterValues.Mn = mg.Mn || 0;
  waterValues.Cu = mg.Cu || 0;
  waterValues.Zn = mg.Zn || 0;
  waterValues.B = mg.B || 0;
  waterValues.Mo = mg.Mo || 0;
  waterValues.CaCO3 = 0;
  waterValues.KH = 0;
  waterValues.SiO2 = mg.SiO2 || 0;

  waterProfileNameInput.value = profile.name || "";
  osmosisPercentInput.value = profile.osmosis_percent ?? 0;
  renderWaterTable();
}

function addFertilizerRow() {
  selectedFertilizers.push({ name: "", form: "", weight: "" });
  fertilizerAmounts.push(0);
  renderSelectionTable();
  renderCalculatorTable();
}

function removeFertilizerRow() {
  if (selectedFertilizers.length <= 1) {
    return;
  }

  selectedFertilizers.pop();
  fertilizerAmounts.pop();
  renderSelectionTable();
  renderCalculatorTable();
}

function renderWaterProfileOptions() {
  waterProfileSelect.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "-- auswählen --";
  waterProfileSelect.appendChild(empty);

  waterProfiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.filename;
    option.textContent = profile.name || profile.filename;
    waterProfileSelect.appendChild(option);
  });
}

async function init() {
  try {
    fertilizerOptions = await fetchFertilizers();
  } catch (error) {
    alert(error.message);
    fertilizerOptions = [];
  }

  try {
    molarMasses = await fetchMolarMasses();
  } catch (error) {
    alert(error.message);
    molarMasses = {};
  }

  try {
    waterProfiles = await fetchWaterProfiles();
  } catch (error) {
    alert(error.message);
    waterProfiles = [];
  }

  renderWaterProfileOptions();

  try {
    const defaultProfile = await fetchWaterProfileData("default");
    applyWaterProfile(defaultProfile);
  } catch (error) {
    renderWaterTable();
  }

  try {
    const recipe = await fetchDefaultRecipe();
    applyRecipe(recipe);
    const data = await calculate();
    renderCalculation(data);
  } catch (error) {
    renderSelectionTable();
    renderCalculatorTable();
    renderSummaryTable(summaryTable, {}, {}, {});
  }
}

reloadButton.addEventListener("click", init);
addRowButton.addEventListener("click", addFertilizerRow);
removeRowButton.addEventListener("click", removeFertilizerRow);
calculateButton.addEventListener("click", async () => {
  try {
    const data = await calculate();
    renderCalculation(data);
  } catch (error) {
    alert(error.message);
  }
});

loadWaterProfileButton.addEventListener("click", async () => {
  const selection = waterProfileSelect.value;
  if (!selection) {
    alert("Bitte ein Wasserprofil auswählen.");
    return;
  }
  try {
    const profile = await fetchWaterProfileData(selection);
    applyWaterProfile(profile);
  } catch (error) {
    alert(error.message);
  }
});

resetWaterProfileButton.addEventListener("click", async () => {
  try {
    const profile = await fetchWaterProfileData("default");
    applyWaterProfile(profile);
  } catch (error) {
    alert(error.message);
  }
});

saveWaterProfileButton.addEventListener("click", async () => {
  try {
    await saveWaterProfile();
    waterProfiles = await fetchWaterProfiles();
    renderWaterProfileOptions();
  } catch (error) {
    alert(error.message);
  }
});

osmosisPercentInput.addEventListener("input", () => {
  scheduleRecalculate();
});

waterUnitToggle.addEventListener("change", (event) => {
  waterUnit = event.target.checked ? "mol_l" : "mg_l";
  renderWaterTable();
  scheduleRecalculate();
});

toggleWaterValuesButton.addEventListener("click", () => {
  const isCollapsed = waterContent.classList.toggle("is-collapsed");
  toggleWaterValuesButton.textContent = isCollapsed ? "Wasserwerte anzeigen" : "Wasserwerte ausblenden";
});

initializeFertilizerTables();
init();
