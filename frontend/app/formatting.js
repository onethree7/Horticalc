export function parseDecimalInput(raw) {
  const text = String(raw ?? "").trim();
  if (!text) {
    return null;
  }
  const value = Number(text.replaceAll(",", "."));
  return Number.isFinite(value) ? value : null;
}

export function decimalInputValue(raw, fallback = 0) {
  const parsed = parseDecimalInput(raw);
  return parsed === null ? fallback : parsed;
}

export function normalizeDecimalInputElement(input, value, fallback = "0") {
  input.value = Number.isFinite(value) ? String(value) : fallback;
}

const defaultNumberFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
  useGrouping: false,
});

export function formatNumber(value, formatter = defaultNumberFormatter) {
  return Number.isFinite(value) ? formatter.format(value) : "-";
}

export function roundScaledValue(value) {
  return Math.round(value * 1000) / 1000;
}

export function buildAlignedRows(headers, rows, numericColumns = []) {
  const allRows = headers ? [headers, ...rows] : rows;
  const widths = allRows.reduce((current, row) => {
    row.forEach((cell, index) => {
      current[index] = Math.max(current[index] || 0, String(cell).length);
    });
    return current;
  }, []);
  const numeric = new Set(numericColumns);
  return allRows.map((row) => row.map((cell, index) => {
    const value = String(cell);
    return numeric.has(index) ? value.padStart(widths[index]) : value.padEnd(widths[index]);
  }).join("  ").trimEnd());
}
