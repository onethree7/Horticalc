calculatorRows = [createCalculatorRow()];
function roundScaledValue(value) {
  return Math.round(value * 1000) / 1000;
}

function createCalculatorRow(name = "", grams = 0) {
  const normalizedGrams = Math.max(0, Number(grams) || 0);
  return {
    name,
    grams: normalizedGrams,
    baseGrams: roundScaledValue(normalizedGrams),
  };
}

function roundScaleFactor(value) {
  return Math.round(value * 100) / 100;
}

function updateScaleDisplay(displayEl, factor) {
  if (displayEl) {
    displayEl.textContent = `${factor.toFixed(2)}x`;
  }
}

function applyScaleFactor({
  nextFactor,
  definitions,
  getBaseValue,
  setScaledValue,
  setFactor,
  render,
  displayEl,
}) {
  const factor = Math.max(0, roundScaleFactor(nextFactor));
  setFactor(factor);
  definitions.forEach((definition) => {
    const baseValue = getBaseValue(definition) || 0;
    const scaledValue = roundScaledValue(baseValue * factor);
    setScaledValue(definition, Math.max(0, scaledValue));
  });
  updateScaleDisplay(displayEl, factor);
  render();
}

function updateSolverTargetScaleDisplay() {
  updateScaleDisplay(solverTargetScaleValue, solverTargetScaleFactor);
}

function applySolverTargetScaleFactor(nextFactor) {
  applyScaleFactor({
    nextFactor,
    definitions: solverTargetDefinitions,
    getBaseValue: (field) => solverTargetBaseValues[field.key],
    setScaledValue: (field, value) => {
      solverTargetValues[field.key] = value;
    },
    setFactor: (factor) => {
      solverTargetScaleFactor = factor;
    },
    render: renderSolverTargetsTable,
    displayEl: solverTargetScaleValue,
  });
}

function updateCalculatorScaleDisplay() {
  updateScaleDisplay(calculatorScaleValue, calculatorScaleFactor);
}

function applyCalculatorScaleFactor(nextFactor) {
  applyScaleFactor({
    nextFactor,
    definitions: calculatorRows,
    getBaseValue: (row) => row.baseGrams,
    setScaledValue: (row, value) => {
      row.grams = value;
    },
    setFactor: (factor) => {
      calculatorScaleFactor = factor;
    },
    render: renderCalculatorTable,
    displayEl: calculatorScaleValue,
  });
  scheduleRecalculate();
}

function bindScaleButtons(downButton, upButton, currentFactor, applyFactor) {
  if (downButton) {
    downButton.addEventListener("click", () => {
      applyFactor(currentFactor() - SCALE_STEP);
    });
  }
  if (upButton) {
    upButton.addEventListener("click", () => {
      applyFactor(currentFactor() + SCALE_STEP);
    });
  }
}

function applySolverResultToCalculator({ switchToCalculator = false } = {}) {
  if (!lastSolveResult) {
    reportError(null, t("solver.noResult"));
    return false;
  }
  const fertilizers = (lastSolveResult.fertilizers || []).map((fert) => ({
    name: fert.name,
    grams: Number(fert.grams || 0),
  }));
  const recipe = {
    liters: currentLiters,
    fertilizers,
  };
  applyRecipe(recipe);
  scheduleRecalculate();
  setSolverApplyStatus(t("status.appliedCalculator"));

  if (switchToCalculator) {
    showShellView("fertilizers");
  }
  return true;
}

function formatClipboardIonLabel(key) {
  if (key === "N_total") {
    return "N";
  }
  return key;
}

function buildClipboardRows(headers, rows, numericColumns = []) {
  const allRows = headers ? [headers, ...rows] : rows;
  const widths = allRows.reduce((currentWidths, row) => {
    row.forEach((cell, index) => {
      currentWidths[index] = Math.max(currentWidths[index] || 0, String(cell).length);
    });
    return currentWidths;
  }, []);
  const numericColumnSet = new Set(numericColumns);

  return allRows.map((row) =>
    row
      .map((cell, index) => {
        const value = String(cell);
        return numericColumnSet.has(index)
          ? value.padStart(widths[index])
          : value.padEnd(widths[index]);
      })
      .join("  ")
      .trimEnd()
  );
}

