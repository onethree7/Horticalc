const fertilizerSelectTable = document.querySelector("#fertilizerSelectTable tbody");
const calculatorTable = document.querySelector("#calculatorTable tbody");
const reloadButton = document.querySelector("#reloadData");
const calculateButton = document.querySelector("#calculateBtn");
const apiBaseInput = document.querySelector("#apiBase");
const addRowButton = document.querySelector("#addFertilizerRow");
const removeRowButton = document.querySelector("#removeFertilizerRow");

const summaryTable = document.querySelector("#summaryTable");
const ionMeqTableBody = document.querySelector("#ionMeqTable tbody");
const ionBalanceTableBody = document.querySelector("#ionBalanceTable tbody");

let fertilizerOptions = [];
const selectedFertilizers = [{ name: "", form: "", weight: "" }];
const fertilizerAmounts = [0];
const numberFormatter = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});
const nutrientFormatter = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});
const nutrientIntegerFormatter = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});
const nutrientIntegerKeys = new Set(["N_total", "P", "K", "Ca", "Mg", "S"]);
const nutrientTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "Si"]);
const oxideIntegerKeys = new Set([
  "N_total",
  "NH4",
  "NO3",
  "Ur-N",
  "P2O5",
  "K2O",
  "CaO",
  "MgO",
  "SO4",
]);
const oxideTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "SiO2"]);
const summaryColumnOrder = [
  { oxide: "N_total", element: "N_total", label: "N_total" },
  { oxide: "P2O5", element: "P", label: "P2O5/P" },
  { oxide: "K2O", element: "K", label: "K2O/K" },
  { oxide: "CaO", element: "Ca", label: "CaO/Ca" },
  { oxide: "MgO", element: "Mg", label: "MgO/Mg" },
  { oxide: "SO4", element: "S", label: "SO4/S" },
  { oxide: "Cl", element: "Cl", label: "Cl" },
  { oxide: "Fe", element: "Fe", label: "Fe" },
  { oxide: "Mn", element: "Mn", label: "Mn" },
  { oxide: "Cu", element: "Cu", label: "Cu" },
  { oxide: "Zn", element: "Zn", label: "Zn" },
  { oxide: "B", element: "B", label: "B" },
  { oxide: "Mo", element: "Mo", label: "Mo" },
  { oxide: "SiO2", element: "Si", label: "SiO2/Si" },
  { oxide: "Na2O", element: "Na", label: "Na2O/Na" },
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

function renderSelectionTable() {
  fertilizerSelectTable.innerHTML = "";
  for (let i = 0; i < selectedFertilizers.length; i += 1) {
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
    });
    select.value = selectedFertilizers[i].name;
    selectCell.appendChild(select);

    const formCell = document.createElement("td");
    formCell.textContent = selectedFertilizers[i].form || "-";

    const weightCell = document.createElement("td");
    weightCell.textContent = selectedFertilizers[i].weight || "-";

    row.append(indexCell, selectCell, formCell, weightCell);
    fertilizerSelectTable.appendChild(row);
  }
}

function renderCalculatorTable() {
  calculatorTable.innerHTML = "";
  for (let i = 0; i < selectedFertilizers.length; i += 1) {
    const row = document.createElement("tr");

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const nameCell = document.createElement("td");
    nameCell.textContent = selectedFertilizers[i].name || "-";

    const amountCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.step = "0.01";
    input.value = fertilizerAmounts[i];
    input.addEventListener("input", (event) => {
      fertilizerAmounts[i] = Number(event.target.value) || 0;
    });
    amountCell.appendChild(input);

    row.append(indexCell, nameCell, amountCell);
    calculatorTable.appendChild(row);
  }
}

function formatNumber(value, formatter = numberFormatter) {
  if (Number.isFinite(value)) {
    return formatter.format(value);
  }
  return "-";
}

function renderKeyValueTable(tableBody, entries) {
  tableBody.innerHTML = "";
  entries.forEach(([key, value]) => {
    const row = document.createElement("tr");
    const keyCell = document.createElement("td");
    keyCell.textContent = key;
    const valueCell = document.createElement("td");
    valueCell.textContent = formatNumber(Number(value));
    row.append(keyCell, valueCell);
    tableBody.appendChild(row);
  });
}

