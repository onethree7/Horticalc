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
const profileSectionTitle = document.querySelector("#profileSectionTitle");
const profileSectionHint = document.querySelector("#profileSectionHint");
const profileSection = document.querySelector("#profileSection");
const profileSelect = document.querySelector("#profileSelect");
const loadProfileButton = document.querySelector("#loadProfile");
const resetProfileButton = document.querySelector("#resetProfile");
const profileNameInput = document.querySelector("#profileName");
const saveProfileButton = document.querySelector("#saveProfile");
const solverProfileActions = document.querySelector("#solverProfileActions");
const saveSolverAsRecipeButton = document.querySelector("#saveSolverAsRecipe");
const applySolverToCalculatorButton = document.querySelector("#applySolverToCalculator");
const applyScaleToCalcLiters = document.querySelector("#applyScaleToCalcLiters");

const waterSummaryTable = document.querySelector("#waterSummaryTable");
const oxideSummaryTable = document.querySelector("#oxideSummaryTable");
const ionSummaryTable = document.querySelector("#ionSummaryTable");
const waterSummaryBadge = document.querySelector("#waterSummaryBadge");
const ionMeqList = document.querySelector("#ionMeqList");
const ionBalanceList = document.querySelector("#ionBalanceList");
const modeToggleInputs = document.querySelectorAll('input[name="modeToggle"]');
const calculatorMode = document.querySelector("#calculatorMode");
const solverMode = document.querySelector("#solverMode");
const fertilizerEditorMode = document.querySelector("#fertilizerEditorMode");
const solverTargetsTable = document.querySelector("#solverTargetsTable tbody");
const solverAllowedFertilizersSelect = document.querySelector("#solverAllowedFertilizers");
const solverFixedTable = document.querySelector("#solverFixedTable tbody");
const solverFertilizersTable = document.querySelector("#solverFertilizersTable tbody");
const solverTargetsResultsTable = document.querySelector("#solverTargetsResultsTable tbody");
const solveButton = document.querySelector("#solveBtn");
const solverLitersInput = document.querySelector("#solverLiters");
const solverUreaToggle = document.querySelector("#solverUreaToggle");
const solverPhosphateSelect = document.querySelector("#solverPhosphate");
const fertilizerEditorTableWrap = document.querySelector("#fertilizerEditorTableWrap");
const fertEditorSearchInput = document.querySelector("#fertEditorSearch");
const fertEditorAddRowButton = document.querySelector("#fertEditorAddRow");
const fertEditorDeleteRowButton = document.querySelector("#fertEditorDeleteRow");
const fertEditorLoadButton = document.querySelector("#fertEditorLoad");
const fertEditorSaveButton = document.querySelector("#fertEditorSave");

const CALC_LITERS = 10.0;

let fertilizerOptions = [];
const selectedFertilizers = [{ name: "", form: "", weight: "" }];
const fertilizerAmounts = [0];
let molarMasses = {};
let waterProfiles = [];
let recipeProfiles = [];
let nutrientSolutions = [];
let waterUnit = "mg_l";
let lastCalculation = null;
let lastSolveResult = null;
let recalculateTimer = null;
let fertilizerSelectTable;
let calculatorTable;
let currentProfileMode = "calculator";
let activeMode = "calculator";
let fertilizerEditorRows = [];
let fertilizerEditorSelectedIndex = 0;
let fertilizerEditorFilter = "";
let fertilizerEditorTable;
let fertilizerEditorCompKeys = [];

const fertilizerEditorPreferredKeys = [
  "NO3",
  "NH4",
  "Ur-N",
  "P2O5",
  "K2O",
  "CaO",
  "MgO",
  "SO4",
  "Fe",
  "Mn",
  "Cu",
  "Zn",
  "B",
  "Mo",
  "SiO2",
  "Na2O",
  "Cl",
  "CO3",
  "HCO3",
];

const solverTargetDefinitions = [
  { key: "N_total", label: "N_total" },
  { key: "N_NH4", label: "N_NH4" },
  { key: "N_NO3", label: "N_NO3" },
  { key: "N_UREA", label: "N_UREA" },
  { key: "P", label: "P" },
  { key: "K", label: "K" },
  { key: "Ca", label: "Ca" },
  { key: "Mg", label: "Mg" },
  { key: "S", label: "S" },
  { key: "SO4", label: "SO4" },
  { key: "Fe", label: "Fe" },
  { key: "Mn", label: "Mn" },
  { key: "Cu", label: "Cu" },
  { key: "Zn", label: "Zn" },
  { key: "B", label: "B" },
  { key: "Mo", label: "Mo" },
  { key: "Si", label: "Si" },
  { key: "Cl", label: "Cl" },
  { key: "Na", label: "Na" },
  { key: "HCO3", label: "HCO3" },
];

