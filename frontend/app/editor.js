import { NUTRIENT_FORMATTER, SOLVER_MAX_FORMATTER } from "./constants.js";
import { createTable, qs, qsa } from "./dom.js";
import { formatNumber, normalizeDecimalInputElement, parseDecimalInput } from "./formatting.js";

export function createEditorController({ api, i18n, notifications, isActive, onCatalogChange }) {
const fertilizerEditorTableWrap = qs("#fertilizerEditorTableWrap");
const fertEditorSearchInput = qs("#fertEditorSearch");
const fertEditorAddRowButton = qs("#fertEditorAddRow");
const fertEditorDeleteRowButton = qs("#fertEditorDeleteRow");
const fertEditorLoadButton = qs("#fertEditorLoad");
const fertEditorSaveButton = qs("#fertEditorSave");
const t = (key, params) => i18n.t(key, params);
const nutrientFormatter = NUTRIENT_FORMATTER;
const solverMaxFormatter = SOLVER_MAX_FORMATTER;
let fertilizerEditorRows = [];
let fertilizerEditorSelectedIndex = 0;
let fertilizerEditorFilter = "";
let fertilizerEditorSearchTimer;
let fertilizerEditorTable;
let fertilizerEditorNameWidthPx = 288;
let fertilizerEditorCompKeys = [];
let fertilizerEditorSort = { key: "name", direction: "asc" };
let fertilizerEditorPreferredKeys = [];
let mounted = false;


function buildFertilizerCompKeys(fertilizers) {
  const keySet = new Set();
  const keyLookup = new Map();
  fertilizers.forEach((fert) => {
    Object.keys(fert.comp || {}).forEach((key) => {
      keySet.add(key);
      const normalized = key.trim().toUpperCase();
      if (!keyLookup.has(normalized)) {
        keyLookup.set(normalized, key);
      }
    });
  });
  const ordered = [];
  fertilizerEditorPreferredKeys.forEach((key) => {
    const normalized = key.trim().toUpperCase();
    const matchedKey = keyLookup.get(normalized);
    if (matchedKey && keySet.has(matchedKey)) {
      ordered.push(matchedKey);
      keySet.delete(matchedKey);
    }
  });
  ordered.push(...Array.from(keySet).sort((a, b) => a.localeCompare(b)));
  return ordered;
}

function setFertilizerEditorData(fertilizers) {
  fertilizerEditorRows = (fertilizers || []).map((fert) => ({
    name: fert.name || "",
    liquid: Boolean(fert.liquid),
    weight_factor: Number.isFinite(fert.weight_factor) ? fert.weight_factor : null,
    comp: { ...(fert.comp || {}) },
    solver_max_dose_per_l: Number.isFinite(fert.solver_max_dose_per_l)
      ? fert.solver_max_dose_per_l
      : null,
  }));
  fertilizerEditorSelectedIndex = 0;
  fertilizerEditorCompKeys = buildFertilizerCompKeys(fertilizerEditorRows);
  if (isActive()) {
    renderFertilizerEditor();
  }
}

function focusEditorInput(rowIndex, field, compKey) {
  if (!fertilizerEditorTableWrap) {
    return;
  }
  let selector = `input[data-row-index="${rowIndex}"][data-field="${field}"]`;
  if (compKey) {
    selector += `[data-comp-key="${compKey}"]`;
  }
  const input = qs(selector, fertilizerEditorTableWrap);
  if (input) {
    input.focus();
  }
}

function setSelectedEditorRow(editorIndex) {
  fertilizerEditorSelectedIndex = editorIndex;
  if (!fertilizerEditorTable) {
    return;
  }
  const rows = Array.from(qsa("tr[data-editor-index]", fertilizerEditorTable));
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
  const nextInRow = qs(`input[data-col-index="${colIndex + 1}"]`, row);
  if (nextInRow) {
    nextInRow.focus();
    return;
  }
  let nextRow = row.nextElementSibling;
  while (nextRow?.hidden) {
    nextRow = nextRow.nextElementSibling;
  }
  if (!nextRow) {
    return;
  }
  const nextRowInput = qs(`input[data-col-index="${colIndex}"]`, nextRow);
  if (nextRowInput) {
    nextRowInput.focus();
  }
}

function fertilizerEditorSortValue(row, key) {
  if (key.startsWith("comp:")) {
    return Number(row.comp?.[key.slice(5)]);
  }
  if (key === "weight_factor" || key === "solver_max_dose_per_l") {
    return row[key] === null ? Number.NaN : Number(row[key]);
  }
  if (key === "liquid") {
    return row.liquid ? 1 : 0;
  }
  return String(row[key] || "").trim();
}

function compareFertilizerEditorRows(left, right) {
  const { key, direction } = fertilizerEditorSort;
  const leftValue = fertilizerEditorSortValue(left.row, key);
  const rightValue = fertilizerEditorSortValue(right.row, key);
  const leftMissing = leftValue === "" || (typeof leftValue === "number" && !Number.isFinite(leftValue));
  const rightMissing = rightValue === "" || (typeof rightValue === "number" && !Number.isFinite(rightValue));
  if (leftMissing !== rightMissing) {
    return leftMissing ? 1 : -1;
  }
  let comparison = 0;
  if (typeof leftValue === "number" && typeof rightValue === "number") {
    comparison = leftValue - rightValue;
  } else {
    comparison = String(leftValue).localeCompare(String(rightValue), i18n.getLocale?.() || undefined, {
      numeric: true,
      sensitivity: "base",
    });
  }
  if (comparison === 0) {
    comparison = left.index - right.index;
  }
  return direction === "desc" ? -comparison : comparison;
}

function setFertilizerEditorSort(key) {
  fertilizerEditorSort = {
    key,
    direction: fertilizerEditorSort.key === key && fertilizerEditorSort.direction === "asc" ? "desc" : "asc",
  };
  renderFertilizerEditor();
}

function fertilizerEditorHeader(label, key, labelKey = null, title = "") {
  const active = fertilizerEditorSort.key === key;
  return {
    label,
    labelKey,
    title,
    onClick: () => setFertilizerEditorSort(key),
    sortDirection: active ? `${fertilizerEditorSort.direction}ending` : "none",
  };
}

function addFertilizerNameColumnResizer(table) {
  const header = table.querySelector("thead th:nth-child(2)");
  if (!header) {
    return;
  }
  const handle = document.createElement("span");
  handle.className = "column-resize-handle";
  handle.setAttribute("role", "separator");
  handle.setAttribute("aria-orientation", "vertical");
  handle.setAttribute("aria-label", t("editor.resizeNameColumn"));
  handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const startX = event.clientX;
    const startWidth = header.getBoundingClientRect().width;
    const onPointerMove = (moveEvent) => {
      fertilizerEditorNameWidthPx = Math.min(640, Math.max(180, startWidth + moveEvent.clientX - startX));
      table.style.setProperty("--fert-editor-name-width", `${fertilizerEditorNameWidthPx}px`);
    };
    const onPointerUp = () => {
      document.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("pointerup", onPointerUp);
    };
    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", onPointerUp);
  });
  header.appendChild(handle);
}

