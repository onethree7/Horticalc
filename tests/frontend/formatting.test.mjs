import assert from "node:assert/strict";
import test from "node:test";

import {
  buildAlignedRows,
  formatNumber,
  parseDecimalInput,
  roundScaledValue,
} from "../../frontend/app/formatting.js";

test("decimal parsing accepts both supported separators and rejects invalid values", () => {
  assert.equal(parseDecimalInput(" 12,5 "), 12.5);
  assert.equal(parseDecimalInput("12.5"), 12.5);
  assert.equal(parseDecimalInput(""), null);
  assert.equal(parseDecimalInput("Infinity"), null);
});

test("number and clipboard formatting are deterministic", () => {
  assert.equal(roundScaledValue(1.23456), 1.235);
  assert.equal(formatNumber(Number.NaN), "-");
  assert.deepEqual(
    buildAlignedRows(["name", "g"], [["A", "2"], ["long", "10"]], [1]),
    ["name   g", "A      2", "long  10"],
  );
});