function renderSummaryTable(table, oxides, elements, nFormsRaw, nFormsElement) {
  table.innerHTML = "";
  const { value: nTotalValue, tooltip: nTotalTooltip } = buildOxideNTotalDetails(nFormsRaw);
  const { value: nTotalElementValue, tooltip: nTotalElementTooltip } = buildElementNTotalDetails(
    nFormsElement,
  );
  const oxideMap = new Map(Object.entries(oxides));
  if (Number.isFinite(nTotalValue)) {
    oxideMap.set("N_total", nTotalValue);
  }
  const elementMap = new Map(Object.entries(elements));

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
  const rows = [
    {
      label: "Oxide",
      valueMap: oxideMap,
      formatter: formatOxideValue,
      title: nTotalTooltip,
      titleKey: "N_total",
      titleValue: nTotalValue,
    },
    {
      label: "Ionen",
      valueMap: elementMap,
      formatter: formatNutrientValue,
      title: nTotalElementTooltip,
      titleKey: "N_total",
      titleValue: nTotalElementValue,
    },
  ];

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
      if (row.title && row.titleKey === key && Number.isFinite(row.titleValue)) {
        td.title = row.title;
      }
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

function buildOxideNTotalDetails(nFormsRaw) {
  if (!nFormsRaw) {
    return { value: Number.NaN, tooltip: "" };
  }

  const parts = [
    ["NH4", Number(nFormsRaw["NH4"])],
    ["NO3", Number(nFormsRaw["NO3"])],
    ["Ur-N", Number(nFormsRaw["Ur-N"])],
  ].filter(([, value]) => Number.isFinite(value));

  const sum = parts.reduce((total, [, value]) => total + value, 0);
  const value = parts.length ? sum : Number.NaN;
  const tooltip = parts.length
    ? `Summe aus:\n${parts
        .map(([label, partValue]) => `${label}=${formatOxideValue(label, partValue)} mg/l`)
        .join("\n")}`
    : "";

  return { value, tooltip };
}

function buildElementNTotalDetails(nFormsElement) {
  if (!nFormsElement) {
    return { value: Number.NaN, tooltip: "" };
  }

  const nh4Value = Number(nFormsElement.N_from_NH4);
  const no3Value = Number(nFormsElement.N_from_NO3);
  const ureaValue = Number(nFormsElement.N_from_UREA);

  const parts = [
    ["NH4", nh4Value],
    ["NO3", no3Value],
    ["Ur-N", ureaValue],
  ].filter(([, value]) => Number.isFinite(value));

  const sum = parts.reduce((total, [, value]) => total + value, 0);
  const value = parts.length ? sum : Number.NaN;
  const tooltip = parts.length
    ? parts
        .map(
          ([label, partValue]) =>
            `N aus ${label} = ${nutrientFormatter.format(partValue)} mg/l`,
        )
        .join("\n")
    : "";

  return { value, tooltip };
}

function buildPayload() {
  const fertilizers = selectedFertilizers
    .map((fert, index) => ({ name: fert.name, grams: fertilizerAmounts[index] }))
    .filter((entry) => entry.name && entry.grams > 0);

  return {
    liters: 10.0,
    fertilizers,
  };
}

async function fetchFertilizers() {
  const response = await fetch(`${apiBase()}/fertilizers`);
  if (!response.ok) {
    throw new Error("Fehler beim Laden der Dünger-Liste");
  }
  return response.json();
}

async function fetchDefaultRecipe() {
  const response = await fetch(`${apiBase()}/recipes/default`);
  if (!response.ok) {
    throw new Error("Fehler beim Laden des Default-Rezepts");
  }
  return response.json();
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
  const oxides = data.oxides_mg_per_l || {};
  const elements = data.elements_mg_per_l || {};
  const nFormsRaw = data.n_forms_raw_mg_per_l || {};
  const nFormsElement = data.n_forms_element_mg_per_l || {};
  renderSummaryTable(summaryTable, oxides, elements, nFormsRaw, nFormsElement);

  const ionMeqEntries = Object.entries(data.ions_meq_per_l || {});
  renderKeyValueTable(ionMeqTableBody, ionMeqEntries);

  const ionBalanceEntries = Object.entries(data.ion_balance || {});
  renderKeyValueTable(ionBalanceTableBody, ionBalanceEntries);
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

async function init() {
  try {
    fertilizerOptions = await fetchFertilizers();
  } catch (error) {
    alert(error.message);
    fertilizerOptions = [];
  }

  try {
    const recipe = await fetchDefaultRecipe();
    applyRecipe(recipe);
    const data = await calculate();
    renderCalculation(data);
  } catch (error) {
    renderSelectionTable();
    renderCalculatorTable();
    renderSummaryTable(summaryTable, {}, {});
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

init();