const solverTargetValues = Object.fromEntries(
  solverTargetDefinitions.map((field) => [field.key, 0])
);
const solverAllowedFertilizers = [];
const solverFixedGrams = {};
const saveAllowedFertilizersDebounced = debounce(() => {
  lsSet(LAST_FERTILIZERS_ALLOWED_KEY, solverAllowedFertilizers);
}, 200);

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
const numberFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
  useGrouping: false,
});
const nutrientFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
  useGrouping: false,
});
const ionFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  useGrouping: false,
});
const nutrientIntegerFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
  useGrouping: false,
});
const LAST_FERTILIZERS_ALLOWED_KEY = "last_fertilizers_allowed";
const LAST_SOLUTION_CALCULATED_KEY = "last_solution_calculated";
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
  { oxide: "N_total", element: "N_total", oxideHeaderLabel: "N_total", ionHeaderLabel: "N_total" },
  { oxide: "P2O5", element: "P", oxideHeaderLabel: "P2O5", ionHeaderLabel: "P" },
  { oxide: "K2O", element: "K", oxideHeaderLabel: "K2O", ionHeaderLabel: "K" },
  { oxide: "CaO", element: "Ca", oxideHeaderLabel: "CaO", ionHeaderLabel: "Ca" },
  { oxide: "MgO", element: "Mg", oxideHeaderLabel: "MgO", ionHeaderLabel: "Mg" },
  { oxide: "SO4", element: "S", oxideHeaderLabel: "SO4", ionHeaderLabel: "S" },
  { oxide: "Fe", element: "Fe", oxideHeaderLabel: "Fe", ionHeaderLabel: "Fe" },
  { oxide: "Mn", element: "Mn", oxideHeaderLabel: "Mn", ionHeaderLabel: "Mn" },
  { oxide: "Cu", element: "Cu", oxideHeaderLabel: "Cu", ionHeaderLabel: "Cu" },
  { oxide: "Zn", element: "Zn", oxideHeaderLabel: "Zn", ionHeaderLabel: "Zn" },
  { oxide: "B", element: "B", oxideHeaderLabel: "B", ionHeaderLabel: "B" },
  { oxide: "Mo", element: "Mo", oxideHeaderLabel: "Mo", ionHeaderLabel: "Mo" },
  { oxide: "SiO2", element: "Si", oxideHeaderLabel: "SiO2", ionHeaderLabel: "Si" },
  { oxide: "Na2O", element: "Na", oxideHeaderLabel: "Na2O", ionHeaderLabel: "Na" },
  { oxide: "Cl", element: "Cl", oxideHeaderLabel: "Cl", ionHeaderLabel: "Cl" },
  { oxide: "HCO3", element: "HCO3", oxideHeaderLabel: "HCO3", ionHeaderLabel: "HCO3" },
];
const summaryLabelWidth = "12rem";

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
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

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), ms);
  };
}

function parseDecimalInput(raw) {
  const s = String(raw ?? "").trim();
  if (!s) {
    return null;
  }
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
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

function setMode(mode) {
  const isSolver = mode === "solver";
  const isEditor = mode === "fertilizers";
  calculatorMode.classList.toggle("is-hidden", isSolver || isEditor);
  solverMode.classList.toggle("is-hidden", !isSolver);
  fertilizerEditorMode.classList.toggle("is-hidden", !isEditor);
  profileSection.classList.toggle("is-hidden", isEditor);
  activeMode = mode;
  if (!isEditor) {
    setProfileMode(mode);
  }
}

const profileConfigs = {
  calculator: {
    title: "Recipe",
    hint: "Recipe lokal speichern/laden.",
  },
  solver: {
    title: "Nutrient Solution",
    hint: "Nutrient Solution lokal speichern/laden.",
  },
};

function setProfileMode(mode) {
  currentProfileMode = mode === "solver" ? "solver" : "calculator";
  const config = profileConfigs[currentProfileMode];
  profileSectionTitle.textContent = config.title;
  profileSectionHint.textContent = config.hint;
  solverProfileActions.classList.toggle("is-hidden", currentProfileMode !== "solver");
  renderProfileOptions();
}

function renderProfileOptions() {
  profileSelect.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "-- auswählen --";
  profileSelect.appendChild(empty);

  const profiles = currentProfileMode === "solver" ? nutrientSolutions : recipeProfiles;
  profiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.filename;
    option.textContent = profile.name || profile.filename;
    profileSelect.appendChild(option);
  });
}

function renderSolverTargetsTable() {
  solverTargetsTable.innerHTML = "";
  solverTargetDefinitions.forEach((field) => {
    const row = document.createElement("tr");

    const labelCell = document.createElement("td");
    labelCell.textContent = field.label;

    const valueCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.step = "0.1";
    input.value = solverTargetValues[field.key] || 0;
    input.addEventListener("input", (event) => {
      solverTargetValues[field.key] = Number(event.target.value) || 0;
    });
    valueCell.appendChild(input);

    row.append(labelCell, valueCell);
    solverTargetsTable.appendChild(row);
  });
}

function buildFertilizerCompKeys(fertilizers) {
  const keySet = new Set();
  fertilizers.forEach((fert) => {
    Object.keys(fert.comp || {}).forEach((key) => {
      keySet.add(key);
    });
  });
  const ordered = [];
  fertilizerEditorPreferredKeys.forEach((key) => {
    if (keySet.has(key)) {
      ordered.push(key);
      keySet.delete(key);
    }
  });
  ordered.push(...Array.from(keySet).sort((a, b) => a.localeCompare(b)));
  return ordered;
}

function setFertilizerEditorData(fertilizers) {
  fertilizerEditorRows = (fertilizers || []).map((fert) => ({
    name: fert.name || "",
    form: fert.form || "",
    weight_factor: Number.isFinite(fert.weight_factor) ? fert.weight_factor : null,
    comp: { ...(fert.comp || {}) },
  }));
  fertilizerEditorSelectedIndex = 0;
  fertilizerEditorCompKeys = buildFertilizerCompKeys(fertilizerEditorRows);
  renderFertilizerEditor();
}

function focusEditorInput(rowIndex, field, compKey) {
  if (!fertilizerEditorTableWrap) {
    return;
  }
  let selector = `input[data-row-index="${rowIndex}"][data-field="${field}"]`;
  if (compKey) {
    selector += `[data-comp-key="${compKey}"]`;
  }
  const input = fertilizerEditorTableWrap.querySelector(selector);
  if (input) {
    input.focus();
  }
}

function setSelectedEditorRow(editorIndex) {
  fertilizerEditorSelectedIndex = editorIndex;
  if (!fertilizerEditorTable) {
    return;
  }
  const rows = Array.from(fertilizerEditorTable.querySelectorAll("tr[data-editor-index]"));
  rows.forEach((row) => {
    row.classList.toggle("is-selected", Number(row.dataset.editorIndex) === editorIndex);
  });
}

function handleEditorEnterKey(event) {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  const input = event.target;
  const colIndex = Number(input.dataset.colIndex);
  const row = input.closest("tr");
  if (!row || Number.isNaN(colIndex)) {
    return;
  }
  const nextInRow = row.querySelector(`input[data-col-index="${colIndex + 1}"]`);
  if (nextInRow) {
    nextInRow.focus();
    return;
  }
  const nextRow = row.nextElementSibling;
  if (!nextRow) {
    return;
  }
  const nextRowInput = nextRow.querySelector(`input[data-col-index="${colIndex}"]`);
  if (nextRowInput) {
    nextRowInput.focus();
  }
}

