import assert from "node:assert/strict";
import test from "node:test";

import { createLatestRequestGate } from "../../frontend/request_gate.js";

test("only the latest asynchronous request remains current", () => {
  const gate = createLatestRequestGate();
  const first = gate.reserve();
  const second = gate.reserve();
  assert.equal(gate.isCurrent(first), false);
  assert.equal(gate.isCurrent(second), true);
  gate.invalidate();
  assert.equal(gate.isCurrent(second), false);
});
