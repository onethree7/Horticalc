import { NUTRIENT_FORMATTER, SUMMARY_COLUMN_ORDER } from "./constants.js";
import { buildAlignedRows, formatNumber } from "./formatting.js";
import { formatClipboardIonLabel, solverResultDisplayKeys } from "./solver_payload.js";
import { solverModelLabel, targetPrioritySummary } from "./solver_presentation.js";

export const printableSolverModelLabel = solverModelLabel;
export const printableTargetPrioritySummary = targetPrioritySummary;

export function buildSolverPrintableText({
  result,
  calculation = {},
  liters,
  osmosisPercent = 0,
  fertilizerKinds = {},
  t,
  units,
}) {
  const fertilizers = Array.isArray(result?.fertilizers) ? result.fertilizers : [];
  const lines = [t("solver.clipboardTitle")];
  lines.push(
    ...buildAlignedRows(
      null,
      [
        [
          t("solver.clipboardBatchVolume", { unit: units.getVolumeUnitDefinition().symbol }),
          units.formatVolumeValue(units.litersToDisplayVolume(Number(liters) || 0)),
        ],
        [t("solver.clipboardOsmosis"), formatNumber(Number(osmosisPercent))],
        [t("solver.modelLabel"), solverModelLabel(result?.solver_model, t)],
      ],
      [1],
    ),
  );
  lines.push("");
  lines.push(
    ...buildAlignedRows(
      [t("common.fertilizer"), t("common.amount"), t("common.unit")],
      fertilizers.map((fertilizer) => {
        const name = fertilizer.name || "";
        const kind = fertilizerKinds[name];
        const definition = kind ? { name, liquid: kind === "liquid" } : name;
        return [
          name,
          units.formatDoseDisplay(Number(fertilizer.grams), definition),
          units.doseUnitDefinition(definition).symbol,
        ];
      }),
      [1],
    ),
  );

  const npkMetrics = calculation?.npk_metrics || {};
  const ecValues = calculation?.ec?.ec_mS_per_cm || {};
  const ionValues = calculation?.elements_mg_per_l || {};
  lines.push("");
  lines.push(t("solver.clipboardNpk"));
  lines.push(
    ...buildAlignedRows(
      null,
      [
        [t("live.npkTotal"), npkMetrics.npk_all_pct || "-"],
        [t("live.npkPNorm"), npkMetrics.npk_p_norm || "-"],
        [t("live.npkRatio"), npkMetrics.npk_npk_pct || "-"],
      ],
      [1],
    ),
  );

  lines.push("");
  lines.push(t("live.ec"));
  lines.push(
    ...buildAlignedRows(
      null,
      [
        [`${t("common.ec")} 25°C`, formatNumber(Number(ecValues["25.0"]))],
        [`${t("common.ec")} 18°C`, formatNumber(Number(ecValues["18.0"]))],
      ],
      [1],
    ),
  );

  lines.push("");
  lines.push(t("solver.clipboardTargets"));
  const targets = result?.targets_mg_per_l || {};
  const achieved = result?.achieved_elements_mg_per_l || {};
  const errors = result?.errors_mg_per_l || {};
  const solverRows = solverResultDisplayKeys(result, SUMMARY_COLUMN_ORDER).map((key) => {
    const targetValue = Number(targets[key] ?? 0);
    const achievedValue = Number(achieved[key] ?? 0);
    const errorValue = Number.isFinite(errors[key])
      ? Number(errors[key])
      : achievedValue - targetValue;
    return [
      [formatClipboardIonLabel(key), targetPrioritySummary(result, key, t)]
        .filter(Boolean)
        .join(" · "),
      targetValue > 0 ? formatNumber(targetValue, NUTRIENT_FORMATTER) : "-",
      formatNumber(achievedValue, NUTRIENT_FORMATTER),
      formatNumber(errorValue, NUTRIENT_FORMATTER),
    ];
  });
  lines.push(
    ...buildAlignedRows(
      [t("common.element"), t("common.target"), t("common.achieved"), t("common.delta")],
      solverRows,
      [1, 2, 3],
    ),
  );

  lines.push("");
  lines.push(t("solver.clipboardIons"));
  const ionRows = SUMMARY_COLUMN_ORDER.map(({ element }) => [
    formatClipboardIonLabel(element),
    formatNumber(Number(ionValues[element]), NUTRIENT_FORMATTER),
  ]);
  lines.push(...buildAlignedRows(null, ionRows, [1]));
  return lines.join("\n");
}
