import assert from "node:assert/strict";
import test from "node:test";

import { storageGet, storageSet } from "../../frontend/app/storage.js";

test("storage helpers round-trip JSON and contain storage failures", () => {
  const values = new Map();
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
  assert.equal(storageSet("prefs", { theme: "soil" }, storage), true);
  assert.deepEqual(storageGet("prefs", {}, storage), { theme: "soil" });
  assert.equal(storageGet("missing", "fallback", storage), "fallback");

  const broken = { getItem: () => { throw new Error("denied"); }, setItem: () => { throw new Error("denied"); } };
  assert.equal(storageSet("prefs", {}, broken), false);
  assert.equal(storageGet("prefs", "fallback", broken), "fallback");
});