function renderFertilizerEditor() {
  if (!fertilizerEditorTableWrap) {
    return;
  }
  fertilizerEditorTableWrap.innerHTML = "";

  fertilizerEditorCompKeys = buildFertilizerCompKeys(fertilizerEditorRows);
  const colgroupClasses = [
    "col-index",
    "col-name",
    "col-form",
    "col-weight",
    ...fertilizerEditorCompKeys.map(() => "col-nutrient"),
  ];
  const headerCells = [
    { label: "#" },
    { label: "Düngername" },
    { label: "Form" },
    { label: "Gewicht" },
    ...fertilizerEditorCompKeys.map((key) => ({ label: key })),
  ];
  const table = createTable({
    id: "fertilizerEditorTable",
    className: "grid grid--form grid--fertilizer grid--fertilizer-editor",
    colgroupClasses,
    headerCells,
  });
  fertilizerEditorTableWrap.appendChild(table.table);
  fertilizerEditorTable = table.table;

  const filterValue = fertilizerEditorFilter.trim().toLowerCase();
  const filteredRows = fertilizerEditorRows
    .map((row, index) => ({ row, index }))
    .filter(({ row }) => {
      if (!filterValue) {
        return true;
      }
      return row.name.toLowerCase().includes(filterValue);
    });

  if (filteredRows.length) {
    const stillVisible = filteredRows.some(({ index }) => index === fertilizerEditorSelectedIndex);
    if (!stillVisible) {
      fertilizerEditorSelectedIndex = filteredRows[0].index;
    }
  }

  filteredRows.forEach(({ row, index }, visibleIndex) => {
    const tr = document.createElement("tr");
    tr.dataset.editorIndex = index;
    tr.classList.toggle("is-selected", index === fertilizerEditorSelectedIndex);
    tr.addEventListener("click", () => setSelectedEditorRow(index));

    const indexCell = document.createElement("td");
    indexCell.textContent = String(visibleIndex + 1);
    tr.appendChild(indexCell);

    let colIndex = 0;
    const nameCell = document.createElement("td");
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.value = row.name;
    nameInput.dataset.rowIndex = index;
    nameInput.dataset.field = "name";
    nameInput.dataset.colIndex = colIndex;
    nameInput.addEventListener("input", (event) => {
      row.name = event.target.value;
    });
    nameInput.addEventListener("keydown", handleEditorEnterKey);
    nameCell.appendChild(nameInput);
    tr.appendChild(nameCell);
    colIndex += 1;

    const formCell = document.createElement("td");
    const formInput = document.createElement("input");
    formInput.type = "text";
    formInput.value = row.form || "";
    formInput.dataset.rowIndex = index;
    formInput.dataset.field = "form";
    formInput.dataset.colIndex = colIndex;
    formInput.addEventListener("input", (event) => {
      row.form = event.target.value;
    });
    formInput.addEventListener("keydown", handleEditorEnterKey);
    formCell.appendChild(formInput);
    tr.appendChild(formCell);
    colIndex += 1;

    const weightCell = document.createElement("td");
    const weightInput = document.createElement("input");
    weightInput.type = "text";
    weightInput.inputMode = "decimal";
    weightInput.value = Number.isFinite(row.weight_factor)
      ? formatNumber(row.weight_factor, nutrientFormatter)
      : "";
    weightInput.dataset.rowIndex = index;
    weightInput.dataset.field = "weight_factor";
    weightInput.dataset.colIndex = colIndex;
    weightInput.addEventListener("input", (event) => {
      row.weight_factor = parseDecimalInput(event.target.value);
    });
    weightInput.addEventListener("keydown", handleEditorEnterKey);
    weightCell.appendChild(weightInput);
    tr.appendChild(weightCell);
    colIndex += 1;

    fertilizerEditorCompKeys.forEach((key) => {
      const cell = document.createElement("td");
      const input = document.createElement("input");
      input.type = "text";
      input.inputMode = "decimal";
      const value = row.comp?.[key];
      input.value = Number.isFinite(value) ? formatNumber(value * 100, nutrientFormatter) : "";
      input.dataset.rowIndex = index;
      input.dataset.field = "comp";
      input.dataset.compKey = key;
      input.dataset.colIndex = colIndex;
      input.addEventListener("input", (event) => {
        const parsed = parseDecimalInput(event.target.value);
        if (!row.comp) {
          row.comp = {};
        }
        if (parsed === null) {
          delete row.comp[key];
        } else {
          row.comp[key] = parsed / 100;
        }
      });
      input.addEventListener("keydown", handleEditorEnterKey);
      cell.appendChild(input);
      tr.appendChild(cell);
      colIndex += 1;
    });

    table.tbody.appendChild(tr);
  });
}

async function putFertilizers(payload) {
  const response = await fetch(`${apiBase()}/fertilizers`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Speichern fehlgeschlagen");
  }
}

async function saveFertilizerEditor() {
  const payload = [];
  const seen = new Set();
  for (let index = 0; index < fertilizerEditorRows.length; index += 1) {
    const row = fertilizerEditorRows[index];
    const name = row.name.trim();
    if (!name) {
      reportError(null, "Bitte einen Düngernamen angeben.");
      focusEditorInput(index, "name");
      return;
    }
    if (seen.has(name)) {
      reportError(null, "Düngernamen müssen eindeutig sein.");
      focusEditorInput(index, "name");
      return;
    }
    seen.add(name);

    const form = row.form.trim() || "fest";
    const weight = Number.isFinite(row.weight_factor) ? row.weight_factor : 1.0;
    const comp = {};
    Object.entries(row.comp || {}).forEach(([key, value]) => {
      if (Number.isFinite(value) && value > 0) {
        comp[key] = value;
      }
    });
    payload.push({
      name,
      form,
      weight_factor: weight,
      comp,
    });
  }
  try {
    await putFertilizers(payload);
    const previousMode = activeMode;
    await init();
    if (previousMode === "fertilizers") {
      setMode("fertilizers");
    }
  } catch (error) {
    reportError(error, "Speichern fehlgeschlagen");
  }
}

