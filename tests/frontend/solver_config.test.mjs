import assert from "node:assert/strict";
import test from "node:test";

import {
  applySolverConfig,
  buildSolverConfigPayload,
  normalizeSolverConfigDefinitions,
  sanitizeSolverConfig,
} from "../../frontend/app/solver_config.js";
import { buildSolvePayload, formatClipboardIonLabel } from "../../frontend/app/solver_payload.js";

const fallback = [
  { key: "solver_model", type: "string", defaultValue: "mass_nnls", choices: ["mass_nnls", "hierarchical", "legacy"] },
  { key: "irls_max_outer_iter", type: "integer", defaultValue: 4, minimum: 1, maximum: 12 },
  { key: "scale_eps_mg_per_l", type: "number", defaultValue: 1, exclusiveMinimum: 0 },
];

test("solver configuration retains schema bounds and normalizes input", () => {
  const definitions = normalizeSolverConfigDefinitions(
    [{ key: "irls_max_outer_iter", type: "integer", default: 4, minimum: 1, maximum: 12 }],
    fallback,
    () => true,
  );
  const controls = {
    solver_model: { value: "legacy" },
    irls_max_outer_iter: { value: "99" },
    scale_eps_mg_per_l: { value: "0" },
  };
  applySolverConfig(definitions, controls, {});
  controls.irls_max_outer_iter.value = "99";
  controls.scale_eps_mg_per_l.value = "0";
  controls.solver_model.value = "mass_nnls";
  assert.deepEqual(buildSolverConfigPayload(definitions, controls), {
    solver_model: "mass_nnls",
    irls_max_outer_iter: 12,
    scale_eps_mg_per_l: 1,
  });
  assert.deepEqual(sanitizeSolverConfig({ irls_max_outer_iter: 2, removed: true }, definitions), {
    irls_max_outer_iter: 2,
  });
});

test("solver payload formatting removes zero entries without changing public keys", () => {
  assert.equal(formatClipboardIonLabel("N_total"), "N");
  assert.deepEqual(buildSolvePayload({
    liters: 10,
    targetValues: { K: 100, Ca: 0 },
    waterMgPerL: { Ca: 20 },
    osmosisPercent: 25,
    allowedFertilizers: ["A"],
    fixedGrams: { A: 0, B: 2 },
    ureaAsNh4: false,
    solverConfig: {
      solver_model: "hierarchical",
      target_priorities: { N_total: { under: 1, over: 1 }, Cu: { under: 4, over: 4 } },
    },
  }), {
    liters: 10,
    targets: { K: 100 },
    water_profile: { mg_per_l: { Ca: 20 }, osmosis_percent: 25 },
    fertilizers_allowed: ["A"],
    fixed_grams: { B: 2 },
    urea_as_nh4: false,
    solver_config: {
      solver_model: "hierarchical",
      target_priorities: { N_total: { under: 1, over: 1 }, Cu: { under: 4, over: 4 } },
    },
  });
});