function applyFertilizerEditorFilter() {
  if (!fertilizerEditorTable) {
    return;
  }
  const query = fertilizerEditorFilter.trim().toLowerCase();
  const rows = Array.from(qsa("tr[data-editor-index]", fertilizerEditorTable));
  let firstVisibleIndex = null;
  let selectedVisible = false;
  rows.forEach((row) => {
    const editorIndex = Number(row.dataset.editorIndex);
    const name = fertilizerEditorRows[editorIndex]?.name || "";
    const visible = !query || name.toLowerCase().includes(query);
    row.hidden = !visible;
    if (visible && firstVisibleIndex === null) {
      firstVisibleIndex = editorIndex;
    }
    if (visible && editorIndex === fertilizerEditorSelectedIndex) {
      selectedVisible = true;
    }
  });
  if (!selectedVisible && firstVisibleIndex !== null) {
    setSelectedEditorRow(firstVisibleIndex);
  }
}

function renderFertilizerEditor() {
  if (!fertilizerEditorTableWrap || !isActive()) {
    return;
  }
  fertilizerEditorTableWrap.innerHTML = "";

  fertilizerEditorCompKeys = buildFertilizerCompKeys(fertilizerEditorRows);
  const sortedRows = fertilizerEditorRows
    .map((row, index) => ({ row, index }))
    .sort(compareFertilizerEditorRows);
  const indexDigitCount = String(Math.max(1, sortedRows.length)).length;
  const colgroupClasses = [
    "col-index",
    "col-name",
    "col-liquid",
    "col-weight",
    ...fertilizerEditorCompKeys.map(() => "col-nutrient"),
    "col-solver-max",
  ];
  const headerCells = [
    { label: "#" },
    fertilizerEditorHeader("Fertilizer name", "name", "editor.fertilizerName"),
    fertilizerEditorHeader("Liquid", "liquid", "common.liquid"),
    fertilizerEditorHeader("Density / factor", "weight_factor", "editor.densityFactor"),
    ...fertilizerEditorCompKeys.map((key) => fertilizerEditorHeader(key, `comp:${key}`)),
    fertilizerEditorHeader(
      "Solver max / L",
      "solver_max_dose_per_l",
      "editor.solverMaxDosePerL",
      t("editor.solverMaxDoseHint")
    ),
  ];
  const table = createTable({
    id: "fertilizerEditorTable",
    className: "grid grid--form grid--fertilizer grid--fertilizer-editor",
    colgroupClasses,
    headerCells,
  });
  fertilizerEditorTableWrap.appendChild(table.table);
  fertilizerEditorTable = table.table;
  fertilizerEditorTable.style.setProperty("--fert-editor-name-width", `${fertilizerEditorNameWidthPx}px`);
  addFertilizerNameColumnResizer(fertilizerEditorTable);
  fertilizerEditorTable.style.setProperty(
    "--fert-editor-index-width",
    `calc(${indexDigitCount}ch + (var(--space-2) * 2))`
  );

  sortedRows.forEach(({ row, index }, visibleIndex) => {
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

    const liquidCell = document.createElement("td");
    const liquidInput = document.createElement("input");
    liquidInput.type = "checkbox";
    liquidInput.checked = Boolean(row.liquid);
    liquidInput.dataset.rowIndex = index;
    liquidInput.dataset.field = "liquid";
    liquidInput.dataset.colIndex = colIndex;
    liquidInput.addEventListener("change", (event) => {
      row.liquid = event.target.checked;
    });
    liquidInput.addEventListener("keydown", handleEditorEnterKey);
    liquidCell.appendChild(liquidInput);
    tr.appendChild(liquidCell);
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
    weightInput.addEventListener("change", () => {
      normalizeDecimalInputElement(weightInput, row.weight_factor, "");
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
      input.addEventListener("change", () => {
        const percentValue = Number.isFinite(row.comp?.[key]) ? row.comp[key] * 100 : null;
        normalizeDecimalInputElement(input, percentValue, "");
      });
      input.addEventListener("keydown", handleEditorEnterKey);
      cell.appendChild(input);
      tr.appendChild(cell);
      colIndex += 1;
    });

    const solverMaxCell = document.createElement("td");
    const solverMaxInput = document.createElement("input");
    solverMaxInput.type = "text";
    solverMaxInput.inputMode = "decimal";
    solverMaxInput.value = Number.isFinite(row.solver_max_dose_per_l)
      ? formatNumber(row.solver_max_dose_per_l, solverMaxFormatter)
      : "";
    solverMaxInput.dataset.rowIndex = index;
    solverMaxInput.dataset.field = "solver_max_dose_per_l";
    solverMaxInput.dataset.colIndex = colIndex;
    solverMaxInput.title = t("editor.solverMaxDoseHint");
    solverMaxInput.addEventListener("input", (event) => {
      row.solver_max_dose_per_l = parseDecimalInput(event.target.value);
    });
    solverMaxInput.addEventListener("change", () => {
      normalizeDecimalInputElement(solverMaxInput, row.solver_max_dose_per_l, "");
    });
    solverMaxInput.addEventListener("keydown", handleEditorEnterKey);
    solverMaxCell.appendChild(solverMaxInput);
    tr.appendChild(solverMaxCell);

    table.tbody.appendChild(tr);
  });
  applyFertilizerEditorFilter();
}

