import assert from "node:assert/strict";
import test from "node:test";

import {
  applyScaledValues,
  roundScaleFactor,
  scaleAmountsByVolume,
  scaledValues,
} from "../../frontend/app/scaling.js";

test("scaling rounds the factor while preserving quantity precision", () => {
  const rows = [{ base: 1.111 }, { base: 2 }];
  const factor = applyScaledValues(
    rows,
    1.049,
    ({ base }) => base,
    (row, value) => { row.value = value; },
  );
  assert.equal(factor, 1.05);
  assert.deepEqual(rows.map(({ value }) => value), [1.16655, 2.1]);
  assert.equal(roundScaleFactor(1.049), 1.05);
  assert.deepEqual(scaledValues(rows, -2, ({ base }) => base).values, [0, 0]);
});

test("trace doses survive factor and batch scaling", () => {
  const scaled = scaledValues([{ dose: 0.0002 }], 1.05, ({ dose }) => dose);
  assert.ok(Math.abs(scaled.values[0] / 0.00021 - 1) < 1e-14);
  const doubled = scaleAmountsByVolume({ trace: 0.0002 }, 1, 2);
  assert.equal(doubled.trace, 0.0004);
  const restored = scaleAmountsByVolume(doubled, 2, 1);
  // Allow floating-point error, well below any displayed dose precision.
  assert.ok(Math.abs(restored.trace / 0.0002 - 1) < 1e-14);
});

test("fixed Solver amounts scale proportionally with batch volume", () => {
  assert.deepEqual(scaleAmountsByVolume({ Fetrilon: 2, PeKacid: 6 }, 10, 20), {
    Fetrilon: 4,
    PeKacid: 12,
  });
});