async function reloadFertilizerEditor() {
  try {
    fertilizerOptions = await fetchFertilizers();
    setFertilizerEditorData(fertilizerOptions);
    renderSelectionTable();
    renderCalculatorTable();
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  } catch (error) {
    reportError(error, "Fehler beim Laden der Dünger-Liste");
  }
}

function addFertilizerEditorRow() {
  fertilizerEditorRows.push({ name: "", form: "", weight_factor: null, comp: {} });
  fertilizerEditorSelectedIndex = fertilizerEditorRows.length - 1;
  renderFertilizerEditor();
  focusEditorInput(fertilizerEditorSelectedIndex, "name");
}

function deleteFertilizerEditorRow() {
  if (!fertilizerEditorRows.length) {
    return;
  }
  fertilizerEditorRows.splice(fertilizerEditorSelectedIndex, 1);
  if (fertilizerEditorSelectedIndex >= fertilizerEditorRows.length) {
    fertilizerEditorSelectedIndex = Math.max(0, fertilizerEditorRows.length - 1);
  }
  renderFertilizerEditor();
}

function renderSolverAllowedOptions() {
  solverAllowedFertilizersSelect.innerHTML = "";
  fertilizerOptions.forEach((fert) => {
    const option = document.createElement("option");
    option.value = fert.name;
    option.textContent = fert.name;
    if (solverAllowedFertilizers.includes(fert.name)) {
      option.selected = true;
    }
    solverAllowedFertilizersSelect.appendChild(option);
  });
}

function renderSolverFixedTable() {
  solverFixedTable.innerHTML = "";
  solverAllowedFertilizers.forEach((name) => {
    const row = document.createElement("tr");

    const nameCell = document.createElement("td");
    nameCell.textContent = name;

    const valueCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.step = "0.01";
    input.value = solverFixedGrams[name] || 0;
    input.addEventListener("input", (event) => {
      solverFixedGrams[name] = Number(event.target.value) || 0;
    });
    valueCell.appendChild(input);

    row.append(nameCell, valueCell);
    solverFixedTable.appendChild(row);
  });
}

