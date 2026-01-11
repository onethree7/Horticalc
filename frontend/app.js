const fertilizerSelectTable = document.querySelector("#fertilizerSelectTable tbody");
const calculatorTable = document.querySelector("#calculatorTable tbody");
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
const waterToggleButton = document.querySelector("#toggleWaterValues");
const waterContent = document.querySelector("#waterContent");
const ecValue18 = document.querySelector("#ecValue18");
const ecValue25 = document.querySelector("#ecValue25");
const npkAllPct = document.querySelector("#npkAllPct");
const npkPNorm = document.querySelector("#npkPNorm");
const npkNpkPct = document.querySelector("#npkNpkPct");

const summaryTable = document.querySelector("#summaryTable");
const ionMeqTableBody = document.querySelector("#ionMeqTable tbody");
const ionBalanceTableBody = document.querySelector("#ionBalanceTable tbody");

let fertilizerOptions = [];
const selectedFertilizers = [{ name: "", form: "", weight: "" }];
const fertilizerAmounts = [0];
let molarMasses = {};
let waterProfiles = [];
let waterUnit = "mg_l";
let lastCalculation = null;

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
    input.value = Number.isFinite(displayValue) ? displayValue : 0;
    input.addEventListener("input", (event) => {
      const parsed = Number(event.target.value) || 0;
      waterValues[field.key] = waterUnit === "mol_l" ? molToMg(field.key, parsed) : parsed;
    });
    valueCell.appendChild(input);

    const unitCell = document.createElement("td");
    unitCell.textContent = unitLabelForKey(field.key);

    row.append(labelCell, valueCell, unitCell);
    waterTableBody.appendChild(row);
  });
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

