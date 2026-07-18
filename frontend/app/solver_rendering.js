const NITROGEN_KEYS = ["N_total", "N_NO3", "N_NH4", "N_UREA"];

function appendEmptyFertilizerRow(tableBody, label) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 2;
  cell.textContent = label;
  row.appendChild(cell);
  tableBody.appendChild(row);
}

function appendFertilizerRows(tableBody, fertilizers, formatAmount) {
  fertilizers.forEach((fertilizer) => {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    nameCell.textContent = fertilizer.name;
    const amountCell = document.createElement("td");
    amountCell.textContent = formatAmount(fertilizer);
    row.append(nameCell, amountCell);
    tableBody.appendChild(row);
  });
}

function appendTargetRows(tableBody, data, displayKeys, labels, formatNutrient) {
  const targets = data.targets_mg_per_l || {};
  const achieved = data.achieved_elements_mg_per_l || {};
  const errors = data.errors_mg_per_l || {};
  const errorsPercent = data.errors_percent || {};
  const objectiveKeys = new Set(data.objective_elements || []);
  const ignoredKeys = new Set(data.ignored_elements || []);

  displayKeys.forEach((key) => {
    const row = document.createElement("tr");
    const keyCell = document.createElement("td");
    keyCell.textContent = ignoredKeys.has(key)
      ? `${labels[key] || key} · ${labels.ignored}`
      : labels[key] || key;
    if (ignoredKeys.has(key)) row.classList.add("solver-result-ignored");
    const nitrogenExtra = key !== "N_total" && NITROGEN_KEYS.includes(key);
    if (nitrogenExtra) keyCell.classList.add("solver-n-extra");

    const hasTarget = Number(targets[key]) > 0 || objectiveKeys.has(key);
    if (!hasTarget) row.classList.add("solver-result-inactive");
    const target = Number(targets[key] ?? 0);
    const actual = Number(achieved[key] ?? 0);
    const delta = Number.isFinite(errors[key]) ? Number(errors[key]) : actual - target;
    const percent = Number.isFinite(errorsPercent[key])
      ? Number(errorsPercent[key])
      : target ? (actual - target) / target * 100 : NaN;
    const values = [
      hasTarget ? formatNutrient(target) : "-",
      formatNutrient(actual),
      formatNutrient(delta),
      Number.isFinite(percent) ? `${percent.toFixed(1)}%` : "-",
    ];
    const cells = values.map((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      if (nitrogenExtra) cell.classList.add("solver-n-extra");
      return cell;
    });
    if (nitrogenExtra) row.classList.add("solver-n-row");
    row.append(keyCell, ...cells);
    tableBody.appendChild(row);
  });
}

export function renderSolverTables({
  data,
  fertilizersTable,
  targetsTable,
  noFertilizersLabel,
  formatAmount,
  displayKeys,
  labels,
  formatNutrient,
}) {
  fertilizersTable.replaceChildren();
  targetsTable.replaceChildren();
  const fertilizers = Array.isArray(data?.fertilizers) ? data.fertilizers : [];
  if (fertilizers.length) appendFertilizerRows(fertilizersTable, fertilizers, formatAmount);
  else appendEmptyFertilizerRow(fertilizersTable, noFertilizersLabel);
  if (data) appendTargetRows(targetsTable, data, displayKeys, labels, formatNutrient);
}
