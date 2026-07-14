export const qs = (selector, root = document) => root.querySelector(selector);
export const qsa = (selector, root = document) => root.querySelectorAll(selector);

export function createSelect(options, onChange, emptyLabel) {
  const select = document.createElement("select");
  const emptyOption = document.createElement("option");
  emptyOption.value = "";
  emptyOption.textContent = emptyLabel;
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

export function createTable({ id, className, colgroupClasses, headerCells }) {
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
    const label = cell.label;
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
      if (cell.labelKey) th.dataset.i18n = cell.labelKey;
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

export function renderTableRows(tableBody, rowCount, buildRow) {
  tableBody.innerHTML = "";
  for (let i = 0; i < rowCount; i += 1) {
    tableBody.appendChild(buildRow(i));
  }
}
