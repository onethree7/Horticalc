export const HIERARCHICAL_MODEL = "hierarchical";
export const NNLS_TUNING_MODEL = "nnls_tuning";
export const DEFAULT_TARGET_PRIORITY = 3;

export function normalizedPriority(value, fallback = DEFAULT_TARGET_PRIORITY) {
  const priority = Number(value);
  return Number.isInteger(priority) && priority >= 0 && priority <= 4 ? priority : fallback;
}

export function solverModelLabel(model, t) {
  if (model === HIERARCHICAL_MODEL) return t("solver.model.hierarchical");
  return model === NNLS_TUNING_MODEL ? t("solver.model.nnlsTuning") : t("solver.model.massNnls");
}

export function targetPrioritySummary(data, key, t) {
  if (data?.solver_model !== HIERARCHICAL_MODEL) return "";
  const configured = data?.target_priorities?.[key];
  if (!configured) return "";
  const under = normalizedPriority(configured.under, 0);
  const over = normalizedPriority(configured.over, 0);
  if (under === 0 && over === 0) return t("solver.priority.reportOnlyResult");
  return t("solver.priority.resultSummary", {
    under: under || "–",
    over: over || "–",
  });
}
