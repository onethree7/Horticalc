import { roundScaledValue } from "./formatting.js";

export function roundScaleFactor(value) {
  return Math.round(value * 100) / 100;
}

export function scaledValues(definitions, nextFactor, getBaseValue) {
  const factor = Math.max(0, roundScaleFactor(nextFactor));
  return {
    factor,
    values: definitions.map((definition) => Math.max(
      0,
      roundScaledValue((getBaseValue(definition) || 0) * factor),
    )),
  };
}

export function applyScaledValues(definitions, nextFactor, getBaseValue, setValue) {
  const scaled = scaledValues(definitions, nextFactor, getBaseValue);
  definitions.forEach((definition, index) => setValue(definition, scaled.values[index]));
  return scaled.factor;
}

export function scaleAmountsByVolume(values, previousLiters, nextLiters) {
  const factor = nextLiters / previousLiters;
  return Object.fromEntries(Object.entries(values).map(([key, value]) => [
    key,
    roundScaledValue((Number(value) || 0) * factor),
  ]));
}

export function bindScaleButtons(downButton, upButton, currentFactor, applyFactor, step = 0.05) {
  downButton?.addEventListener("click", () => applyFactor(currentFactor() - step));
  upButton?.addEventListener("click", () => applyFactor(currentFactor() + step));
}
