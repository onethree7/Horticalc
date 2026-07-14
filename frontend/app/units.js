import {
  DEFAULT_LIQUID_DOSE_UNIT,
  DEFAULT_LITERS,
  DEFAULT_SOLID_DOSE_UNIT,
  DEFAULT_VOLUME_UNIT,
  FALLBACK_LIQUID_VOLUME_UNITS,
  FALLBACK_MASS_UNITS,
  FALLBACK_VOLUME_UNITS,
} from "./constants.js";
import { parseDecimalInput } from "./formatting.js";

export function createUnitService({ onLitersChange = () => {}, onDoseUnitsChange = () => {} } = {}) {
  let liters = DEFAULT_LITERS;
  let volumeUnits = [...FALLBACK_VOLUME_UNITS];
  let massUnits = [...FALLBACK_MASS_UNITS];
  let liquidVolumeUnits = [...FALLBACK_LIQUID_VOLUME_UNITS];
  let volumeUnit = DEFAULT_VOLUME_UNIT;
  let solidDoseUnit = DEFAULT_SOLID_DOSE_UNIT;
  let liquidDoseUnit = DEFAULT_LIQUID_DOSE_UNIT;
  let fertilizers = [];

  const findDefinition = (definitions, key, canonical, fallback) =>
    definitions.find((definition) => definition.key === key)
    || definitions.find((definition) => definition.key === canonical)
    || fallback;

  const validLiters = (value) => {
    const parsed = parseDecimalInput(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_LITERS;
  };

  function configure(definitions = {}) {
    volumeUnits = definitions.volumeUnits?.length ? definitions.volumeUnits : [...FALLBACK_VOLUME_UNITS];
    massUnits = definitions.massUnits?.length ? definitions.massUnits : [...FALLBACK_MASS_UNITS];
    liquidVolumeUnits = definitions.liquidVolumeUnits?.length
      ? definitions.liquidVolumeUnits
      : [...FALLBACK_LIQUID_VOLUME_UNITS];
    volumeUnit = normalizeVolumeUnit(volumeUnit);
    solidDoseUnit = normalizeSolidDoseUnit(solidDoseUnit);
    liquidDoseUnit = normalizeLiquidDoseUnit(liquidDoseUnit);
  }

  function getVolumeUnitDefinition(key = volumeUnit) {
    return findDefinition(volumeUnits, key, DEFAULT_VOLUME_UNIT, FALLBACK_VOLUME_UNITS[0]);
  }
  function getMassUnitDefinition(key = solidDoseUnit) {
    return findDefinition(massUnits, key, DEFAULT_SOLID_DOSE_UNIT, FALLBACK_MASS_UNITS[0]);
  }
  function getLiquidVolumeUnitDefinition(key = liquidDoseUnit) {
    return findDefinition(
      liquidVolumeUnits,
      key,
      DEFAULT_LIQUID_DOSE_UNIT,
      FALLBACK_LIQUID_VOLUME_UNITS[0],
    );
  }
  function normalizeVolumeUnit(key) {
    return volumeUnits.some((definition) => definition.key === key) ? key : DEFAULT_VOLUME_UNIT;
  }
  function normalizeSolidDoseUnit(key) {
    return massUnits.some((definition) => definition.key === key) ? key : DEFAULT_SOLID_DOSE_UNIT;
  }
  function normalizeLiquidDoseUnit(key) {
    return liquidVolumeUnits.some((definition) => definition.key === key)
      ? key
      : DEFAULT_LIQUID_DOSE_UNIT;
  }
  function litersToDisplayVolume(value, key = volumeUnit) {
    return validLiters(value) / getVolumeUnitDefinition(key).liters_per_unit;
  }
  function displayVolumeToLiters(value, key = volumeUnit) {
    const parsed = parseDecimalInput(value);
    return Number.isFinite(parsed) ? parsed * getVolumeUnitDefinition(key).liters_per_unit : null;
  }
  function formatVolumeValue(value) {
    return Number.isFinite(value) ? String(Math.round(value * 10000) / 10000) : "";
  }
  function fertilizerDefinition(fertilizerOrName) {
    if (fertilizerOrName && typeof fertilizerOrName === "object") return fertilizerOrName;
    return fertilizers.find((fertilizer) => fertilizer.name === fertilizerOrName) || null;
  }
  function doseUnitDefinition(fertilizerOrName) {
    return fertilizerDefinition(fertilizerOrName)?.liquid
      ? getLiquidVolumeUnitDefinition()
      : getMassUnitDefinition();
  }
  function canonicalDoseToDisplay(value, fertilizerOrName) {
    const definition = doseUnitDefinition(fertilizerOrName);
    const factor = fertilizerDefinition(fertilizerOrName)?.liquid
      ? definition.milliliters_per_unit
      : definition.grams_per_unit;
    return (Number(value) || 0) / factor;
  }
  function displayDoseToCanonical(value, fertilizerOrName) {
    const parsed = parseDecimalInput(value);
    if (!Number.isFinite(parsed)) return null;
    const definition = doseUnitDefinition(fertilizerOrName);
    const factor = fertilizerDefinition(fertilizerOrName)?.liquid
      ? definition.milliliters_per_unit
      : definition.grams_per_unit;
    return parsed * factor;
  }
  function formatDoseValue(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "-";
    const abs = Math.abs(numeric);
    const decimals = abs >= 1 ? 4 : abs >= 0.01 ? 6 : 8;
    return numeric.toFixed(decimals).replace(/(\.\d*?[1-9])0+$/, "$1").replace(/\.0+$/, "");
  }

  return {
    configure,
    setFertilizers(value) { fertilizers = value || []; },
    get liters() { return liters; },
    get volumeUnit() { return volumeUnit; },
    get solidDoseUnit() { return solidDoseUnit; },
    get liquidDoseUnit() { return liquidDoseUnit; },
    get volumeUnits() { return volumeUnits; },
    get massUnits() { return massUnits; },
    get liquidVolumeUnits() { return liquidVolumeUnits; },
    getVolumeUnitDefinition,
    getMassUnitDefinition,
    getLiquidVolumeUnitDefinition,
    litersToDisplayVolume,
    displayVolumeToLiters,
    formatVolumeValue,
    doseUnitDefinition,
    displayDoseToCanonical,
    formatDoseDisplay(value, fertilizer) {
      return formatDoseValue(canonicalDoseToDisplay(value, fertilizer));
    },
    formatDoseInput(value, fertilizer) {
      const formatted = formatDoseValue(canonicalDoseToDisplay(value, fertilizer));
      return formatted === "-" ? "0" : formatted;
    },
    setVolumeUnit(value) { volumeUnit = normalizeVolumeUnit(value); },
    setSolidDoseUnit(value, notify = false) {
      solidDoseUnit = normalizeSolidDoseUnit(value);
      if (notify) onDoseUnitsChange();
    },
    setLiquidDoseUnit(value, notify = false) {
      liquidDoseUnit = normalizeLiquidDoseUnit(value);
      if (notify) onDoseUnitsChange();
    },
    setLiters(value, options = {}) {
      const previousLiters = liters;
      const nextLiters = validLiters(value);
      liters = nextLiters;
      onLitersChange({ previousLiters, nextLiters, ...options });
    },
  };
}
