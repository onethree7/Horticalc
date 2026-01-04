const MAX_ROWS = 10;

const fertilizerSelectTable = document.querySelector("#fertilizerSelectTable tbody");
const calculatorTable = document.querySelector("#calculatorTable tbody");
const reloadButton = document.querySelector("#reloadData");
const calculateButton = document.querySelector("#calculateBtn");
const apiBaseInput = document.querySelector("#apiBase");
const addRowButton = document.querySelector("#addRowBtn");

const ppmHeaderRow = document.querySelector("#ppmHeaderRow");
const ppmValueRow = document.querySelector("#ppmValueRow");
const ionHeaderRow = document.querySelector("#ionHeaderRow");
const ionValueRow = document.querySelector("#ionValueRow");

let fertilizerOptions = [];
let activeRowCount = 1;
const selectedFertilizers = Array.from({ length: MAX_ROWS }, () => ({ name: "", form: "", weight: "" }));
const fertilizerAmounts = Array.from({ length: MAX_ROWS }, () => 0);

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
  for (let i = 0; i < activeRowCount; i += 1) {
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
  addRowButton.disabled = activeRowCount >= MAX_ROWS;
}

function renderCalculatorTable() {
  calculatorTable.innerHTML = "";
  for (let i = 0; i < activeRowCount; i += 1) {
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

function renderTable(rowEl, values) {
  rowEl.innerHTML = "";
  values.forEach((value) => {
    const cell = document.createElement("td");
    cell.textContent = value;
    rowEl.appendChild(cell);
  });
}

function renderHeader(rowEl, headers) {
  rowEl.innerHTML = "";
  headers.forEach((header) => {
    const cell = document.createElement("th");
    cell.textContent = header;
    rowEl.appendChild(cell);
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
  const elementHeaders = elementEntries.map(([key]) => key);
  const elementValues = elementEntries.map(([, value]) => value.toFixed(3));

  renderHeader(ppmHeaderRow, elementHeaders);
  renderTable(ppmValueRow, elementValues);

  const nFormEntries = Object.entries(data.n_forms_mg_per_l || {});
  const ionHeaders = nFormEntries.map(([key]) => key);
  const ionValues = nFormEntries.map(([, value]) => value.toFixed(3));

  renderHeader(ionHeaderRow, ionHeaders);
  renderTable(ionValueRow, ionValues);
}

async function init() {
  try {
    fertilizerOptions = await fetchFertilizers();
  } catch (error) {
    alert(error.message);
    fertilizerOptions = [];
  }

  renderSelectionTable();
  renderCalculatorTable();
}

reloadButton.addEventListener("click", init);
addRowButton.addEventListener("click", () => {
  if (activeRowCount < MAX_ROWS) {
    activeRowCount += 1;
    renderSelectionTable();
    renderCalculatorTable();
  }
});
calculateButton.addEventListener("click", async () => {
  try {
    const data = await calculate();
    renderCalculation(data);
  } catch (error) {
    alert(error.message);
  }
});

init();