function buildCalculatorClipboardText() {
  const fertilizers = buildSelectedFertilizerEntries();
  const lines = [t("calculator.clipboardTitle")];
  lines.push(
    ...buildClipboardRows(null, [
      [
        t("solver.clipboardBatchVolume", { unit: getVolumeUnitDefinition().symbol }),
        formatVolumeValue(litersToDisplayVolume(currentLiters)),
      ],
      [t("solver.clipboardOsmosis"), formatNumber(decimalInputValue(osmosisPercentInput.value))],
    ], [1])
  );
  lines.push("");
  lines.push(
    ...buildClipboardRows(
      [t("common.fertilizer"), t("common.amount"), t("common.unit")],
      fertilizers.map((fertilizer) => [
        fertilizer.name,
        formatDoseDisplay(fertilizer.grams, fertilizer.name),
        doseUnitDefinition(fertilizer.name).symbol,
      ]),
      [1]
    )
  );

  const npkMetrics = lastCalculation?.npk_metrics || {};
  lines.push("");
  lines.push(t("solver.clipboardNpk"));
  lines.push(
    ...buildClipboardRows(null, [
      [t("live.npkTotal"), npkMetrics.npk_all_pct || "-"],
      [t("live.npkPNorm"), npkMetrics.npk_p_norm || "-"],
      [t("live.npkRatio"), npkMetrics.npk_npk_pct || "-"],
    ], [1])
  );

  const solutionEc = lastCalculation?.ec?.ec_mS_per_cm || {};
  const waterEc = lastCalculation?.ec_water?.ec_mS_per_cm || {};
  lines.push("");
  lines.push(t("live.ec"));
  lines.push(
    ...buildClipboardRows(null, [
      [`${t("live.solution")} 25°C`, formatNumber(Number(solutionEc["25.0"]))],
      [`${t("live.solution")} 18°C`, formatNumber(Number(solutionEc["18.0"]))],
      [`${t("live.water")} 25°C`, formatNumber(Number(waterEc["25.0"]))],
      [`${t("live.water")} 18°C`, formatNumber(Number(waterEc["18.0"]))],
    ], [1])
  );

  const elementValues = lastCalculation?.elements_mg_per_l || {};
  lines.push("");
  lines.push(t("solver.clipboardIons"));
  lines.push(
    ...buildClipboardRows(
      null,
      summaryColumnOrder.map((column) => [
        t(column.ionHeaderLabelKey || column.ionHeaderLabel),
        formatNumber(Number(elementValues[column.element]), nutrientFormatter),
      ]),
      [1]
    )
  );

  const oxideValues = lastCalculation?.oxides_mg_per_l || {};
  lines.push("");
  lines.push(`${t("calculator.oxideForms")} (mg/L)`);
  lines.push(
    ...buildClipboardRows(
      null,
      summaryColumnOrder.map((column) => [
        t(column.oxideHeaderLabelKey || column.oxideHeaderLabel),
        formatOxideValue(column.oxide, Number(oxideValues[column.oxide])),
      ]),
      [1]
    )
  );

  const ionValues = lastCalculation?.ions_meq_per_l || {};
  lines.push("");
  lines.push(`${t("calculator.ions")} (meq/L)`);
  lines.push(
    ...buildClipboardRows(
      null,
      Object.entries(ionValues)
        .filter(([, value]) => Number.isFinite(Number(value)))
        .map(([key, value]) => [key, formatNumber(Number(value), ionFormatter)]),
      [1]
    )
  );

  const balance = lastCalculation?.ion_balance || {};
  const rawCbe = Number(balance.raw_cbe_percent_signed ?? balance.error_percent_signed);
  const dinCbe = Number.isFinite(Number(balance.din_38402_62_percent_signed))
    ? Number(balance.din_38402_62_percent_signed)
    : rawCbe * 2;
  lines.push("");
  lines.push(t("calculator.ionBalance"));
  lines.push(
    ...buildClipboardRows(
      [t("common.parameter"), t("common.value"), t("common.unit")],
      [
        [t("calculator.ionBalance.cations"), formatNumber(Number(balance.cations_meq_per_l), ionFormatter), "meq/L"],
        [t("calculator.ionBalance.anions"), formatNumber(Number(balance.anions_meq_per_l), ionFormatter), "meq/L"],
        [t("calculator.ionBalance.cbeRaw"), formatNumber(rawCbe, ionFormatter), "%"],
        [t("calculator.ionBalance.dinRaw"), formatNumber(dinCbe, ionFormatter), "%"],
      ],
      [1]
    )
  );

  return lines.join("\n");
}

