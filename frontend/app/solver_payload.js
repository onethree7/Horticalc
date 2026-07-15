export function formatClipboardIonLabel(key) {
  return key === "N_total" ? "N" : key;
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
  const positiveEntries = (values) => Object.fromEntries(
    Object.entries(values).filter(([, value]) => Number(value) > 0),
  );
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