async function refreshFertilizerCatalog() {
  const refreshedFertilizers = await api.fetchFertilizers(t("errors.loadFertilizers"));
  setFertilizerEditorData(refreshedFertilizers);
  onCatalogChange(refreshedFertilizers);
}

async function saveFertilizerEditor() {
  const payload = [];
  const seen = new Set();
  for (let index = 0; index < fertilizerEditorRows.length; index += 1) {
    const row = fertilizerEditorRows[index];
    const name = row.name.trim();
    if (!name) {
      notifications.reportError(null, t("editor.nameRequired"));
      focusEditorInput(index, "name");
      return;
    }
    if (seen.has(name)) {
      notifications.reportError(null, t("editor.uniqueNames"));
      focusEditorInput(index, "name");
      return;
    }
    seen.add(name);

    const weight = Number.isFinite(row.weight_factor) ? row.weight_factor : 1.0;
    const comp = {};
    Object.entries(row.comp || {}).forEach(([key, value]) => {
      if (Number.isFinite(value) && value > 0) {
        comp[key] = value;
      }
    });
    payload.push({
      name,
      liquid: Boolean(row.liquid),
      weight_factor: weight,
      comp,
      solver_max_dose_per_l: Number.isFinite(row.solver_max_dose_per_l)
        ? row.solver_max_dose_per_l
        : null,
    });
  }
  try {
    await api.putFertilizers(payload, t("errors.saveFailed"));
    await refreshFertilizerCatalog();
  } catch (error) {
    notifications.reportError(error, t("errors.saveFailed"));
  }
}

