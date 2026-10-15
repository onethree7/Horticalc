import assert from "node:assert/strict";
import test from "node:test";

import { loadPreferences, persistPreferences, postJson } from "../../frontend/app/api.js";

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

test("preference writes reject failures and keep later writes queued", async () => {
  const previousFetch = globalThis.fetch;
  const requests = [];
  let rejectFirst;
  globalThis.fetch = async (_url, options) => {
    if (!options) return { ok: true, json: async () => ({ theme: "soil" }) };
    requests.push(JSON.parse(options.body));
    if (requests.length === 1) {
      await new Promise((resolve) => { rejectFirst = resolve; });
      return { ok: false, status: 500, json: async () => ({ detail: "disk unavailable" }) };
    }
    return { ok: true, json: async () => ({ theme: "soil", ...JSON.parse(options.body) }) };
  };
  try {
    assert.deepEqual(await loadPreferences(), { theme: "soil" });
    const failed = persistPreferences({ solver_history_limit: 0 });
    const rejected = assert.rejects(failed, /disk unavailable/);
    const recovered = persistPreferences({ locale: "de" });
    await Promise.resolve();
    assert.deepEqual(requests, [{ solver_history_limit: 0 }]);
    rejectFirst();
    await rejected;
    assert.deepEqual(await recovered, { theme: "soil", locale: "de" });
    assert.deepEqual(requests, [{ solver_history_limit: 0 }, { locale: "de" }]);
  } finally {
    globalThis.fetch = previousFetch;
  }
});
