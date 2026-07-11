const qs = (selector, root = document) => root.querySelector(selector);
const qsa = (selector, root = document) => root.querySelectorAll(selector);
const { createLatestRequestGate } = window.HorticalcRequestGate;

function createSelect(options, onChange) {
  const select = document.createElement("select");
  const emptyOption = document.createElement("option");
  emptyOption.value = "";
  emptyOption.textContent = t("common.selectEmpty");
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
    const label = cell.labelKey ? t(cell.labelKey) : cell.label;
    if (cell.onClick) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "table-sort-button";
      button.textContent = label;
      button.addEventListener("click", cell.onClick);
      th.classList.add("is-sortable");
      th.setAttribute("aria-sort", cell.sortDirection || "none");
      th.appendChild(button);
    } else {
      if (cell.labelKey) {
        th.dataset.i18n = cell.labelKey;
      }
      th.textContent = label;
    }
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
    colgroupClasses: ["col-index", "col-name", "col-liquid", "col-weight"],
    headerCells: [
      { label: "#" },
      { labelKey: "calculator.fertilizerDropdown", label: "Fertilizer (dropdown)" },
      { labelKey: "common.productType", label: "Type" },
      { labelKey: "editor.densityFactor", label: "Density / factor" },
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
      { labelKey: "editor.fertilizerName", label: "Fertilizer name", colSpan: 2 },
      { labelKey: "common.amount", label: "Amount" },
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

function releaseInactiveHeavyViews() {
  if (currentShellView !== "editor") {
    fertilizerEditorTableWrap.replaceChildren();
    fertilizerEditorTable = null;
  }
  if (currentShellView !== "solver") {
    solverAllowedFertilizersSelect.replaceChildren();
    solverFixedTable.replaceChildren();
  }
}

function renderActiveHeavyView() {
  if (currentShellView === "editor") {
    renderFertilizerEditor();
  } else if (currentShellView === "solver") {
    renderSolverAllowedOptions();
    renderSolverFixedTable();
  }
}