function updateWaterToggle(isCollapsed) {
  waterContent.classList.toggle("is-collapsed", isCollapsed);
  waterToggleButton.setAttribute("aria-expanded", String(!isCollapsed));
  waterToggleButton.textContent = isCollapsed ? "Wasserwerte anzeigen" : "Wasserwerte ausblenden";
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
      label: "Wasserwerte",
      valueMap: waterMap,
      formatter: waterUnit === "mol_l" ? formatTraceValue : formatNutrientValue,
    });
  }
  rows.push(
    {
      label: "Oxide",
      valueMap: oxideMap,
      formatter: formatOxideValue,
    },
    {
      label: "Ionen",
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

function normalizeWaterValues(rawValues, osmosisPercent) {
  const factor = 1 - clamp(osmosisPercent, 0, 100) / 100;
  const normalized = {};

  const add = (key, value) => {
    if (!Number.isFinite(value) || value === 0) {
      return;
    }
    normalized[key] = (normalized[key] || 0) + value * factor;
  };

  const mm = (key) => getMolarMass(key) || 1;

  const p2o5FromP = (mgP) => (mgP ? (mgP * mm("P2O5")) / (2 * mm("P")) : 0);
  const p2o5FromPO4 = (mgPO4) => {
    if (!mgPO4) return 0;
    const mgP = (mgPO4 * mm("P")) / mm("PO4");
    return p2o5FromP(mgP);
  };

  const so4FromS = (mgS) => (mgS ? (mgS * mm("SO4")) / mm("S") : 0);
  const k2oFromK = (mgK) => (mgK ? (mgK * mm("K2O")) / (2 * mm("K")) : 0);
  const na2oFromNa = (mgNa) => (mgNa ? (mgNa * mm("Na2O")) / (2 * mm("Na")) : 0);
  const caoFromCa = (mgCa) => (mgCa ? (mgCa * mm("CaO")) / mm("Ca") : 0);
  const mgoFromMg = (mgMg) => (mgMg ? (mgMg * mm("MgO")) / mm("Mg") : 0);

  const hco3FromCaco3 = (mgCaCO3) => {
    if (!mgCaCO3) return 0;
    const equiv = mm("CaCO3") / 2;
    return (mgCaCO3 * mm("HCO3")) / equiv;
  };

  const hco3FromKh = (dKh) => {
    if (!dKh) return 0;
    const mgCaCO3 = dKh * 17.848;
    return hco3FromCaco3(mgCaCO3);
  };

  add("NH4", (rawValues.NH4 || 0) + (rawValues.NH3 || 0));
  add("NO3", (rawValues.NO3 || 0) + (rawValues.NO2 || 0));
  add("P2O5", p2o5FromPO4(rawValues.PO4 || 0));
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
  add("HCO3", (rawValues.HCO3 || 0) + hco3FromCaco3(rawValues.CaCO3 || 0) + hco3FromKh(rawValues.KH || 0));
  add("CO3", rawValues.CO3 || 0);
  add("SiO2", rawValues.SiO2 || 0);

  return normalized;
}

function computeWaterElements(normalizedWater) {
  const mm = (key) => getMolarMass(key) || 1;
  const elements = {};

  const nh4 = normalizedWater.NH4 || 0;
  const no3 = normalizedWater.NO3 || 0;
  const nFromNh4 = nh4 ? (nh4 * mm("N")) / mm("NH4") : 0;
  const nFromNo3 = no3 ? (no3 * mm("N")) / mm("NO3") : 0;
  elements.N_total = nFromNh4 + nFromNo3;

  const p2o5 = normalizedWater.P2O5 || 0;
  if (p2o5) {
    elements.P = (p2o5 * 2 * mm("P")) / mm("P2O5");
  }

  const k2o = normalizedWater.K2O || 0;
  if (k2o) {
    elements.K = (k2o * 2 * mm("K")) / mm("K2O");
  }

  const cao = normalizedWater.CaO || 0;
  if (cao) {
    elements.Ca = (cao * mm("Ca")) / mm("CaO");
  }

  const mgo = normalizedWater.MgO || 0;
  if (mgo) {
    elements.Mg = (mgo * mm("Mg")) / mm("MgO");
  }

  const na2o = normalizedWater.Na2O || 0;
  if (na2o) {
    elements.Na = (na2o * 2 * mm("Na")) / mm("Na2O");
  }

  const so4 = normalizedWater.SO4 || 0;
  if (so4) {
    elements.S = (so4 * mm("S")) / mm("SO4");
  }

  ["Cl", "Fe", "Mn", "Cu", "Zn", "B", "Mo"].forEach((key) => {
    if (normalizedWater[key]) {
      elements[key] = normalizedWater[key];
    }
  });

  const sio2 = normalizedWater.SiO2 || 0;
  if (sio2) {
    elements.Si = (sio2 * mm("Si")) / mm("SiO2");
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

  return {
    liters: 10.0,
    fertilizers,
    water_mg_l: normalizeWaterValues(waterValues, Number(osmosisPercentInput.value) || 0),
  };
}

async function fetchFertilizers() {
  const response = await fetch(`${apiBase()}/fertilizers`);
  if (!response.ok) {
    throw new Error("Fehler beim Laden der Dünger-Liste");
  }
  return response.json();
}

async function fetchMolarMasses() {
  const response = await fetch(`${apiBase()}/molar-masses`);
  if (!response.ok) {
    throw new Error("Fehler beim Laden der Molmassen");
  }
  return response.json();
}

async function fetchWaterProfiles() {
  const response = await fetch(`${apiBase()}/water-profiles`);
  if (!response.ok) {
    throw new Error("Fehler beim Laden der Wasserprofile");
  }
  return response.json();
}

async function fetchWaterProfileData(filename) {
  const response = await fetch(`${apiBase()}/water-profiles/${encodeURIComponent(filename)}`);
  if (!response.ok) {
    throw new Error("Fehler beim Laden des Wasserprofils");
  }
  return response.json();
}

async function saveWaterProfile() {
  const name = waterProfileNameInput.value.trim();
  if (!name) {
    alert("Bitte einen Profilnamen angeben.");
    return;
  }
  const payload = {
    name,
    source: "Horticalc UI",
    mg_per_l: { ...waterValues },
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
  lastCalculation = data;
  const oxides = data.oxides_mg_per_l || {};
  const elements = data.elements_mg_per_l || {};
  const normalizedWater = normalizeWaterValues(waterValues, Number(osmosisPercentInput.value) || 0);
  const waterElements = computeWaterElements(normalizedWater);
  const waterDisplay = waterElementsForDisplay(waterElements);
  renderSummaryTable(summaryTable, oxides, elements, waterDisplay);

  const ionMeqEntries = Object.entries(data.ions_meq_per_l || {});
  renderKeyValueTable(ionMeqTableBody, ionMeqEntries);

  const ionBalanceEntries = Object.entries(data.ion_balance || {});
  renderKeyValueTable(ionBalanceTableBody, ionBalanceEntries);

  const ec = data.ec || {};
  const ecValues = ec.ec_mS_per_cm || {};
  const ec18 = Number(ecValues["18.0"]);
  const ec25 = Number(ecValues["25.0"]);
  if (Number.isFinite(ec18) && Number.isFinite(ec25)) {
    ecValue18.textContent = `${formatNumber(ec18)} mS/cm`;
    ecValue25.textContent = `${formatNumber(ec25)} mS/cm`;
  } else {
    ecValue18.textContent = "-";
    ecValue25.textContent = "-";
  }

  const npk = data.npk_metrics || {};
  npkAllPct.textContent = npk.npk_all_pct || "-";
  npkPNorm.textContent = npk.npk_p_norm || "-";
  npkNpkPct.textContent = npk.npk_npk_pct || "-";
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
  const mm = (key) => getMolarMass(key) || 1;

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
    waterValues.PO4 = (mg.P2O5 * 2 * mm("PO4")) / mm("P2O5");
  }
  waterValues.P = mg.P || 0;

  waterValues.SO4 = mg.SO4 || 0;
  waterValues.S = mg.S || 0;

  waterValues.K = mg.K || (mg.K2O ? (mg.K2O * 2 * mm("K")) / mm("K2O") : 0);
  waterValues.Ca = mg.Ca || (mg.CaO ? (mg.CaO * mm("Ca")) / mm("CaO") : 0);
  waterValues.Mg = mg.Mg || (mg.MgO ? (mg.MgO * mm("Mg")) / mm("MgO") : 0);
  waterValues.Na = mg.Na || (mg.Na2O ? (mg.Na2O * 2 * mm("Na")) / mm("Na2O") : 0);

  waterValues.Cl = mg.Cl || 0;
  waterValues.HCO3 = mg.HCO3 || 0;
  waterValues.CO3 = mg.CO3 || 0;
  waterValues.Fe = mg.Fe || 0;
  waterValues.Mn = mg.Mn || 0;
  waterValues.Cu = mg.Cu || 0;
  waterValues.Zn = mg.Zn || 0;
  waterValues.B = mg.B || 0;
  waterValues.Mo = mg.Mo || 0;
  waterValues.CaCO3 = mg.CaCO3 || 0;
  waterValues.KH = mg.KH || 0;
  waterValues.SiO2 = mg.SiO2 || 0;

  waterProfileNameInput.value = profile.name || "";
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
  if (lastCalculation) {
    renderCalculation(lastCalculation);
  }
});

waterUnitToggle.addEventListener("change", (event) => {
  waterUnit = event.target.checked ? "mol_l" : "mg_l";
  renderWaterTable();
  if (lastCalculation) {
    renderCalculation(lastCalculation);
  }
});

waterToggleButton.addEventListener("click", () => {
  const isCollapsed = !waterContent.classList.contains("is-collapsed");
  updateWaterToggle(isCollapsed);
});

updateWaterToggle(true);

init();
