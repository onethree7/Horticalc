import { qs, qsa } from "./dom.js";
import { formatNumber, parseDecimalInput } from "./formatting.js";
import { createLatestRequestGate } from "../request_gate.js";

const instructionKeys = ["stock.prepare", "stock.store", "stock.dilute", "stock.smallBatch"];
const readingSources = [
  { name: "Science in Hydroponics", url: "https://scienceinhydroponics.com/2017/09/five-things-you-should-know-when-mixing-your-own-hydroponic-liquid-nutrients.html" },
  { name: "Frontiers in Agronomy", url: "https://www.frontiersin.org/journals/agronomy/articles/10.3389/fagro.2026.1823187/full" },
];
const numberFormatter = new Intl.NumberFormat("en-US", { maximumSignificantDigits: 6, useGrouping: false });

function defaultStockSettings() {
  return { schema_version: 2, tanks: { A: { liters: 1, factor: 100 }, B: { liters: 1, factor: 100 } }, assignments: {}, material_fingerprints: {} };
}

function findingText(finding, t) {
  const message = finding.code === "pair_risk"
    ? finding.risks.map((risk) => t(`stock.risk.${risk}`)).join(" ") : t(`stock.finding.${finding.code}`);
  return [finding.tank, finding.materials.join(", "), message].filter(Boolean).join(" · ");
}

function stockAmount(item, amount, units) {
  const formatted = units.formatDoseDisplay(amount, item.name);
  const value = amount > 0 && Number(formatted) === 0
    ? (amount / units.displayDoseToCanonical(1, item.name)).toExponential(4) : formatted;
  return `${value} ${units.doseUnitDefinition(item.name).symbol}`;
}

function stockVolumeValue(liters, units) {
  if (liters === null) return "";
  const value = liters / units.getVolumeUnitDefinition().liters_per_unit;
  const formatted = units.formatVolumeValue(value);
  return Number(formatted) === 0 && value !== 0 ? value.toExponential(4) : formatted;
}

function volume(liters, units) {
  return `${stockVolumeValue(liters, units)} ${units.getVolumeUnitDefinition().symbol}`;
}

function batchDose(plan, t) {
  return plan.tanks.map((tank) => `${Number(tank.dose_ml.toPrecision(6))} mL ${tank.id}`).join(" + ") || t("stock.separate");
}

export function buildStockPrintableText(plan, t, units) {
  if (!plan?.exportable) return "";
  const lines = [t("stock.title"), t("stock.context", { volume: volume(plan.liters, units) }), ""];
  const water = plan.settings.source_water;
  const analysis = Object.entries(water.mg_per_l).filter(([, amount]) => amount > 0)
    .map(([ion, amount]) => `${ion} ${formatNumber(amount, numberFormatter)} ${ion === "KH" ? "°dKH" : "mg/L"}`).join(", ");
  lines.push(`${t("stock.batchWater")}: ${analysis || t("stock.ro")}`);
  lines.push(`${t("water.osmosisPercent")}: ${formatNumber(water.osmosis_percent, numberFormatter)}`);
  lines.push(t("stock.waterAssumption"));
  lines.push("");
  for (const tank of plan.tanks) {
    lines.push(t("stock.tankTitle", { tank: tank.id, volume: volume(tank.liters, units), factor: tank.factor }));
    tank.ingredients.forEach((item) => lines.push(`${item.name}: ${stockAmount(item, item.stock_amount, units)}`));
    lines.push(t("stock.dose", { dose: Number(tank.dose_ml_per_l.toPrecision(6)) }), t("stock.capacity", { volume: volume(tank.capacity_liters, units) }), "");
  }
  lines.push(t("stock.batchDose", { dose: batchDose(plan, t), volume: volume(plan.liters, units) }));
  plan.ingredients.filter((item) => item.assignment === "separate").forEach((item) => {
    lines.push(`${t("stock.separate")}: ${item.name} — ${stockAmount(item, item.recipe_amount, units)}`);
  });
  lines.push("", ...instructionKeys.map((key) => t(key)), t("stock.guidance"));
  if (plan.findings.length) lines.push("", t("stock.checks"), ...plan.findings.map((item) => `${t(`stock.${item.severity}`)}: ${findingText(item, t)}`));
  lines.push("", t("stock.reading"), ...readingSources.map(({ name, url }) => `${name}: ${url}`));
  return lines.join("\n");
}

