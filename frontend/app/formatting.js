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

export function buildDoseTable(fertilizers, { t, units, fertilizerKinds = {} }) {
  return buildAlignedRows(
    [t("common.fertilizer"), t("common.amount"), t("common.unit")],
    fertilizers.map(({ name, grams }) => {
      const kind = fertilizerKinds[name];
      const definition = kind ? { name, liquid: kind === "liquid" } : name;
      return [name, units.formatDoseDisplay(Number(grams), definition), units.doseUnitDefinition(definition).symbol];
    }),
    [1],
  );
}

function ratioValueText(value) {
  const text = String(value || "").trim();
  if (!text) return "-";
  const markerIndex = text.indexOf("=");
  return markerIndex >= 0 ? text.slice(markerIndex + 1) : text;
}

function formatRatioNumber(value) {
  if (!Number.isFinite(value)) return "-";
  return (Math.round(value * 10) / 10).toFixed(1).replace(/\.0$/, "");
}

function calciumMagnesiumRatio(value) {
  const parts = ratioValueText(value).split(":").map(Number);
  if (parts.length !== 2 || !parts.every(Number.isFinite)) return "-";
  const [left, right] = parts;
  if (left <= 0 && right <= 0) return "0 Ca : 0 Mg";
  if (right <= 0) return `${formatRatioNumber(left)} Ca : 0 Mg`;
  return `${formatRatioNumber(left / right)} Ca : 1 Mg`;
}

export function sidebarRatioRows(metrics = {}) {
  const ratios = metrics.npk_ratios_ion || {};
  const nitrogen = metrics.n_form_pct;
  return [
    ["Ca:Mg", calciumMagnesiumRatio(ratios["Ca:Mg"])],
    ["N:K", ratioValueText(ratios["N:K"])],
    ["Ca:K", ratioValueText(ratios["Ca:K"])],
    ["NO3:NH4:UR (%)", nitrogen ? `${nitrogen.no3}:${nitrogen.nh4}:${nitrogen.urea}` : "-", "live.nitrogenFormsHint"],
    ["SO4:P", ratioValueText(ratios["SO4:P"])],
    ["P:K", ratioValueText(ratios["P:K"])],
    ["Fe:Mg", ratioValueText(ratios["Fe:Mg"])],
  ];
}