function renderSolverResults(data) {
  lastSolveResult = data || null;
  updateSolverResultActions();
  solverFertilizersTable.innerHTML = "";
  solverTargetsResultsTable.innerHTML = "";

  const fertilizers = Array.isArray(data?.fertilizers) ? data.fertilizers : [];
  if (!fertilizers.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 2;
    cell.textContent = "Keine Dünger berechnet";
    row.appendChild(cell);
    solverFertilizersTable.appendChild(row);
  } else {
    fertilizers.forEach((fert) => {
      const row = document.createElement("tr");
      const nameCell = document.createElement("td");
      nameCell.textContent = fert.name;
      const gramsCell = document.createElement("td");
      gramsCell.textContent = formatNumber(Number(fert.grams), nutrientFormatter);
      row.append(nameCell, gramsCell);
      solverFertilizersTable.appendChild(row);
    });
  }

  const targets = data?.targets_mg_per_l || {};
  const achieved = data?.achieved_elements_mg_per_l || {};
  const errors = data?.errors_mg_per_l || {};
  const errorsPercent = data?.errors_percent || {};
  const keys = data?.objective_elements?.length
    ? data.objective_elements
    : Object.keys(targets);

  keys.forEach((key) => {
    const row = document.createElement("tr");
    const keyCell = document.createElement("td");
    keyCell.textContent = key;

    const targetCell = document.createElement("td");
    targetCell.textContent = formatNumber(Number(targets[key]), nutrientFormatter);

    const achievedCell = document.createElement("td");
    achievedCell.textContent = formatNumber(Number(achieved[key]), nutrientFormatter);

    const deltaCell = document.createElement("td");
    deltaCell.textContent = formatNumber(Number(errors[key]), nutrientFormatter);

    const percentCell = document.createElement("td");
    const percent = Number(errorsPercent[key]);
    percentCell.textContent = Number.isFinite(percent) ? `${percent.toFixed(1)}%` : "-";

    row.append(keyCell, targetCell, achievedCell, deltaCell, percentCell);
    solverTargetsResultsTable.appendChild(row);
  });
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
      updateHco3FromHelper(field.key);
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

function reportError(error, fallbackMessage = "Unbekannter Fehler") {
  const message = error?.message || fallbackMessage;
  alert(message);
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
      reportError(error, "Berechnung fehlgeschlagen");
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

function buildSummaryColgroup() {
  const colgroup = document.createElement("colgroup");
  const labelCol = document.createElement("col");
  labelCol.classList.add("col-row-label");
  labelCol.style.width = summaryLabelWidth;
  colgroup.appendChild(labelCol);
  summaryColumnOrder.forEach((column) => {
    const col = document.createElement("col");
    col.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
    colgroup.appendChild(col);
  });
  return colgroup;
}

function renderSummaryTable({ table, headerLabels, rowLabel, valueMap, valueKey, formatter }) {
  table.innerHTML = "";
  table.appendChild(buildSummaryColgroup());

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const spacer = document.createElement("th");
  spacer.textContent = "";
  headerRow.appendChild(spacer);
  summaryColumnOrder.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = headerLabels(column);
    th.classList.add(`col-${normalizeColumnKey(column.oxide)}`);
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const tr = document.createElement("tr");
  const labelCell = document.createElement("th");
  labelCell.textContent = rowLabel;
  labelCell.classList.add("row-label");
  labelCell.scope = "row";
  tr.appendChild(labelCell);

  summaryColumnOrder.forEach((column) => {
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
    waterSummaryBadge.textContent = waterUnit === "mol_l" ? "mol/L" : "mg/L";
  }
  renderSummaryTable({
    table,
    headerLabels: (column) => column.ionHeaderLabel,
    valueKey: (column) => column.element,
    rowLabel: "Wasserprofil",
    valueMap: waterMap,
    formatter: (column, value) =>
      waterUnit === "mol_l" ? formatTraceValue(value) : formatNutrientValue(column.element, value),
  });
}

function renderOxideSummaryTable(table, oxides) {
  const oxideMap = new Map(Object.entries(oxides || {}));
  renderSummaryTable({
    table,
    headerLabels: (column) => column.oxideHeaderLabel,
    valueKey: (column) => column.oxide,
    rowLabel: "Gesamtansatz",
    valueMap: oxideMap,
    formatter: (column, value) => formatOxideValue(column.oxide, value),
  });
}

function renderIonSummaryTable(table, elements) {
  const elementMap = new Map(Object.entries(elements || {}));
  renderSummaryTable({
    table,
    headerLabels: (column) => column.ionHeaderLabel,
    valueKey: (column) => column.element,
    rowLabel: "Gesamtansatz",
    valueMap: elementMap,
    formatter: (column, value) => formatNutrientValue(column.element, value),
  });
}

function getSummaryTables() {
  return [waterSummaryTable, oxideSummaryTable, ionSummaryTable].filter(Boolean);
}

function assertSharedSummaryScroller() {
  const scroller = document.querySelector("#summaryScroll");
  if (!scroller) {
    return true;
  }
  const ok = getSummaryTables().every((table) => table.closest("#summaryScroll") === scroller);
  if (!ok) {
    console.error("Summary tables are not inside a single shared scroller (#summaryScroll).");
    getSummaryTables().forEach((table) => {
      table.closest(".table-card")?.classList.add("is-align-fail");
    });
    return false;
  }
  return true;
}

function assertSummaryAlignment(tables) {
  const colClassSignature = (table) =>
    Array.from(table.querySelectorAll("colgroup col")).map((col) => col.className).join("|");

  const signatures = tables.map((table) => ({
    table,
    signature: colClassSignature(table),
  }));

  const uniqueSignatures = new Set(signatures.map((entry) => entry.signature));
  if (uniqueSignatures.size <= 1) {
    return true;
  }

  console.error("Summary tables are misaligned.");
  signatures.forEach(({ table }) => {
    const card = table.closest(".table-card");
    if (card) {
      card.classList.add("is-align-fail");
    }
  });
  return false;
}

function assertNoClipping() {
  let isOk = true;

  getSummaryTables().forEach((table) => {
    const card = table.closest(".table-card");
    if (!card) {
      return;
    }
    card.classList.remove("is-align-fail");
    const labelCell = table.querySelector("th.row-label");
    const title = card.querySelector("h3");
    const checkCell = (el) =>
      !el || el.scrollWidth <= el.clientWidth || el.scrollHeight > el.clientHeight;

    const labelOk = checkCell(labelCell);
    const titleOk = checkCell(title);

    if (!labelOk || !titleOk) {
      card.classList.add("is-align-fail");
      console.error("Summary table clipping detected.");
      isOk = false;
    }
  });

  return isOk;
}

window.__horticalcCheckSummaryAlignment = () =>
  assertSharedSummaryScroller() && assertSummaryAlignment(getSummaryTables()) && assertNoClipping();

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

const carbonateHco3Converters = {
  CO3: hco3FromCo3Value,
  CaCO3: hco3FromCaco3Value,
  KH: hco3FromKhValue,
};

function updateHco3FromHelper(key) {
  const converter = carbonateHco3Converters[key];
  if (!converter) {
    return;
  }
  waterValues.HCO3 = converter(waterValues[key] || 0);
  updateWaterInputValue("HCO3");
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

function pFromP2o5(mgP2O5) {
  return mgP2O5 ? (mgP2O5 * 2 * getMolarMassOrOne("P")) / getMolarMassOrOne("P2O5") : 0;
}

function so4FromS(mgS) {
  return mgS ? (mgS * getMolarMassOrOne("SO4")) / getMolarMassOrOne("S") : 0;
}

function sFromSo4(mgSo4) {
  return mgSo4 ? (mgSo4 * getMolarMassOrOne("S")) / getMolarMassOrOne("SO4") : 0;
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

function nFromNh4(mgNh4) {
  return mgNh4 ? (mgNh4 * getMolarMassOrOne("N")) / getMolarMassOrOne("NH4") : 0;
}

function nFromNo3(mgNo3) {
  return mgNo3 ? (mgNo3 * getMolarMassOrOne("N")) / getMolarMassOrOne("NO3") : 0;
}

function siFromSio2(mgSio2) {
  return mgSio2 ? (mgSio2 * getMolarMassOrOne("Si")) / getMolarMassOrOne("SiO2") : 0;
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
  return buildWaterPayloadFromValues(rawValues);
}

function computeWaterElements(normalizedWater) {
  const elements = {};

  const nh4 = normalizedWater.NH4 || 0;
  const no3 = normalizedWater.NO3 || 0;
  elements.N_total = nFromNh4(nh4) + nFromNo3(no3);

  const p2o5 = normalizedWater.P2O5 || 0;
  if (p2o5) {
    elements.P = pFromP2o5(p2o5);
  }

  const k2o = normalizedWater.K2O || 0;
  if (k2o) {
    elements.K = kFromK2o(k2o);
  }

  const cao = normalizedWater.CaO || 0;
  if (cao) {
    elements.Ca = caFromCao(cao);
  }

  const mgo = normalizedWater.MgO || 0;
  if (mgo) {
    elements.Mg = mgFromMgo(mgo);
  }

  const na2o = normalizedWater.Na2O || 0;
  if (na2o) {
    elements.Na = naFromNa2o(na2o);
  }

  const so4 = normalizedWater.SO4 || 0;
  if (so4) {
    elements.S = sFromSo4(so4);
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
    elements.Si = siFromSio2(sio2);
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
    liters: CALC_LITERS,
    fertilizers,
    water_mg_l: waterPayload,
    osmosis_percent: Number(osmosisPercentInput.value) || 0,
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
    liters: Number(solverLitersInput.value) || CALC_LITERS,
    targets,
    water_profile: {
      mg_per_l: waterPayload,
      osmosis_percent: Number(osmosisPercentInput.value) || 0,
    },
    fertilizers_allowed: solverAllowedFertilizers,
    fixed_grams: fixedGrams,
    urea_as_nh4: solverUreaToggle.checked,
    phosphate_species: solverPhosphateSelect.value,
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
    reportError(null, "Bitte einen Profilnamen angeben.");
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

function fetchRecipes() {
  return fetchJson(`${apiBase()}/recipes`, "Fehler beim Laden der Recipes");
}

function fetchRecipeData(filename) {
  return fetchJson(`${apiBase()}/recipes/${encodeURIComponent(filename)}`, "Fehler beim Laden des Recipes");
}

async function saveRecipeData(payload) {
  const response = await fetch(`${apiBase()}/recipes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Recipe speichern fehlgeschlagen");
  }
}

function fetchNutrientSolutions() {
  return fetchJson(`${apiBase()}/nutrient-solutions`, "Fehler beim Laden der Nutrient Solutions");
}

function fetchNutrientSolutionData(filename) {
  return fetchJson(
    `${apiBase()}/nutrient-solutions/${encodeURIComponent(filename)}`,
    "Fehler beim Laden der Nutrient Solution"
  );
}

async function saveNutrientSolutionData(payload) {
  const response = await fetch(`${apiBase()}/nutrient-solutions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Nutrient Solution speichern fehlgeschlagen");
  }
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

async function solveRecipe() {
  const payload = buildSolvePayload();
  const response = await fetch(`${apiBase()}/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Solver fehlgeschlagen");
  }

  return response.json();
}

function renderEcPair(ecValues, el18, el25) {
  const ec18 = Number(ecValues["18.0"]);
  const ec25 = Number(ecValues["25.0"]);
  el18.textContent = Number.isFinite(ec18) ? formatNumber(ec18) : "-";
  el25.textContent = Number.isFinite(ec25) ? formatNumber(ec25) : "-";
}

function renderCalculation(data) {
  lastCalculation = data;
  const oxides = data.oxides_mg_per_l || {};
  const elements = data.elements_mg_per_l || {};
  const npkMetrics = data.npk_metrics || {};
  const waterElements = data.water_elements_mg_per_l || {};
  const waterDisplay = waterElementsForDisplay(waterElements);
  renderWaterSummaryTable(waterSummaryTable, waterDisplay);
  renderOxideSummaryTable(oxideSummaryTable, oxides);
  renderIonSummaryTable(ionSummaryTable, elements);

  const ionMeqEntries = Object.entries(data.ions_meq_per_l || {});
  renderIonCompactList(ionMeqList, ionMeqEntries);

  const ionBalanceEntries = Object.entries(data.ion_balance || {});
  renderIonBalanceCompact(ionBalanceList, ionBalanceEntries);

  npkAllPctValue.textContent = npkMetrics.npk_all_pct || "-";
  npkPNormValue.textContent = npkMetrics.npk_p_norm || "-";
  npkNpkPctValue.textContent = npkMetrics.npk_npk_pct || "-";

  const ec = data.ec || {};
  renderEcPair(ec.ec_mS_per_cm || {}, ec18Value, ec25Value);

  const waterEc = data.ec_water || {};
  renderEcPair(waterEc.ec_mS_per_cm || {}, ecWater18Value, ecWater25Value);
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

function applyNutrientSolution(solution) {
  const targets = solution?.targets_mg_per_l || solution?.targets || {};
  solverTargetDefinitions.forEach((field) => {
    solverTargetValues[field.key] = Number(targets[field.key]) || 0;
  });
  renderSolverTargetsTable();
}

function resetSolverTargets() {
  solverTargetDefinitions.forEach((field) => {
    solverTargetValues[field.key] = 0;
  });
  renderSolverTargetsTable();
  renderSolverResults(null);
}

function updateSolverResultActions() {
  const hasResult = !!(lastSolveResult && lastSolveResult.fertilizers && lastSolveResult.fertilizers.length);
  saveSolverAsRecipeButton.disabled = !hasResult;
  applySolverToCalculatorButton.disabled = !hasResult;
}

function seedSolverAllowedFertilizers() {
  if (solverAllowedFertilizers.length) {
    return;
  }
  selectedFertilizers.forEach((fert) => {
    if (fert.name && !solverAllowedFertilizers.includes(fert.name)) {
      solverAllowedFertilizers.push(fert.name);
    }
  });
  renderSolverAllowedOptions();
  renderSolverFixedTable();
}

function applyWaterProfile(profile) {
  const mg = profile.mg_per_l || {};
  const hco3Direct = mg.HCO3 || 0;
  const derivedHco3 = hco3Direct ? 0 : hco3FromCaco3Value(mg.CaCO3 || 0) + hco3FromKhValue(mg.KH || 0);
  const standardMgKeyMap = {
    NH4: "NH4",
    NH3: "NH3",
    NO3: "NO3",
    NO2: "NO2",
    P: "P",
    SO4: "SO4",
    S: "S",
    Cl: "Cl",
    Fe: "Fe",
    Mn: "Mn",
    Cu: "Cu",
    Zn: "Zn",
    B: "B",
    Mo: "Mo",
    SiO2: "SiO2",
  };

  waterFieldDefinitions.forEach((field) => {
    waterValues[field.key] = 0;
  });

  Object.entries(standardMgKeyMap).forEach(([fieldKey, mgKey]) => {
    waterValues[fieldKey] = mg[mgKey] || 0;
  });

  if (mg.PO4) {
    waterValues.PO4 = mg.PO4;
  } else if (mg.P2O5) {
    waterValues.PO4 = po4FromP2o5(mg.P2O5);
  }

  waterValues.K = mg.K || kFromK2o(mg.K2O || 0);
  waterValues.Ca = mg.Ca || caFromCao(mg.CaO || 0);
  waterValues.Mg = mg.Mg || mgFromMgo(mg.MgO || 0);
  waterValues.Na = mg.Na || naFromNa2o(mg.Na2O || 0);

  waterValues.HCO3 = hco3Direct || derivedHco3;
  waterValues.CO3 = 0;
  waterValues.CaCO3 = 0;
  waterValues.KH = 0;

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

function buildRecipePayload(name, fertilizers, liters, ureaAsNh4, phosphateSpecies) {
  const payload = {
    name,
    liters,
    fertilizers,
    urea_as_nh4: ureaAsNh4,
    phosphate_species: phosphateSpecies,
  };
  const waterProfileSelection = waterProfileSelect.value;
  if (waterProfileSelection) {
    payload.water_profile = waterProfileSelection.replace(/\.yml$/, "");
  }
  const osmosisPercent = Number(osmosisPercentInput.value);
  if (Number.isFinite(osmosisPercent)) {
    payload.osmosis_percent = osmosisPercent;
  }
  return payload;
}

function buildRecipePayloadFromSelection(name) {
  const fertilizers = selectedFertilizers
    .map((fert, index) => ({ name: fert.name, grams: fertilizerAmounts[index] }))
    .filter((entry) => entry.name && entry.grams > 0);
  return buildRecipePayload(name, fertilizers, CALC_LITERS, false, "H2PO4");
}

function buildRecipePayloadFromSolver(name) {
  const fertilizers = Array.isArray(lastSolveResult?.fertilizers) ? lastSolveResult.fertilizers : [];
  return buildRecipePayload(
    name,
    fertilizers,
    Number(solverLitersInput.value) || CALC_LITERS,
    solverUreaToggle.checked,
    solverPhosphateSelect.value
  );
}

function buildSolutionSnapshot() {
  const fertilizers = selectedFertilizers
    .map((fert, index) => ({
      name: fert.name,
      grams: Number(fertilizerAmounts[index]) || 0,
    }))
    .filter((entry) => entry.name);
  return {
    water_profile_value: waterProfileSelect.value || "",
    osmosis_percent: Number(osmosisPercentInput.value) || 0,
    water_unit: waterUnit,
    water_values: { ...waterValues },
    fertilizers,
  };
}

function restoreSolverAllowedFromStorage() {
  const allowed = lsGet(LAST_FERTILIZERS_ALLOWED_KEY, null);
  if (!Array.isArray(allowed)) {
    return false;
  }
  const options = new Set(fertilizerOptions.map((fert) => fert.name));
  const filtered = allowed.filter((name) => options.has(name));
  solverAllowedFertilizers.length = 0;
  solverAllowedFertilizers.push(...filtered);
  renderSolverAllowedOptions();
  renderSolverFixedTable();
  return true;
}

async function init() {
  let hasStoredAllowed = false;
  try {
    fertilizerOptions = await fetchFertilizers();
  } catch (error) {
    reportError(error, "Fehler beim Laden der Dünger-Liste");
    fertilizerOptions = [];
  }
  setFertilizerEditorData(fertilizerOptions);
  hasStoredAllowed = restoreSolverAllowedFromStorage();
  if (!hasStoredAllowed) {
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  }

  try {
    molarMasses = await fetchMolarMasses();
  } catch (error) {
    reportError(error, "Fehler beim Laden der Molmassen");
    molarMasses = {};
  }

  try {
    waterProfiles = await fetchWaterProfiles();
  } catch (error) {
    reportError(error, "Fehler beim Laden der Wasserprofile");
    waterProfiles = [];
  }

  renderWaterProfileOptions();

  try {
    recipeProfiles = await fetchRecipes();
  } catch (error) {
    reportError(error, "Fehler beim Laden der Recipes");
    recipeProfiles = [];
  }

  try {
    nutrientSolutions = await fetchNutrientSolutions();
  } catch (error) {
    reportError(error, "Fehler beim Laden der Nutrient Solutions");
    nutrientSolutions = [];
  }

  renderProfileOptions();

  const savedSolution = lsGet(LAST_SOLUTION_CALCULATED_KEY, null);

  if (savedSolution) {
    waterUnit = savedSolution.water_unit === "mol_l" ? "mol_l" : "mg_l";
    waterUnitToggle.checked = waterUnit === "mol_l";
    osmosisPercentInput.value = Number(savedSolution.osmosis_percent) || 0;
    waterProfileSelect.value = savedSolution.water_profile_value || "";
    waterFieldDefinitions.forEach((field) => {
      waterValues[field.key] = Number(savedSolution.water_values?.[field.key]) || 0;
    });
    renderWaterTable();
    applyRecipe({ fertilizers: savedSolution.fertilizers || [] });
    if (!hasStoredAllowed) {
      seedSolverAllowedFertilizers();
      lsSet(LAST_FERTILIZERS_ALLOWED_KEY, solverAllowedFertilizers);
    }
    try {
      const data = await calculate();
      renderCalculation(data);
    } catch (error) {
      reportError(error, "Berechnung fehlgeschlagen");
    }
    return;
  }

  try {
    const defaultProfile = await fetchWaterProfileData("default");
    applyWaterProfile(defaultProfile);
  } catch (error) {
    renderWaterTable();
  }

  try {
    const recipe = await fetchDefaultRecipe();
    applyRecipe(recipe);
    if (!hasStoredAllowed) {
      seedSolverAllowedFertilizers();
    }
    const data = await calculate();
    renderCalculation(data);
  } catch (error) {
    renderSelectionTable();
    renderCalculatorTable();
    renderWaterSummaryTable(waterSummaryTable, {});
    renderOxideSummaryTable(oxideSummaryTable, {});
    renderIonSummaryTable(ionSummaryTable, {});
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  }
}

reloadButton.addEventListener("click", init);
addRowButton.addEventListener("click", addFertilizerRow);
removeRowButton.addEventListener("click", removeFertilizerRow);
calculateButton.addEventListener("click", async () => {
  try {
    const data = await calculate();
    renderCalculation(data);
    lsSet(LAST_SOLUTION_CALCULATED_KEY, buildSolutionSnapshot());
  } catch (error) {
    reportError(error, "Berechnung fehlgeschlagen");
  }
});

modeToggleInputs.forEach((input) => {
  input.addEventListener("change", (event) => {
    setMode(event.target.value);
  });
});

fertEditorSearchInput.addEventListener("input", (event) => {
  fertilizerEditorFilter = event.target.value || "";
  renderFertilizerEditor();
});

fertEditorAddRowButton.addEventListener("click", addFertilizerEditorRow);
fertEditorDeleteRowButton.addEventListener("click", deleteFertilizerEditorRow);
fertEditorLoadButton.addEventListener("click", reloadFertilizerEditor);
fertEditorSaveButton.addEventListener("click", saveFertilizerEditor);

solverAllowedFertilizersSelect.addEventListener("change", () => {
  solverAllowedFertilizers.length = 0;
  const selected = Array.from(solverAllowedFertilizersSelect.selectedOptions).map((opt) => opt.value);
  solverAllowedFertilizers.push(...selected);
  Object.keys(solverFixedGrams).forEach((key) => {
    if (!solverAllowedFertilizers.includes(key)) {
      delete solverFixedGrams[key];
    }
  });
  renderSolverFixedTable();
  saveAllowedFertilizersDebounced();
});

solveButton.addEventListener("click", async () => {
  try {
    const data = await solveRecipe();
    renderSolverResults(data);
  } catch (error) {
    reportError(error, "Solver fehlgeschlagen");
  }
});

loadProfileButton.addEventListener("click", async () => {
  const selection = profileSelect.value;
  if (!selection) {
    reportError(null, "Bitte ein Profil auswählen.");
    return;
  }
  try {
    if (currentProfileMode === "solver") {
      const solution = await fetchNutrientSolutionData(selection);
      applyNutrientSolution(solution);
      profileNameInput.value = solution.name || "";
    } else {
      const recipe = await fetchRecipeData(selection);
      applyRecipe(recipe);
      seedSolverAllowedFertilizers();
      if (recipe.water_profile) {
        const filename = recipe.water_profile.endsWith(".yml")
          ? recipe.water_profile
          : `${recipe.water_profile}.yml`;
        waterProfileSelect.value = filename;
        const profile = await fetchWaterProfileData(recipe.water_profile);
        applyWaterProfile(profile);
      }
      if (recipe.osmosis_percent !== undefined && recipe.osmosis_percent !== null) {
        osmosisPercentInput.value = recipe.osmosis_percent;
      }
      profileNameInput.value = recipe.name || "";
      scheduleRecalculate();
    }
  } catch (error) {
    reportError(error, "Fehler beim Laden des Profils");
  }
});

resetProfileButton.addEventListener("click", async () => {
  try {
    if (currentProfileMode === "solver") {
      resetSolverTargets();
    } else {
      const recipe = await fetchDefaultRecipe();
      applyRecipe(recipe);
      seedSolverAllowedFertilizers();
      if (recipe.water_profile) {
        const filename = recipe.water_profile.endsWith(".yml")
          ? recipe.water_profile
          : `${recipe.water_profile}.yml`;
        waterProfileSelect.value = filename;
        const profile = await fetchWaterProfileData(recipe.water_profile);
        applyWaterProfile(profile);
      }
      if (recipe.osmosis_percent !== undefined && recipe.osmosis_percent !== null) {
        osmosisPercentInput.value = recipe.osmosis_percent;
      }
      profileNameInput.value = recipe.name || "";
      scheduleRecalculate();
    }
  } catch (error) {
    reportError(error, "Reset fehlgeschlagen");
  }
});

saveProfileButton.addEventListener("click", async () => {
  const name = profileNameInput.value.trim();
  if (!name) {
    reportError(null, "Bitte einen Profilnamen angeben.");
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
    reportError(error, "Speichern fehlgeschlagen");
  }
});

saveSolverAsRecipeButton.addEventListener("click", async () => {
  const name = profileNameInput.value.trim();
  if (!name) {
    reportError(null, "Bitte einen Profilnamen angeben.");
    return;
  }
  if (!lastSolveResult) {
    reportError(null, "Bitte zuerst eine Solver Recipe berechnen.");
    return;
  }
  try {
    const payload = buildRecipePayloadFromSolver(name);
    await saveRecipeData(payload);
    recipeProfiles = await fetchRecipes();
    renderProfileOptions();
  } catch (error) {
    reportError(error, "Recipe speichern fehlgeschlagen");
  }
});

applySolverToCalculatorButton.addEventListener("click", async () => {
  if (!lastSolveResult) {
    reportError(null, "Bitte zuerst eine Solver Recipe berechnen.");
    return;
  }
  const solverLitersRaw = Number(solverLitersInput.value);
  const solverLiters = solverLitersRaw > 0 ? solverLitersRaw : CALC_LITERS;
  const shouldScale = applyScaleToCalcLiters ? applyScaleToCalcLiters.checked : true;
  const factor = shouldScale ? CALC_LITERS / solverLiters : 1;
  const fertilizers = (lastSolveResult.fertilizers || []).map((fert) => ({
    name: fert.name,
    grams: Number(fert.grams || 0) * factor,
  }));
  const recipe = {
    fertilizers,
  };
  applyRecipe(recipe);
  seedSolverAllowedFertilizers();
  const calculatorInput = Array.from(modeToggleInputs).find((input) => input.value === "calculator");
  if (calculatorInput) {
    calculatorInput.checked = true;
  }
  setMode("calculator");
  scheduleRecalculate();
});

loadWaterProfileButton.addEventListener("click", async () => {
  const selection = waterProfileSelect.value;
  if (!selection) {
    reportError(null, "Bitte ein Wasserprofil auswählen.");
    return;
  }
  try {
    const profile = await fetchWaterProfileData(selection);
    applyWaterProfile(profile);
  } catch (error) {
    reportError(error, "Fehler beim Laden des Wasserprofils");
  }
});

resetWaterProfileButton.addEventListener("click", async () => {
  try {
    const profile = await fetchWaterProfileData("default");
    applyWaterProfile(profile);
  } catch (error) {
    reportError(error, "Fehler beim Laden des Wasserprofils");
  }
});

saveWaterProfileButton.addEventListener("click", async () => {
  try {
    await saveWaterProfile();
    waterProfiles = await fetchWaterProfiles();
    renderWaterProfileOptions();
  } catch (error) {
    reportError(error, "Speichern fehlgeschlagen");
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
renderSolverTargetsTable();
setMode("calculator");
updateSolverResultActions();
init();
