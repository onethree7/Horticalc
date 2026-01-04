const fertilizerSelectTable = document.querySelector("#fertilizerSelectTable tbody");
const calculatorTable = document.querySelector("#calculatorTable tbody");
const reloadButton = document.querySelector("#reloadData");
const calculateButton = document.querySelector("#calculateBtn");
const apiBaseInput = document.querySelector("#apiBase");
const addRowButton = document.querySelector("#addFertilizerRow");

const ppmTable = document.querySelector("#ppmTable");
const nFormTableBody = document.querySelector("#nFormTable tbody");
const ionMmolTableBody = document.querySelector("#ionMmolTable tbody");
const ionMeqTableBody = document.querySelector("#ionMeqTable tbody");
const ionBalanceTableBody = document.querySelector("#ionBalanceTable tbody");

let fertilizerOptions = [];
const selectedFertilizers = [{ name: "", form: "", weight: "" }];
const fertilizerAmounts = [0];
const numberFormatter = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});
const nutrientColumnOrder = [
  "N_total",
  "P",
  "K",
  "Ca",
  "Mg",
  "S",
  "Cl",
  "Fe",
  "Mn",
  "Cu",
  "Zn",
  "B",
  "Mo",
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

function formatNumber(value) {
  if (Number.isFinite(value)) {
    return numberFormatter.format(value);
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

function renderHorizontalTable(table, entries, orderedKeys = []) {
  table.innerHTML = "";
  const dataMap = new Map(entries);
  const ordered = orderedKeys.filter((key) => key);
  const remaining = entries
    .map(([key]) => key)
    .filter((key) => !ordered.includes(key));
  const columns = [...ordered, ...remaining];

  if (!columns.length) {
    return;
  }

  const colgroup = document.createElement("colgroup");
  columns.forEach(() => {
    const col = document.createElement("col");
    colgroup.appendChild(col);
  });
  table.appendChild(colgroup);

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((key) => {
    const th = document.createElement("th");
    th.textContent = key;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const valueRow = document.createElement("tr");
  columns.forEach((key) => {
    const td = document.createElement("td");
    td.textContent = formatNumber(Number(dataMap.get(key)));
    valueRow.appendChild(td);
  });
  tbody.appendChild(valueRow);
  table.appendChild(tbody);
}

function formatSeries(values) {
  return values.map((value) => formatNumber(value)).join(" / ");
}

function renderNFormsTable(tableBody, data) {
  tableBody.innerHTML = "";
  const fertNh4 = Number(data.N_from_fert_NH4 || 0);
  const fertNo3 = Number(data.N_from_fert_NO3 || 0);
  const fertUrea = Number(data.N_from_fert_urea || 0);
  const waterNh4 = Number(data.N_from_water_NH4 || 0);
  const waterNo3 = Number(data.N_from_water_NO3 || 0);

  const fertTotal = fertNh4 + fertNo3 + fertUrea;
  const waterTotal = waterNh4 + waterNo3;
  const overallTotal = fertTotal + waterTotal;

  const rows = [
    [
      "N aus Dünger (NH4 / NO3 / Urea)",
      `${formatSeries([fertNh4, fertNo3, fertUrea])} (Σ ${formatNumber(fertTotal)})`,
    ],
    [
      "N aus Wasser (NH4 / NO3)",
      `${formatSeries([waterNh4, waterNo3])} (Σ ${formatNumber(waterTotal)})`,
    ],
    ["N gesamt (Formen)", formatNumber(overallTotal)],
  ];

  rows.forEach(([label, value]) => {
    const row = document.createElement("tr");
    const labelCell = document.createElement("td");
    labelCell.textContent = label;
    const valueCell = document.createElement("td");
    valueCell.textContent = value;
    row.append(labelCell, valueCell);
    tableBody.appendChild(row);
  });
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
  const elementEntries = Object.entries(data.elements_mg_per_l || {});
  renderHorizontalTable(ppmTable, elementEntries, nutrientColumnOrder);

  renderNFormsTable(nFormTableBody, data.n_forms_mg_per_l || {});

  const ionMmolEntries = Object.entries(data.ions_mmol_per_l || {});
  renderKeyValueTable(ionMmolTableBody, ionMmolEntries);

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
    renderHorizontalTable(ppmTable, [], nutrientColumnOrder);
  }
}

reloadButton.addEventListener("click", init);
addRowButton.addEventListener("click", addFertilizerRow);
calculateButton.addEventListener("click", async () => {
  try {
    const data = await calculate();
    renderCalculation(data);
  } catch (error) {
    alert(error.message);
  }
});

init();
