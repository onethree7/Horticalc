const fertilizerSelectTable = document.querySelector("#fertilizerSelectTable tbody");
const calculatorTable = document.querySelector("#calculatorTable tbody");
const reloadButton = document.querySelector("#reloadData");
const calculateButton = document.querySelector("#calculateBtn");
const apiBaseInput = document.querySelector("#apiBase");
const addRowButton = document.querySelector("#addFertilizerRow");
const fertilizerDatalist = document.querySelector("#fertilizerOptions");

const ppmHeaderRow = document.querySelector("#ppmHeaderRow");
const ppmValueRow = document.querySelector("#ppmValueRow");
const nFormValueRow = document.querySelector("#nFormValueRow");
const ionMmolHeaderRow = document.querySelector("#ionMmolHeaderRow");
const ionMmolValueRow = document.querySelector("#ionMmolValueRow");
const ionMeqHeaderRow = document.querySelector("#ionMeqHeaderRow");
const ionMeqValueRow = document.querySelector("#ionMeqValueRow");
const ionBalanceHeaderRow = document.querySelector("#ionBalanceHeaderRow");
const ionBalanceValueRow = document.querySelector("#ionBalanceValueRow");

let fertilizerOptions = [];
const selectedFertilizers = [{ name: "", form: "", weight: "" }];
const fertilizerAmounts = [0];

const ppmOrder = ["N_total", "P", "K", "Ca", "Mg", "Na", "S", "C", "Si", "Cl", "Fe", "Mn", "Cu", "Zn", "B", "Mo"];
const ionOrder = [
  "NH4+",
  "K+",
  "Ca+2",
  "Mg+2",
  "Na+",
  "NO3-",
  "H2PO4-",
  "HPO4^2-",
  "SO4^2-",
  "Cl-",
  "HCO3-",
  "CO3^2-",
];

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}

function renderFertilizerDatalist(filterValue = "") {
  fertilizerDatalist.innerHTML = "";
  const query = filterValue.trim().toLowerCase();
  const filtered = query
    ? fertilizerOptions.filter((opt) => opt.name.toLowerCase().includes(query))
    : fertilizerOptions;
  filtered.slice(0, 200).forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt.name;
    fertilizerDatalist.appendChild(option);
  });
}

function resolveFertilizerSelection(value) {
  if (!value) {
    return { name: "", form: "", weight: "" };
  }
  const exact = fertilizerOptions.find((opt) => opt.name.toLowerCase() === value.toLowerCase());
  if (exact) {
    return { name: exact.name, form: exact.form, weight: exact.weight_factor };
  }
  const fallback = fertilizerOptions.find((opt) => opt.name.toLowerCase().includes(value.toLowerCase()));
  if (fallback) {
    return { name: fallback.name, form: fallback.form, weight: fallback.weight_factor };
  }
  return { name: value, form: "", weight: "" };
}

function createSearchInput(initialValue, onSelect) {
  const wrapper = document.createElement("div");
  wrapper.className = "combobox";

  const input = document.createElement("input");
  input.type = "text";
  input.value = initialValue || "";
  input.placeholder = "-- auswählen oder suchen --";
  input.setAttribute("list", "fertilizerOptions");

  const hint = document.createElement("span");
  hint.className = "combo-hint";
  hint.textContent = "Tippe zum Filtern (z. B. Nummer, Marke, Teilstring).";

  input.addEventListener("input", (event) => {
    renderFertilizerDatalist(event.target.value);
  });

  input.addEventListener("change", (event) => {
    const resolved = resolveFertilizerSelection(event.target.value);
    input.value = resolved.name;
    onSelect(resolved);
  });

  input.addEventListener("blur", (event) => {
    const resolved = resolveFertilizerSelection(event.target.value);
    input.value = resolved.name;
    onSelect(resolved);
  });

  wrapper.append(input, hint);
  return wrapper;
}

function renderSelectionTable() {
  fertilizerSelectTable.innerHTML = "";
  for (let i = 0; i < selectedFertilizers.length; i += 1) {
    const row = document.createElement("tr");

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const selectCell = document.createElement("td");
    const combo = createSearchInput(selectedFertilizers[i].name, (resolved) => {
      selectedFertilizers[i] = resolved;
      renderSelectionTable();
      renderCalculatorTable();
    });
    selectCell.appendChild(combo);

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

function renderKeyValueTable(headerRow, valueRow, entries, order = []) {
  const byKey = new Map(entries);
  const orderedKeys = [
    ...order.filter((key) => byKey.has(key)),
    ...entries.map(([key]) => key).filter((key) => !order.includes(key)),
  ];
  const headers = orderedKeys;
  const values = orderedKeys.map((key) => Number(byKey.get(key)).toFixed(3));

  renderHeader(headerRow, headers);
  renderTable(valueRow, values);
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
  renderKeyValueTable(ppmHeaderRow, ppmValueRow, elementEntries, ppmOrder);

  const nFormEntries = Object.entries(data.n_forms_mg_per_l || {});
  const nFormMap = new Map(nFormEntries);
  const nFormValues = [
    nFormMap.get("N_from_fert_NH4") || 0,
    nFormMap.get("N_from_fert_NO3") || 0,
    nFormMap.get("N_from_fert_urea") || 0,
    nFormMap.get("N_from_water_NH4") || 0,
    nFormMap.get("N_from_water_NO3") || 0,
  ];
  const nFormTotal = nFormValues.reduce((sum, value) => sum + value, 0);
  const nFormLabel = "N aus NH4/NO3/Urea/Wasser-NH4/Wasser-NO3 (Summe)";
  const nFormValue = `${nFormValues.map((val) => Number(val).toFixed(3)).join(" / ")} (${nFormTotal.toFixed(3)})`;
  nFormValueRow.innerHTML = "";
  const labelCell = document.createElement("td");
  labelCell.textContent = nFormLabel;
  const valueCell = document.createElement("td");
  valueCell.textContent = nFormValue;
  nFormValueRow.append(labelCell, valueCell);

  const ionMmolEntries = Object.entries(data.ions_mmol_per_l || {});
  renderKeyValueTable(ionMmolHeaderRow, ionMmolValueRow, ionMmolEntries, ionOrder);

  const ionMeqEntries = Object.entries(data.ions_meq_per_l || {});
  renderKeyValueTable(ionMeqHeaderRow, ionMeqValueRow, ionMeqEntries, ionOrder);

  const ionBalanceEntries = Object.entries(data.ion_balance || {});
  renderKeyValueTable(ionBalanceHeaderRow, ionBalanceValueRow, ionBalanceEntries);
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
    renderFertilizerDatalist();
  } catch (error) {
    alert(error.message);
    fertilizerOptions = [];
    renderFertilizerDatalist();
  }

  renderSelectionTable();
  renderCalculatorTable();
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