async function reloadFertilizerEditor() {
  try {
    await refreshFertilizerCatalog();
  } catch (error) {
      notifications.reportError(error, t("errors.loadFertilizers"));
  }
}

function addFertilizerEditorRow() {
  fertilizerEditorFilter = "";
  fertEditorSearchInput.value = "";
  if (fertilizerEditorSearchTimer) {
    clearTimeout(fertilizerEditorSearchTimer);
    fertilizerEditorSearchTimer = null;
  }
  fertilizerEditorRows.push({
    name: "",
    liquid: false,
    weight_factor: null,
    comp: {},
    solver_max_dose_per_l: null,
  });
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

function setData(fertilizers, preferredKeys = fertilizerEditorPreferredKeys) {
  fertilizerEditorPreferredKeys = preferredKeys || [];
  setFertilizerEditorData(fertilizers);
}

function mount() {
  if (mounted) return;
  mounted = true;
  fertEditorSearchInput.addEventListener("input", (event) => {
    fertilizerEditorFilter = event.target.value || "";
    if (fertilizerEditorSearchTimer) clearTimeout(fertilizerEditorSearchTimer);
    fertilizerEditorSearchTimer = window.setTimeout(() => {
      fertilizerEditorSearchTimer = null;
      applyFertilizerEditorFilter();
    }, 150);
  });
  fertEditorAddRowButton.addEventListener("click", addFertilizerEditorRow);
  fertEditorDeleteRowButton.addEventListener("click", deleteFertilizerEditorRow);
  fertEditorLoadButton.addEventListener("click", reloadFertilizerEditor);
  fertEditorSaveButton.addEventListener("click", saveFertilizerEditor);
}

function activate() {
  renderFertilizerEditor();
}

function deactivate() {
  fertilizerEditorTableWrap.replaceChildren();
  fertilizerEditorTable = null;
}

return {
  activate,
  deactivate,
  mount,
  refreshLocalized: renderFertilizerEditor,
  setData,
};
}