async function copyCalculatorResultsToClipboard() {
  if (!lastCalculation || !calculatorResultCurrent) {
    reportError(null, t("calculator.noResult"));
    return;
  }

  try {
    await copyTextWithFallback(buildCalculatorClipboardText());
    setCopyCalculatorStatus(t("status.copied"));
  } catch (error) {
    reportError(error, t("errors.copyFailed"));
    setCopyCalculatorStatus(t("status.copyFailed"));
  }
}

function renderSelectionTable() {
  renderTableRows(fertilizerSelectTable, calculatorRows.length, (i) => {
    const calculatorRow = calculatorRows[i];
    const row = document.createElement("tr");

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const selectCell = document.createElement("td");
    const select = createSelect(fertilizerOptions, (value) => {
      calculatorRow.name = value;
      renderSelectionTable();
      renderCalculatorTable();
      scheduleRecalculate();
    });
    select.value = calculatorRow.name;
    selectCell.appendChild(select);

    const selectedOption = fertilizerOptions.find((option) => option.name === calculatorRow.name);

    const liquidCell = document.createElement("td");
    liquidCell.textContent = calculatorRow.name
      ? selectedOption?.liquid
        ? t("common.liquid")
        : t("common.solid")
      : "-";

    const weightCell = document.createElement("td");
    if (!selectedOption) {
      weightCell.textContent = "-";
    } else if (selectedOption.liquid) {
      weightCell.textContent = `${formatNumber(selectedOption.weight_factor, nutrientFormatter)} g/mL`;
    } else if (Number(selectedOption.weight_factor) !== 1) {
      weightCell.textContent = `${formatNumber(selectedOption.weight_factor, nutrientFormatter)}×`;
    } else {
      weightCell.textContent = "—";
    }

    row.append(indexCell, selectCell, liquidCell, weightCell);
    return row;
  });
}

function renderCalculatorTable() {
  renderTableRows(calculatorTable, calculatorRows.length, (i) => {
    const calculatorRow = calculatorRows[i];
    const row = document.createElement("tr");
    if (calculatorRow.baseGrams === undefined) {
      const currentAmount = Math.max(0, Number(calculatorRow.grams) || 0);
      calculatorRow.baseGrams =
        calculatorScaleFactor > 0 ? roundScaledValue(currentAmount / calculatorScaleFactor) : 0;
    }

    const indexCell = document.createElement("td");
    indexCell.textContent = `${i + 1}`;

    const nameCell = document.createElement("td");
    nameCell.textContent = calculatorRow.name || "-";
    nameCell.colSpan = 2;

    const amountCell = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.min = "0";
    input.step = "any";
    input.value = formatDoseInput(calculatorRow.grams, calculatorRow.name);
    input.addEventListener("input", (event) => {
      const canonicalValue = displayDoseToCanonical(event.target.value, calculatorRow.name);
      if (canonicalValue === null || canonicalValue < 0) {
        return;
      }
      calculatorRow.grams = canonicalValue;
      calculatorRow.baseGrams =
        calculatorScaleFactor > 0 ? roundScaledValue(canonicalValue / calculatorScaleFactor) : 0;
      scheduleRecalculate();
    });
    input.addEventListener("change", () => {
      input.value = formatDoseInput(calculatorRow.grams, calculatorRow.name);
    });
    appendDoseInput(amountCell, input, calculatorRow.name);

    row.append(indexCell, nameCell, amountCell);
    return row;
  });
}

function scheduleRecalculate() {
  const requestVersion = calculationRequests.reserve();
  setCalculatorResultCurrent(false);
  if (recalculateTimer) {
    clearTimeout(recalculateTimer);
  }
  recalculateTimer = setTimeout(async () => {
    try {
      await calculateAndRender(null, requestVersion);
    } catch (error) {
      reportError(error, t("errors.calculateFailed"));
    }
  }, 250);
}


