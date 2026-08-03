export function formatClipboardIonLabel(key) {
  return key === "N_total" ? "N" : key;
}

export const NUTRIENT_SOLUTION_SETUP_FIELDS = [
  "liters",
  "water_profile",
  "osmosis_percent",
  "fertilizers_allowed",
  "fixed_grams",
  "urea_as_nh4",
  "solver_config",
];

export function positiveEntries(values = {}) {
  return Object.fromEntries(
    Object.entries(values).filter(([, value]) => Number(value) > 0),
  );
}

export function activeFixedAmountCount(values = {}) {
  return Object.keys(positiveEntries(values)).length;
}

export function nutrientSolutionHasSetup(solution = {}) {
  return NUTRIENT_SOLUTION_SETUP_FIELDS.some((field) =>
    Object.prototype.hasOwnProperty.call(solution, field)
  );
}

export function buildNutrientSolutionPayload({
  name,
  targets,
  includeSetup = false,
  liters,
  waterProfile,
  osmosisPercent,
  allowedFertilizers,
  fixedGrams,
  ureaAsNh4,
  solverConfig,
}) {
  const payload = {
    name,
    source: "Horticalc UI",
    targets_mg_per_l: targets,
  };
  if (!includeSetup) return payload;
  return {
    ...payload,
    liters,
    water_profile: String(waterProfile || "").replace(/\.yml$/i, ""),
    osmosis_percent: osmosisPercent,
    fertilizers_allowed: [...allowedFertilizers],
    fixed_grams: positiveEntries(fixedGrams),
    urea_as_nh4: ureaAsNh4,
    solver_config: solverConfig,
  };
}

export function buildSolvePayload({
  liters,
  targetValues,
  waterMgPerL,
  osmosisPercent,
  allowedFertilizers,
  fixedGrams,
  ureaAsNh4,
  solverConfig,
}) {
  return {
    liters,
    targets: positiveEntries(targetValues),
    water_profile: { mg_per_l: waterMgPerL, osmosis_percent: osmosisPercent },
    fertilizers_allowed: allowedFertilizers,
    fixed_grams: positiveEntries(fixedGrams),
    urea_as_nh4: ureaAsNh4,
    solver_config: solverConfig,
  };
}

export function solverResultDisplayKeys(data, summaryColumnOrder) {
  const nitrogenKeys = ["N_total", "N_NO3", "N_NH4", "N_UREA"];
  const orderedKeys = [
    ...nitrogenKeys,
    ...summaryColumnOrder.map(({ element }) => element).filter((key) => !nitrogenKeys.includes(key)),
  ];
  const seen = new Set(orderedKeys);
  const addKey = (key) => {
    if (key && !seen.has(key)) {
      seen.add(key);
      orderedKeys.push(key);
    }
  };
  Object.keys(data?.targets_mg_per_l || {}).forEach(addKey);
  Object.keys(data?.achieved_elements_mg_per_l || {}).forEach(addKey);
  (data?.objective_elements || []).forEach(addKey);
  return orderedKeys;
}
