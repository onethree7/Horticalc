import assert from "node:assert/strict";
import test from "node:test";

import { syncSelectedOptionTitle } from "../../frontend/app/dom.js";

test("selected option titles expose the complete active label", () => {
  const select = {
    value: "long-profile.yml",
    selectedOptions: [{ textContent: "  A deliberately long profile name  " }],
    title: "",
  };

  syncSelectedOptionTitle(select);

  assert.equal(select.title, "A deliberately long profile name");
});

test("empty profile selections do not expose a tooltip", () => {
  const select = {
    value: "",
    selectedOptions: [{ textContent: "Select profile" }],
    title: "stale title",
  };

  syncSelectedOptionTitle(select);

  assert.equal(select.title, "");
});
