import assert from "node:assert/strict";
import test from "node:test";

import {
  activeFixedAmountCount,
  buildNutrientSolutionPayload,
  nutrientSolutionHasSetup,
} from "../../frontend/app/solver_payload.js";

test("target-only profiles omit every Solver setup field", () => {
  assert.deepEqual(buildNutrientSolutionPayload({
    name: "Leaf target",
    targets: { N_total: 120, K: 180 },
    includeSetup: false,
    liters: 10,
    waterProfile: "tap.yml",
    osmosisPercent: 25,
    allowedFertilizers: ["A"],
    fixedGrams: { A: 2 },
    ureaAsNh4: true,
    solverConfig: { solver_model: "mass_nnls" },
  }), {
    name: "Leaf target",
    source: "Horticalc UI",
    targets_mg_per_l: { N_total: 120, K: 180 },
  });
});

test("Solver setup profiles preserve inputs and only positive fixed amounts", () => {
  const payload = buildNutrientSolutionPayload({
    name: "Fixed micronutrients",
    targets: { N_total: 100 },
    includeSetup: true,
    liters: 10,
    waterProfile: "tap.yml",
    osmosisPercent: 15,
    allowedFertilizers: ["Compo Fetrilon Combi 1", "ICL Nova PeKacid 0-60-20"],
    fixedGrams: {
      "Compo Fetrilon Combi 1": 2,
      "ICL Nova PeKacid 0-60-20": 6,
      Unused: 0,
    },
    ureaAsNh4: false,
    solverConfig: { solver_model: "hierarchical" },
  });

  assert.deepEqual(payload, {
    name: "Fixed micronutrients",
    source: "Horticalc UI",
    targets_mg_per_l: { N_total: 100 },
    liters: 10,
    water_profile: "tap",
    osmosis_percent: 15,
    fertilizers_allowed: ["Compo Fetrilon Combi 1", "ICL Nova PeKacid 0-60-20"],
    fixed_grams: {
      "Compo Fetrilon Combi 1": 2,
      "ICL Nova PeKacid 0-60-20": 6,
    },
    urea_as_nh4: false,
    solver_config: { solver_model: "hierarchical" },
  });
  assert.equal(nutrientSolutionHasSetup(payload), true);
  assert.equal(activeFixedAmountCount(payload.fixed_grams), 2);
});

test("legacy profiles containing only solver_config still report saved setup", () => {
  assert.equal(nutrientSolutionHasSetup({
    name: "Legacy",
    targets_mg_per_l: { K: 100 },
    solver_config: { solver_model: "mass_nnls" },
  }), true);
  assert.equal(nutrientSolutionHasSetup({ targets_mg_per_l: { K: 100 } }), false);
});
