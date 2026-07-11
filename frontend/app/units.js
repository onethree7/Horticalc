function parseDecimalInput(raw) {
  const s = String(raw ?? "").trim();
  if (!s) {
    return null;
  }
  const n = Number(s.replaceAll(",", "."));
  return Number.isFinite(n) ? n : null;
}

function decimalInputValue(raw, fallback = 0) {
  const parsed = parseDecimalInput(raw);
  return parsed === null ? fallback : parsed;
}

function normalizeDecimalInputElement(input, value, fallback = "0") {
  input.value = Number.isFinite(value) ? String(value) : fallback;
}

function validLiters(value) {
  const liters = parseDecimalInput(value);
  return Number.isFinite(liters) && liters > 0 ? liters : DEFAULT_LITERS;
}

function getVolumeUnitDefinition(unitKey = volumeUnit) {
  return volumeUnitDefinitions.find((definition) => definition.key === unitKey)
    || volumeUnitDefinitions.find((definition) => definition.key === DEFAULT_VOLUME_UNIT)
    || FALLBACK_VOLUME_UNITS[0];
}

function normalizeVolumeUnit(unitKey) {
  return volumeUnitDefinitions.some((definition) => definition.key === unitKey)
    ? unitKey
    : DEFAULT_VOLUME_UNIT;
}

function litersToDisplayVolume(liters, unitKey = volumeUnit) {
  return validLiters(liters) / getVolumeUnitDefinition(unitKey).liters_per_unit;
}

function displayVolumeToLiters(value, unitKey = volumeUnit) {
  const displayValue = parseDecimalInput(value);
  if (!Number.isFinite(displayValue)) {
    return null;
  }
  return displayValue * getVolumeUnitDefinition(unitKey).liters_per_unit;
}

function formatVolumeValue(value) {
  if (!Number.isFinite(value)) {
    return "";
  }
  return String(Math.round(value * 10000) / 10000);
}

function renderVolumeUnitOptions() {
  if (!configVolumeUnitSelect) {
    return;
  }
  configVolumeUnitSelect.replaceChildren();
  volumeUnitDefinitions.forEach((definition) => {
    const option = document.createElement("option");
    option.value = definition.key;
    option.textContent = definition.symbol;
    option.title = definition.label;
    configVolumeUnitSelect.appendChild(option);
  });
  configVolumeUnitSelect.value = normalizeVolumeUnit(volumeUnit);
}

function setVolumeUnit(unitKey) {
  volumeUnit = normalizeVolumeUnit(unitKey);
  if (configVolumeUnitSelect) {
    configVolumeUnitSelect.value = volumeUnit;
  }
  updateLitersDisplay();
}

function getMassUnitDefinition(unitKey = solidDoseUnit) {
  return massUnitDefinitions.find((definition) => definition.key === unitKey)
    || massUnitDefinitions.find((definition) => definition.key === DEFAULT_SOLID_DOSE_UNIT)
    || FALLBACK_MASS_UNITS[0];
}

function getLiquidVolumeUnitDefinition(unitKey = liquidDoseUnit) {
  return liquidVolumeUnitDefinitions.find((definition) => definition.key === unitKey)
    || liquidVolumeUnitDefinitions.find((definition) => definition.key === DEFAULT_LIQUID_DOSE_UNIT)
    || FALLBACK_LIQUID_VOLUME_UNITS[0];
}

function normalizeSolidDoseUnit(unitKey) {
  return massUnitDefinitions.some((definition) => definition.key === unitKey)
    ? unitKey
    : DEFAULT_SOLID_DOSE_UNIT;
}

function normalizeLiquidDoseUnit(unitKey) {
  return liquidVolumeUnitDefinitions.some((definition) => definition.key === unitKey)
    ? unitKey
    : DEFAULT_LIQUID_DOSE_UNIT;
}

function renderLinearUnitOptions(select, definitions, selectedUnit) {
  if (!select) {
    return;
  }
  select.replaceChildren();
  definitions.forEach((definition) => {
    const option = document.createElement("option");
    option.value = definition.key;
    option.textContent = definition.symbol;
    option.title = definition.label;
    select.appendChild(option);
  });
  select.value = selectedUnit;
}

function fertilizerDefinition(fertilizerOrName) {
  if (fertilizerOrName && typeof fertilizerOrName === "object") {
    return fertilizerOrName;
  }
  return fertilizerOptions.find((fertilizer) => fertilizer.name === fertilizerOrName) || null;
}

function doseUnitDefinition(fertilizerOrName) {
  return fertilizerDefinition(fertilizerOrName)?.liquid
    ? getLiquidVolumeUnitDefinition()
    : getMassUnitDefinition();
}

function canonicalDoseToDisplay(value, fertilizerOrName) {
  const canonicalValue = Number(value) || 0;
  const definition = doseUnitDefinition(fertilizerOrName);
  const factor = fertilizerDefinition(fertilizerOrName)?.liquid
    ? definition.milliliters_per_unit
    : definition.grams_per_unit;
  return canonicalValue / factor;
}