function buildSelectedFertilizerEntries({ allowZeroGrams = false } = {}) {
  return calculatorRows
    .map((row) => ({
      name: row.name,
      grams: Number(row.grams) || 0,
    }))
    .filter((entry) => entry.name && (allowZeroGrams || entry.grams > 0));
}

function renderCalculation(data, { resultCurrent = true } = {}) {
  lastCalculation = data;
  const oxides = data.oxides_mg_per_l || {};
  const elements = data.elements_mg_per_l || {};
  const npkMetrics = data.npk_metrics || {};
  const waterElements = data.water_elements_mg_per_l || {};
  const waterDisplay = waterElementsForDisplay(waterElements);
  renderWaterSummaryTable(waterSummaryTable, waterDisplay);
  renderOxideSummaryTable(oxideSummaryTable, oxides);
  renderIonSummaryTable(ionSummaryTable, elements);

  const ionMeqEntries = Object.entries(data.ions_meq_per_l || {});
  renderIonCompactList(ionMeqList, ionMeqEntries);

  const ionBalanceEntries = Object.entries(data.ion_balance || {});
  renderIonBalanceCompact(ionBalanceList, ionBalanceEntries);

  npkAllPctValue.textContent = npkMetrics.npk_all_pct || "-";
  npkPNormValue.textContent = npkMetrics.npk_p_norm || "-";
  npkNpkPctValue.textContent = npkMetrics.npk_npk_pct || "-";
  renderIonRatios(npkMetrics);

  const ec = data.ec || {};
  renderEcPair(ec.ec_mS_per_cm || {}, ec18Value, ec25Value);

  const waterEc = data.ec_water || {};
  renderEcPair(waterEc.ec_mS_per_cm || {}, ecWater18Value, ecWater25Value);
  updateLiveResultBar(data);
  setCalculatorResultCurrent(resultCurrent);
}

function applyRecipe(recipe, { applyLiters = true } = {}) {
  if (applyLiters && recipe && recipe.liters !== undefined && recipe.liters !== null) {
    setCurrentLiters(recipe.liters, { scaleBatch: false, recalculate: false, invalidateSolver: false });
  }
  const fertilizers = Array.isArray(recipe.fertilizers) ? recipe.fertilizers : [];
  calculatorRows.length = 0;
  calculatorScaleFactor = 1.0;

  fertilizers.forEach((entry) => {
    const name = entry.name || "";
    const grams = Math.max(0, Number(entry.grams) || 0);
    calculatorRows.push(createCalculatorRow(name, grams));
  });

  if (!calculatorRows.length) {
    calculatorRows.push(createCalculatorRow());
  }

  updateCalculatorScaleDisplay();
  renderSelectionTable();
  renderCalculatorTable();
}

function collectSelectedFertilizerNames() {
  const names = calculatorRows.map((row) => row.name).filter(Boolean);
  return Array.from(new Set(names));
}

function addFertilizerRow() {
  calculatorRows.push(createCalculatorRow());
  renderSelectionTable();
  renderCalculatorTable();
}

function removeFertilizerRow() {
  if (calculatorRows.length <= 1) {
    return;
  }

  calculatorRows.pop();
  renderSelectionTable();
  renderCalculatorTable();
}

function buildRecipePayloadFromSelection(name) {
  const fertilizers = buildSelectedFertilizerEntries();
  return buildRecipePayload(name, fertilizers, currentLiters, false);
}

function buildRecipePayloadFromSolver(name) {
  const fertilizers = Array.isArray(lastSolveResult?.fertilizers) ? lastSolveResult.fertilizers : [];
  return buildRecipePayload(
    name,
    fertilizers,
    currentLiters,
    solverUreaToggle.checked
  );
}

function buildSolutionSnapshot() {
  const fertilizers = buildSelectedFertilizerEntries({ allowZeroGrams: true });
  return {
    water_profile_value: waterProfileSelect.value || "",
    osmosis_percent: decimalInputValue(osmosisPercentInput.value),
    water_unit: waterUnit,
    liters: currentLiters,
    water_values: { ...waterValues },
    fertilizers,
  };
}
