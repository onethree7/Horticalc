const fertilizerSelectTable = document.querySelector("#fertilizerSelectTable tbody");
const calculatorTable = document.querySelector("#calculatorTable tbody");
const reloadButton = document.querySelector("#reloadData");
const calculateButton = document.querySelector("#calculateBtn");
const apiBaseInput = document.querySelector("#apiBase");
const addRowButton = document.querySelector("#addFertilizerRow");
const removeRowButton = document.querySelector("#removeFertilizerRow");

const ppmTable = document.querySelector("#ppmTable");
const oxideTable = document.querySelector("#oxideTable");
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
const oxideColumnOrder = [
  "NH4",
  "NO3",
  "Ur-N",
  "P2O5",
  "K2O",
  "CaO",
  "MgO",
  "SO4",
  "Cl",
  "Fe",
  "Mn",
  "Cu",
  "Zn",
  "B",
  "Mo",
  "SiO2",
  "Na2O",
];
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
  "Si",
];
const nutrientIntegerKeys = new Set(["N_total", "P", "K", "Ca", "Mg", "S"]);
const nutrientTraceKeys = new Set(["Fe", "Mn", "Cu", "Zn", "B", "Mo", "Si"]);
const oxideIntegerKeys = new Set([
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

function renderHorizontalTable(
  table,
  entries,
  orderedKeys = [],
  formatter = numberFormatter,
  formatValue = null,
) {
  table.innerHTML = "";
  const dataMap = new Map(entries);
  const ordered = orderedKeys.filter((key) => key);
  const remaining = entries
    .map(([key]) => key)
    .filter((key) => !ordered.includes(key));
  const trailingKeys = ["CO3"];
  const trailing = remaining.filter((key) => trailingKeys.includes(key));
  const remainingOrdered = remaining.filter((key) => !trailingKeys.includes(key));
  const columns = [...ordered, ...remainingOrdered, ...trailing];

  if (!columns.length) {
    return;
  }

  const colgroup = document.createElement("colgroup");
  columns.forEach((key) => {
    const col = document.createElement("col");
    const columnClass = `col-${normalizeColumnKey(key)}`;
    col.classList.add(columnClass);
    colgroup.appendChild(col);
  });
  table.appendChild(colgroup);

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((key) => {
    const th = document.createElement("th");
    th.textContent = key;
    th.dataset.key = key;
    th.classList.add(`col-${normalizeColumnKey(key)}`);
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const valueRow = document.createElement("tr");
  const formatCellValue =
    typeof formatValue === "function"
      ? formatValue
      : (key, value) => formatNumber(value, formatter);

  columns.forEach((key) => {
    const td = document.createElement("td");
    td.textContent = formatCellValue(key, Number(dataMap.get(key)));
    td.dataset.key = key;
    td.classList.add(`col-${normalizeColumnKey(key)}`);
    valueRow.appendChild(td);
  });
  tbody.appendChild(valueRow);
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
  renderHorizontalTable(ppmTable, elementEntries, nutrientColumnOrder, nutrientFormatter, formatNutrientValue);

  const oxideEntries = Object.entries(data.oxides_mg_per_l || {});
  renderHorizontalTable(oxideTable, oxideEntries, oxideColumnOrder, nutrientFormatter, formatOxideValue);

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
    renderHorizontalTable(ppmTable, [], nutrientColumnOrder);
    renderHorizontalTable(oxideTable, [], oxideColumnOrder);
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