function textElement(tag, text, className = "") {
  const element = document.createElement(tag);
  element.textContent = text;
  element.className = className;
  return element;
}

export function createStocksController({ api, i18n, units, notifications, getRecipe, getWater, onDisplayResult, onSettingsChange, onClose }) {
  const t = (key, params) => i18n.t(key, params);
  const requests = createLatestRequestGate();
  const panel = qs("#stockSolutionPanel");
  const calculatorMode = qs("#calculatorMode");
  const status = qs("#stockStatus");
  const volumeInput = qs("#stockVolume");
  const factorInput = qs("#stockFactor");
  const independentInput = qs("#stockIndependent");
  const copyButton = qs("#copyStocks");
  const printButton = qs("#printStocks");
  const updateButton = qs("#updateStocks");
  const suggestButton = qs("#suggestStocks");
  const addCButton = qs("#addStockC");
  let settings = defaultStockSettings();
  let plan = null;
  let current = false;
  let hasSettings = false;
  let opened = false;
  let active = false;
  let batchRefreshPending = false;

  function displayResult() {
    onDisplayResult(opened && active && current && plan?.complete ? plan.final_solution : null);
  }

  function invalidate() {
    requests.invalidate();
    current = false;
    copyButton.disabled = true;
    printButton.disabled = true;
    qs("#stockOutput").hidden = true;
    qsa("#stockIngredients tbody tr td:last-child").forEach((cell) => { cell.textContent = "—"; });
    if (opened) status.textContent = t("stock.stale");
    displayResult();
  }

  function changed() {
    hasSettings = true;
    invalidate();
    onSettingsChange();
  }

  function renderSettings() {
    const first = Object.values(settings.tanks)[0];
    volumeInput.value = stockVolumeValue(first.liters, units);
    factorInput.value = first.factor;
    volumeInput.disabled = independentInput.checked;
    factorInput.disabled = independentInput.checked;
    qsa(".stock-volume-unit").forEach((element) => { element.textContent = units.getVolumeUnitDefinition().symbol; });
    addCButton.textContent = t(settings.tanks.C ? "stock.removeC" : "stock.addC");
    addCButton.disabled = Boolean(settings.tanks.C) && Object.keys(settings.tanks).length === 1;
    const tankControls = qs("#stockTankSettings");
    tankControls.replaceChildren();
    tankControls.hidden = !independentInput.checked;
    for (const [id, tank] of Object.entries(settings.tanks)) {
      for (const key of ["liters", "factor"]) {
        const label = textElement("label", `${id} · ${t(key === "liters" ? "stock.volume" : "stock.factor")}${key === "liters" ? ` (${units.getVolumeUnitDefinition().symbol})` : ""}`);
        const input = document.createElement("input");
        input.type = "text";
        input.className = "input-field";
        input.inputMode = "decimal";
        input.dataset.tank = id;
        input.dataset.field = key;
        input.value = key === "liters" ? stockVolumeValue(tank[key], units) : tank[key] ?? "";
        input.addEventListener("input", () => {
          const value = parseDecimalInput(input.value);
          tank[key] = value === null ? null : key === "liters" ? value * units.getVolumeUnitDefinition().liters_per_unit : value;
          changed();
        });
        label.append(input);
        tankControls.append(label);
      }
    }
  }

  function renderIngredients() {
    const body = qs("#stockIngredients tbody");
    body.replaceChildren();
    for (const item of plan?.ingredients || []) {
      const row = document.createElement("tr");
      const choice = document.createElement("select");
      choice.setAttribute("aria-label", `${t("stock.assignment")}: ${item.name}`);
      choice.dataset.material = item.name;
      for (const [value, label] of [["", t("stock.choose")], ...Object.keys(settings.tanks).map((id) => [id, id]), ["separate", t("stock.separate")]]) {
        const option = textElement("option", label);
        option.value = value;
        choice.append(option);
      }
      choice.value = settings.assignments[item.name] || "";
      choice.addEventListener("change", () => {
        settings.assignments[item.name] = choice.value || null;
        changed();
      });
      const cell = document.createElement("td");
      cell.append(choice);
      row.append(textElement("td", item.name), cell, textElement("td", !current || item.stock_amount === null ? "—" : stockAmount(item, item.stock_amount, units)));
      body.append(row);
    }
  }

  function renderPlan() {
    if (!plan) return;
    qs("#stockContext").textContent = t("stock.context", { volume: volume(plan.liters, units) });
    renderIngredients();
    const cards = qs("#stockTankCards");
    cards.replaceChildren();
    for (const tank of plan.tanks) {
      const card = textElement("section", "", "table-card stock-tank");
      card.append(textElement("h3", t("stock.tankTitle", { tank: tank.id, volume: volume(tank.liters, units), factor: tank.factor })));
      const list = document.createElement("ul");
      tank.ingredients.forEach((item) => list.append(textElement("li", `${item.name}: ${stockAmount(item, item.stock_amount, units)}`)));
      card.append(list, textElement("p", t("stock.dose", { dose: Number(tank.dose_ml_per_l.toPrecision(6)) })), textElement("p", t("stock.capacity", { volume: volume(tank.capacity_liters, units) }), "hint"));
      cards.append(card);
    }
    qs("#stockBatchDose").textContent = plan.complete ? t("stock.batchDose", { dose: batchDose(plan, t), volume: volume(plan.liters, units) }) : t("stock.incomplete");
    qs("#stockSeparate").replaceChildren(...plan.ingredients.filter((item) => item.assignment === "separate").map((item) =>
      textElement("li", `${t("stock.separate")}: ${item.name} — ${stockAmount(item, item.recipe_amount, units)}`)
    ));
    qs("#stockInstructions").replaceChildren(...instructionKeys.map((key) => textElement("li", t(key))));
    qs("#stockFindings").replaceChildren(...plan.findings.map((item) => {
      const element = textElement("li", `${t(`stock.${item.severity}`)}: ${findingText(item, t)}`);
      element.dataset.severity = item.severity;
      if (item.code === "material_changed") {
        const reassess = textElement("button", t("stock.reassessed"), "btn btn--outline");
        reassess.type = "button";
        reassess.addEventListener("click", () => {
          settings.material_fingerprints[item.materials[0]] = item.fingerprint;
          changed();
          update();
        });
        element.append(" ", reassess);
      }
      return element;
    }));
    qs("#stockFindings").hidden = !plan.findings.length;
    qs("#stockChecksTitle").hidden = !plan.findings.length;
    qs("#stockOutput").hidden = !current;
    copyButton.disabled = !current || !plan.exportable;
    printButton.disabled = copyButton.disabled;
    status.textContent = t(!current ? "stock.stale" : !plan.complete ? "stock.incomplete" : !plan.exportable ? "stock.exportBlocked" : plan.findings.length ? "stock.review" : "stock.calculated");
    displayResult();
  }

  async function update(suggestAssignments = false) {
    if (updateButton.disabled) return;
    const recipe = getRecipe();
    if (!recipe?.fertilizers.some((item) => item.grams > 0)) {
      status.textContent = t("stock.recalculate");
      return;
    }
    if (Object.values(settings.tanks).some((tank) => !Number.isFinite(tank.liters) || tank.liters <= 0 || !Number.isFinite(tank.factor) || tank.factor <= 1)) {
      status.textContent = t("stock.invalidSettings");
      return;
    }
    invalidate();
    const version = requests.reserve();
    status.textContent = t("status.loadingData");
    try {
      const result = await api.planStocks({ recipe, settings, suggest_assignments: suggestAssignments }, t("stock.failed"));
      if (!requests.isCurrent(version)) return;
      plan = result;
      settings = result.settings;
      hasSettings = true;
      current = true;
      renderSettings();
      renderPlan();
      onSettingsChange();
    } catch (error) {
      if (requests.isCurrent(version)) status.textContent = error.message;
    }
  }

  function close() {
    opened = false;
    batchRefreshPending = false;
    panel.classList.add("is-hidden");
    calculatorMode.classList.remove("is-stock-view");
    displayResult();
  }

  function refreshBatch() {
    const recipe = getRecipe();
    if (opened && active && recipe && batchRefreshPending) {
      batchRefreshPending = false;
      update();
    }
  }

  function mount() {
    qs("#closeStocks").addEventListener("click", onClose);
    updateButton.addEventListener("click", () => update());
    suggestButton.addEventListener("click", () => update(true));
    const readingLink = qs("#stockReading");
    readingLink.href = readingSources[0].url;
    readingLink.addEventListener("click", (event) => {
      event.preventDefault();
      readingSources.forEach(({ url }) => window.open(url, "_blank", "noopener,noreferrer"));
    });
    document.addEventListener("copy", (event) => {
      const selection = window.getSelection();
      if (!opened || !active || !event.clipboardData || !selection?.rangeCount
        || document.activeElement?.matches("input, textarea") || !selection.getRangeAt(0).intersectsNode(panel)) return;
      const text = selection.toString();
      if (!text) return;
      event.clipboardData.setData("text/plain", text);
      event.preventDefault();
    });
    for (const [input, key] of [[volumeInput, "liters"], [factorInput, "factor"]]) {
      input.addEventListener("input", () => {
        const value = parseDecimalInput(input.value);
        Object.values(settings.tanks).forEach((tank) => { tank[key] = value === null ? null : key === "liters" ? value * units.getVolumeUnitDefinition().liters_per_unit : value; });
        changed();
      });
    }
    independentInput.addEventListener("change", () => {
      if (!independentInput.checked) {
        const first = Object.values(settings.tanks)[0];
        Object.keys(settings.tanks).forEach((id) => { settings.tanks[id] = { ...first }; });
        changed();
      }
      renderSettings();
    });
    addCButton.addEventListener("click", () => {
      if (addCButton.disabled) return;
      if (settings.tanks.C) {
        delete settings.tanks.C;
        Object.keys(settings.assignments).forEach((name) => { if (settings.assignments[name] === "C") settings.assignments[name] = null; });
      } else {
        settings.tanks.C = { ...Object.values(settings.tanks)[0] };
      }
      changed();
      renderSettings();
      renderIngredients();
    });
    copyButton.addEventListener("click", async () => {
      if (!current || !plan?.exportable) return;
      try {
        await notifications.copyText(buildStockPrintableText(plan, t, units));
        status.textContent = t("status.copied");
      } catch (error) { notifications.reportError(error, t("errors.copyFailed")); }
    });
    printButton.addEventListener("click", () => {
      if (!current || !plan?.exportable) return;
      qs("#stockPrintSheet").textContent = buildStockPrintableText(plan, t, units);
      document.body.classList.add("printing-stocks");
      document.documentElement.classList.add("printing-stocks");
      try { window.print(); } finally {
        document.body.classList.remove("printing-stocks");
        document.documentElement.classList.remove("printing-stocks");
      }
    });
    renderSettings();
  }

  return {
    mount,
    close,
    invalidate,
    refreshBatch,
    onBatchVolumeChange() { batchRefreshPending = opened; },
    setActive(value) { active = value; refreshBatch(); displayResult(); },
    refreshLocalized() { renderSettings(); renderPlan(); },
    async open() {
      opened = true;
      panel.classList.remove("is-hidden");
      calculatorMode.classList.add("is-stock-view");
      if (!current) await update();
      else renderPlan();
    },
    load(value) {
      close();
      invalidate();
      settings = value ? JSON.parse(JSON.stringify(value)) : defaultStockSettings();
      hasSettings = Boolean(value);
      plan = null;
      independentInput.checked = new Set(Object.values(settings.tanks).map((tank) => JSON.stringify(tank))).size > 1;
      renderSettings();
      qs("#stockIngredients tbody").replaceChildren();
    },
    get attachment() {
      return hasSettings ? JSON.parse(JSON.stringify({ ...settings, source_water: getWater() })) : null;
    },
  };
}
