const fertilizerSelectTable = document.querySelector("#fertilizerSelectTable tbody");
const calculatorTable = document.querySelector("#calculatorTable tbody");
const reloadButton = document.querySelector("#reloadData");
const calculateButton = document.querySelector("#calculateBtn");
const apiBaseInput = document.querySelector("#apiBase");
const addRowButton = document.querySelector("#addFertilizerRow");

const ppmHeaderRow = document.querySelector("#ppmHeaderRow");
const ppmValueRow = document.querySelector("#ppmValueRow");
const nFormRow = document.querySelector("#nFormRow");
const ionMmolHeaderRow = document.querySelector("#ionMmolHeaderRow");
const ionMmolValueRow = document.querySelector("#ionMmolValueRow");
const ionMeqHeaderRow = document.querySelector("#ionMeqHeaderRow");
const ionMeqValueRow = document.querySelector("#ionMeqValueRow");
const ionBalanceHeaderRow = document.querySelector("#ionBalanceHeaderRow");
const ionBalanceValueRow = document.querySelector("#ionBalanceValueRow");

let fertilizerOptions = [];
const selectedFertilizers = [{ name: "", form: "", weight: "" }];
const fertilizerAmounts = [0];

const ELEMENT_ORDER = [
  "N_total",
  "P",
  "K",
  "Ca",
  "Mg",
  "Na",
  "S",
  "Cl",
  "C",
  "Si",
  "Fe",
  "Mn",
  "Cu",
  "Zn",
  "B",
  "Mo",
];

const ION_ORDER = [
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

const ION_BALANCE_ORDER = [
  "cations_meq_per_l",
  "anions_meq_per_l",
  "error_percent_signed",
  "error_percent_abs",
];

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}

function createComboBox(options, onChange) {
  const wrapper = document.createElement("div");
  wrapper.className = "combo";

  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "-- auswählen --";
  input.autocomplete = "off";

  const list = document.createElement("div");
  list.className = "combo-list";
  list.hidden = true;

  let activeIndex = -1;
  let filteredOptions = options;

  function closeList() {
    list.hidden = true;
    activeIndex = -1;
  }

  function selectOption(option) {
    input.value = option ? option.name : "";
    closeList();
    onChange(option ? option.name : "");
  }

  function renderList() {
    list.innerHTML = "";
    if (filteredOptions.length === 0) {
      const meta = document.createElement("div");
      meta.className = "combo-meta";
      meta.textContent = "Keine Treffer";
      list.appendChild(meta);
      return;
    }

    filteredOptions.slice(0, 12).forEach((opt, index) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "combo-item";
      if (index === activeIndex) {
        item.classList.add("is-active");
      }
      item.textContent = opt.name;
      item.addEventListener("click", () => selectOption(opt));
      list.appendChild(item);
    });
  }

  function updateFilter(value) {
    const query = value.trim().toLowerCase();
    filteredOptions = options.filter((opt) => opt.name.toLowerCase().includes(query));
    activeIndex = -1;
    renderList();
  }

  input.addEventListener("focus", () => {
    updateFilter(input.value);
    list.hidden = false;
  });

  input.addEventListener("input", (event) => {
    updateFilter(event.target.value);
    list.hidden = false;
    if (!event.target.value) {
      onChange("");
    }
  });

  input.addEventListener("keydown", (event) => {
    if (list.hidden) {
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeIndex = Math.min(activeIndex + 1, filteredOptions.length - 1);
      renderList();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      renderList();
    } else if (event.key === "Enter") {
      event.preventDefault();
      const choice = filteredOptions[activeIndex];
      if (choice) {
        selectOption(choice);
      }
    } else if (event.key === "Escape") {
      closeList();
    }
  });

  input.addEventListener("blur", () => {
    window.setTimeout(() => closeList(), 150);
  });

  wrapper.append(input, list);
  return { wrapper, input, selectOption };
}

