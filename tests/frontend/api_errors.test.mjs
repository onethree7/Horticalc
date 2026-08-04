import assert from "node:assert/strict";
import test from "node:test";

import { postJson } from "../../frontend/app/api.js";

test("API errors retain structured conflict metadata", async () => {
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 409,
    async json() {
      return {
        detail: {
          code: "nutrient_solution_exists",
          name: "Existing",
          filename: "Existing.yml",
          has_solver_setup: true,
        },
      };
    },
  });

  try {
    await assert.rejects(
      postJson("/nutrient-solutions", {}, "Unable to save"),
      (error) => {
        assert.equal(error.message, "Unable to save");
        assert.equal(error.status, 409);
        assert.equal(error.detail.code, "nutrient_solution_exists");
        assert.equal(error.detail.has_solver_setup, true);
        return true;
      },
    );
  } finally {
    globalThis.fetch = previousFetch;
  }
});
