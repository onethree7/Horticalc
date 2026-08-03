import assert from "node:assert/strict";
import test from "node:test";

import {
  applyScaledValues,
  roundScaleFactor,
  scaleAmountsByVolume,
  scaledValues,
} from "../../frontend/app/scaling.js";

test("scaling rounds the factor and values once", () => {
  const rows = [{ base: 1.111 }, { base: 2 }];
  const factor = applyScaledValues(
    rows,
    1.049,
    ({ base }) => base,
    (row, value) => { row.value = value; },
  );
  assert.equal(factor, 1.05);
  assert.deepEqual(rows.map(({ value }) => value), [1.167, 2.1]);
  assert.equal(roundScaleFactor(1.049), 1.05);
  assert.deepEqual(scaledValues(rows, -2, ({ base }) => base).values, [0, 0]);
});

test("fixed Solver amounts scale proportionally with batch volume", () => {
  assert.deepEqual(scaleAmountsByVolume({ Fetrilon: 2, PeKacid: 6 }, 10, 20), {
    Fetrilon: 4,
    PeKacid: 12,
  });
});