function renderSelectionTable() {
  fertilizerSelectTable.innerHTML = "";
  for (let i = 0; i < selectedFertilizers.length; i += 1) {
    const row = document.createElement("tr");

    const indexCell = document.createElement("td");
    indexCell.className = "col-index";
    indexCell.textContent = `${i + 1}`;

    const selectCell = document.createElement("td");
    selectCell.className = "col-name";
    const combo = createComboBox(fertilizerOptions, (value) => {
      const match = fertilizerOptions.find((opt) => opt.name === value);
      selectedFertilizers[i] = {
        name: value,
        form: match ? match.form : "",
        weight: match ? match.weight_factor : "",
      };
      renderSelectionTable();
      renderCalculatorTable();
    });
    combo.input.value = selectedFertilizers[i].name;
    selectCell.appendChild(combo.wrapper);

    const formCell = document.createElement("td");
    formCell.className = "col-form";
    formCell.textContent = selectedFertilizers[i].form || "-";

    const weightCell = document.createElement("td");
    weightCell.className = "col-weight";
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
    indexCell.className = "col-index";
    indexCell.textContent = `${i + 1}`;

    const nameCell = document.createElement("td");
    nameCell.className = "col-name";
    nameCell.textContent = selectedFertilizers[i].name || "-";

    const amountCell = document.createElement("td");
    amountCell.className = "col-amount";
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

function orderEntries(entries, order) {
  const map = new Map(entries);
  const ordered = order.filter((key) => map.has(key)).map((key) => [key, map.get(key)]);
  const remaining = entries
    .filter(([key]) => !order.includes(key))
    .sort(([a], [b]) => a.localeCompare(b));
  return [...ordered, ...remaining];
}

function renderKeyValueTable(headerRow, valueRow, entries, order = []) {
  const orderedEntries = order.length ? orderEntries(entries, order) : entries;
  const headers = orderedEntries.map(([key]) => key);
  const values = orderedEntries.map(([, value]) => Number(value).toFixed(3));

  renderHeader(headerRow, headers);
  renderTable(valueRow, values);
}

function formatNForms(entries) {
  const map = new Map(entries);
  const parts = [
    { key: "N_from_fert_NH4", label: "NH4" },
    { key: "N_from_fert_NO3", label: "NO3" },
    { key: "N_from_fert_urea", label: "Urea" },
    { key: "N_from_water_NH4", label: "Water NH4" },
    { key: "N_from_water_NO3", label: "Water NO3" },
  ];
  const values = parts.map((part) => Number(map.get(part.key) || 0));
  const total = values.reduce((sum, value) => sum + value, 0);
  return {
    label: "Fert NH4/NO3/Urea + Water NH4/NO3",
    values: values.map((value) => value.toFixed(3)).join(" / "),
    total: total.toFixed(3),
  };
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
  renderKeyValueTable(ppmHeaderRow, ppmValueRow, elementEntries, ELEMENT_ORDER);

  const nFormEntries = Object.entries(data.n_forms_mg_per_l || {});
  const nForm = formatNForms(nFormEntries);
  nFormRow.innerHTML = "";
  [nForm.label, nForm.values, nForm.total].forEach((value) => {
    const cell = document.createElement("td");
    cell.textContent = value;
    nFormRow.appendChild(cell);
  });

  const ionMmolEntries = Object.entries(data.ions_mmol_per_l || {});
  renderKeyValueTable(ionMmolHeaderRow, ionMmolValueRow, ionMmolEntries, ION_ORDER);

  const ionMeqEntries = Object.entries(data.ions_meq_per_l || {});
  renderKeyValueTable(ionMeqHeaderRow, ionMeqValueRow, ionMeqEntries, ION_ORDER);

  const ionBalanceEntries = Object.entries(data.ion_balance || {});
  renderKeyValueTable(
    ionBalanceHeaderRow,
    ionBalanceValueRow,
    ionBalanceEntries,
    ION_BALANCE_ORDER
  );
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
