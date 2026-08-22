import assert from "node:assert/strict";
import test from "node:test";

import {
  compactSolverHistoryPreview,
  formatSolverHistorySummary,
} from "../../frontend/app/history.js";
import { buildSolverPrintableText } from "../../frontend/app/solver_printable.js";
import { createUnitService } from "../../frontend/app/units.js";

const t = (key, params = {}) => `${key}${params.unit ? ` (${params.unit})` : ""}`;

test("solver history summaries follow current volume units and retain compact NPK targets", () => {
  const units = createUnitService();
  const entry = {
    created_at: "invalid",
    liters: 10,
    targets_mg_per_l: { N_total: 100, P: 20, K: 150 },
  };

  assert.equal(
    formatSolverHistorySummary(entry, { locale: "en", units }),
    "– · 10 L · N100/P20/K150",
  );
  units.setVolumeUnit("us_gallon");
  assert.match(formatSolverHistorySummary(entry, { locale: "en", units }), /2\.6417 US gal/);
});

test("printable solver history uses stored fertilizer kinds and canonical calculation data", () => {
  const units = createUnitService();
  const result = {
    solver_model: "mass_nnls",
    fertilizers: [
      { name: "Solid", grams: 10 },
      { name: "Liquid", grams: 20 },
    ],
    targets_mg_per_l: { N_total: 100 },
    achieved_elements_mg_per_l: { N_total: 99 },
    errors_mg_per_l: { N_total: -1 },
  };
  const calculation = {
    npk_metrics: { npk_all_pct: "1-2-3" },
    ec: { ec_mS_per_cm: { "25.0": 1.2, "18.0": 1.1 } },
    elements_mg_per_l: { N_total: 99, K: 150 },
  };

  const text = buildSolverPrintableText({
    result,
    calculation,
    liters: 10,
    osmosisPercent: 25,
    fertilizerKinds: { Solid: "solid", Liquid: "liquid" },
    t,
    units,
  });

  assert.match(text, /Solid\s+10\s+g/);
  assert.match(text, /Liquid\s+20\s+mL/);
  assert.match(text, /1-2-3/);
  assert.match(text, /1\.200/);
  assert.match(text, /N\s+100\s+99\s+-1/);
});

test("solver history hover preview is a bounded excerpt with a dialog hint", () => {
  const text = Array.from({ length: 24 }, (_, index) => `line ${index + 1}`).join("\n");
  const preview = compactSolverHistoryPreview(text, "Click for the complete output", 5);

  assert.equal(
    preview,
    "line 1\nline 2\nline 3\nline 4\nline 5\n\n… Click for the complete output",
  );
  assert.equal(compactSolverHistoryPreview("line 1\nline 2", "More", 5), "line 1\nline 2");
});