function displayDoseToCanonical(value, fertilizerOrName) {
  const displayValue = parseDecimalInput(value);
  if (!Number.isFinite(displayValue)) {
    return null;
  }
  const definition = doseUnitDefinition(fertilizerOrName);
  const factor = fertilizerDefinition(fertilizerOrName)?.liquid
    ? definition.milliliters_per_unit
    : definition.grams_per_unit;
  return displayValue * factor;
}

function formatDoseValue(value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return "-";
  }
  const absValue = Math.abs(numericValue);
  const decimals = absValue >= 1 ? 4 : absValue >= 0.01 ? 6 : 8;
  return numericValue
    .toFixed(decimals)
    .replace(/(\.\d*?[1-9])0+$/, "$1")
    .replace(/\.0+$/, "");
}

function formatDoseDisplay(value, fertilizerOrName) {
  return formatDoseValue(canonicalDoseToDisplay(value, fertilizerOrName));
}

function formatDoseInput(value, fertilizerOrName) {
  const formatted = formatDoseValue(canonicalDoseToDisplay(value, fertilizerOrName));
  return formatted === "-" ? "0" : formatted;
}

function appendDoseInput(valueCell, input, fertilizerOrName) {
  const wrapper = document.createElement("span");
  wrapper.className = "dose-input";
  const unit = document.createElement("span");
  unit.className = "dose-input-unit";
  unit.textContent = doseUnitDefinition(fertilizerOrName).symbol;
  wrapper.append(input, unit);
  valueCell.appendChild(wrapper);
}

function refreshDoseUnitDisplays() {
  renderSelectionTable();
  renderCalculatorTable();
  renderSolverFixedTable();
  if (lastSolveResult) {
    renderSolverResults(lastSolveResult);
  }
}

function setSolidDoseUnit(unitKey, { refresh = false } = {}) {
  solidDoseUnit = normalizeSolidDoseUnit(unitKey);
  if (configSolidDoseUnitSelect) {
    configSolidDoseUnitSelect.value = solidDoseUnit;
  }
  if (refresh) {
    refreshDoseUnitDisplays();
  }
  updateLitersDisplay();
}

function setLiquidDoseUnit(unitKey, { refresh = false } = {}) {
  liquidDoseUnit = normalizeLiquidDoseUnit(unitKey);
  if (configLiquidDoseUnitSelect) {
    configLiquidDoseUnitSelect.value = liquidDoseUnit;
  }
  if (refresh) {
    refreshDoseUnitDisplays();
  }
  updateLitersDisplay();
}

function updateLitersDisplay() {
  const definition = getVolumeUnitDefinition();
  const displayValue = formatVolumeValue(litersToDisplayVolume(currentLiters));
  if (configLitersInput) {
    configLitersInput.value = displayValue;
  }
  if (configLitersStatus) {
    configLitersStatus.setAttribute(
      "aria-label",
      `${t("config.solutionLiters")} ${displayValue} ${definition.symbol}`
    );
  }
  if (configVolumeUnitSymbol) {
    configVolumeUnitSymbol.textContent = definition.symbol;
  }
  if (configUnitSummary) {
    configUnitSummary.textContent = [
      definition.symbol,
      getMassUnitDefinition().symbol,
      getLiquidVolumeUnitDefinition().symbol,
    ].join(" · ");
  }
}

function scaleCurrentBatch(fromLiters, toLiters) {
  const oldLiters = validLiters(fromLiters);
  const newLiters = validLiters(toLiters);
  const factor = newLiters / oldLiters;
  calculatorRows.forEach((row) => {
    const scaled = roundScaledValue((Number(row.grams) || 0) * factor);
    row.grams = scaled;
    row.baseGrams =
      calculatorScaleFactor > 0 ? roundScaledValue(scaled / calculatorScaleFactor) : scaled;
  });
  Object.keys(solverFixedGrams).forEach((key) => {
    solverFixedGrams[key] = roundScaledValue((Number(solverFixedGrams[key]) || 0) * factor);
  });
}

function setCurrentLiters(value, { scaleBatch = false, recalculate = false, invalidateSolver = true } = {}) {
  const nextLiters = validLiters(value);
  const previousLiters = currentLiters;
  if (scaleBatch && previousLiters > 0 && nextLiters !== previousLiters) {
    scaleCurrentBatch(previousLiters, nextLiters);
    renderCalculatorTable();
    renderSolverFixedTable();
  }
  currentLiters = nextLiters;
  updateLitersDisplay();
  if (invalidateSolver) {
    renderSolverResults(null);
  }
  if (recalculate) {
    scheduleRecalculate();
  }
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

function convertWaterUnitValue(key, value, convert) {
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
  return convert(value, mm);
}

function mgToMol(key, value) {
  return convertWaterUnitValue(key, value, (mgValue, mm) => mgValue / mm);
}

function molToMg(key, value) {
  return convertWaterUnitValue(key, value, (molValue, mm) => molValue * mm);
}

function unitLabelForKey(key) {
  if (key === "KH") {
    return "°dKH";
  }
  return waterUnit === "mol_l" ? "mmol/L" : "mg/L";
}
