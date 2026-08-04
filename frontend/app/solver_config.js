import { parseDecimalInput } from "./formatting.js";

export const NITROGEN_OBJECTIVE_TOTAL_ONLY = "n_total_only";
export const NITROGEN_OBJECTIVE_FORMS_ONLY = "n_forms_only";

const SUPPORTED_TYPES = new Set(["boolean", "number", "integer", "string"]);

function normalizeDefinition(definition) {
  const source = definition || {};
  return {
    key: String(source.key || ""),
    type: String(source.type || ""),
    defaultValue: Object.hasOwn(source, "default") ? source.default : source.defaultValue,
    minimum: source.minimum,
    maximum: source.maximum,
    exclusiveMinimum: source.exclusive_minimum ?? source.exclusiveMinimum,
    choices: Array.isArray(source.choices) ? [...source.choices] : [],
  };
}

export function normalizeSolverConfigDefinitions(definitions, fallbackDefinitions, hasControl) {
  const fallback = fallbackDefinitions.map(normalizeDefinition);
  if (!Array.isArray(definitions)) return fallback;

  const normalized = definitions
    .map(normalizeDefinition)
    .filter((definition) => definition.key
      && hasControl(definition.key)
      && SUPPORTED_TYPES.has(definition.type));
  if (!normalized.length) return fallback;

  const seenKeys = new Set(normalized.map(({ key }) => key));
  fallback.forEach((definition) => {
    if (!seenKeys.has(definition.key) && hasControl(definition.key)) {
      normalized.push(definition);
    }
  });
  return normalized;
}

export function sanitizeSolverConfig(config, definitions) {
  const allowedKeys = new Set(definitions.map(({ key }) => key));
  return Object.fromEntries(
    Object.entries(config || {}).filter(([key]) => allowedKeys.has(key)),
  );
}

function normalizedNumericValue(definition, rawValue) {
  let value = definition.type === "integer" ? Math.round(rawValue) : rawValue;
  if (Number.isFinite(definition.minimum)) value = Math.max(definition.minimum, value);
  if (Number.isFinite(definition.maximum)) value = Math.min(definition.maximum, value);
  if (Number.isFinite(definition.exclusiveMinimum) && value <= definition.exclusiveMinimum) {
    value = Number(definition.defaultValue);
  }
  return value;
}

export function buildSolverConfigPayload(definitions, controls) {
  const config = {};
  definitions.forEach((definition) => {
    const input = controls[definition.key];
    if (!input) return;
    if (definition.key === "nitrogen_objective_mode") {
      config[definition.key] = input.checked
        ? NITROGEN_OBJECTIVE_TOTAL_ONLY
        : NITROGEN_OBJECTIVE_FORMS_ONLY;
    } else if (definition.type === "boolean") {
      config[definition.key] = Boolean(input.checked);
    } else if (definition.type === "string") {
      config[definition.key] = String(input.value);
    } else {
      const rawValue = parseDecimalInput(input.value);
      if (rawValue !== null) config[definition.key] = normalizedNumericValue(definition, rawValue);
    }
  });
  return config;
}

export function applySolverConfig(definitions, controls, config = {}) {
  const sanitized = sanitizeSolverConfig(config, definitions);
  definitions.forEach((definition) => {
    const input = controls[definition.key];
    if (!input) return;
    const value = Object.hasOwn(sanitized, definition.key)
      ? sanitized[definition.key]
      : definition.defaultValue;
    if (definition.key === "nitrogen_objective_mode") {
      input.checked = value !== NITROGEN_OBJECTIVE_FORMS_ONLY;
    } else if (definition.type === "boolean") {
      input.checked = Boolean(value);
    } else if (definition.type === "string") {
      input.value = String(value);
    } else {
      input.value = String(value);
      if (Number.isFinite(definition.minimum)) input.min = String(definition.minimum);
      if (Number.isFinite(definition.maximum)) input.max = String(definition.maximum);
    }
  });
}
