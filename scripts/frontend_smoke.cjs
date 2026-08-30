const { chromium } = require("playwright");
const fs = require("node:fs");
const { URL } = require("node:url");

const baseUrl = process.env.HORTICALC_TEST_URL || "http://127.0.0.1:8765";
const browserCandidates = process.platform === "win32"
  ? [
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    ]
  : ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"];
const executablePath = process.env.HORTICALC_BROWSER_PATH
  || browserCandidates.find((candidate) => fs.existsSync(candidate));

async function assertNoPageOverflow(page, label) {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  if (dimensions.scrollWidth > dimensions.clientWidth + 1) {
    throw new Error(`${label} has horizontal page overflow: ${JSON.stringify(dimensions)}`);
  }
}

async function assertFlexibleDesktopFrame(page) {
  await page.setViewportSize({ width: 1920, height: 1080 });
  const layout = await page.locator(".app-shell").evaluate((frame) => ({
    frameWidth: frame.getBoundingClientRect().width,
    viewportWidth: document.documentElement.clientWidth,
  }));
  const expectedWidth = layout.viewportWidth - 16;
  if (layout.frameWidth <= 1480 || Math.abs(layout.frameWidth - expectedWidth) > 1) {
    throw new Error(`Desktop app frame did not use the available width: ${JSON.stringify({
      ...layout,
      expectedWidth,
    })}`);
  }
  await assertNoPageOverflow(page, "1920px desktop layout");
  await page.setViewportSize({ width: 1280, height: 900 });
}

async function assertUiScaleControls(page) {
  const control = page.locator("#uiScaleSelect");
  if (await control.inputValue() !== "100") {
    throw new Error("UI scale did not start at 100%");
  }

  for (const scale of [75, 125, 150]) {
    await control.selectOption(String(scale), { force: true });
    await page.waitForFunction(
      (expected) => document.documentElement.style.getPropertyValue("--app-ui-scale") === expected,
      String(scale / 100),
    );
    const frame = await page.locator(".app-shell").evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return {
        left: rect.left,
        right: rect.right,
        viewportWidth: document.documentElement.clientWidth,
      };
    });
    const rightInset = frame.viewportWidth - frame.right;
    if (frame.left < -1 || rightInset < -1 || frame.left > 12 || rightInset > 12
        || Math.abs(frame.left - rightInset) > 1) {
      throw new Error(`${scale}% UI scale moved the app frame edge: ${JSON.stringify(frame)}`);
    }
    await assertNoPageOverflow(page, `${scale}% UI scale`);
  }

  await control.selectOption("125", { force: true });
  await page.waitForFunction(() => document.querySelector("#uiScaleSelect")?.value === "125");

  await page.keyboard.press("Control+-");
  await page.waitForFunction(() => document.querySelector("#uiScaleSelect")?.value === "110");
  await page.keyboard.press("Control+0");
  await page.waitForFunction(() => document.querySelector("#uiScaleSelect")?.value === "100");
  if (await page.evaluate(
    () => document.documentElement.style.getPropertyValue("--app-ui-scale"),
  ) !== "1") {
    throw new Error("Ctrl+0 did not restore the default UI scale");
  }

  await page.evaluate(() => {
    globalThis.dispatchEvent(new globalThis.WheelEvent(
      "wheel",
      { ctrlKey: true, deltaY: -100, cancelable: true },
    ));
  });
  await page.waitForFunction(() => document.querySelector("#uiScaleSelect")?.value === "110");
  await control.selectOption("100", { force: true });
}

async function readWorkspaceGeometry(page, selectors) {
  return page.evaluate((requestedSelectors) => {
    const workspace = document.querySelector(".workspace");
    const view = workspace.ownerDocument.defaultView;
    const workspaceStyle = view.getComputedStyle(workspace);
    const workspaceRect = workspace.getBoundingClientRect();
    const paddingLeft = Number.parseFloat(workspaceStyle.paddingLeft);
    const paddingRight = Number.parseFloat(workspaceStyle.paddingRight);
    const elements = Object.fromEntries(Object.entries(requestedSelectors).map(([name, selector]) => {
      const element = document.querySelector(selector);
      const rect = element.getBoundingClientRect();
      return [name, {
        left: rect.left,
        top: rect.top,
        bottom: rect.bottom,
        width: rect.width,
      }];
    }));
    return {
      availableLeft: workspaceRect.left + paddingLeft,
      availableWidth: workspace.clientWidth - paddingLeft - paddingRight,
      rootFontSize: Number.parseFloat(view.getComputedStyle(document.documentElement).fontSize),
      elements,
    };
  }, selectors);
}

function assertWorkspaceMeasure(layout, key, maxRem, label) {
  const box = layout.elements[key];
  const expectedWidth = Math.min(layout.availableWidth, maxRem * layout.rootFontSize);
  if (Math.abs(box.left - layout.availableLeft) > 1 || Math.abs(box.width - expectedWidth) > 2) {
    throw new Error(`${label} did not use its content measure: ${JSON.stringify({
      box,
      availableLeft: layout.availableLeft,
      availableWidth: layout.availableWidth,
      expectedWidth,
    })}`);
  }
}

function assertFullWorkspaceWidth(layout, key, label) {
  const box = layout.elements[key];
  if (Math.abs(box.left - layout.availableLeft) > 1
      || Math.abs(box.width - layout.availableWidth) > 2) {
    throw new Error(`${label} did not use the full workspace width: ${JSON.stringify({
      box,
      availableLeft: layout.availableLeft,
      availableWidth: layout.availableWidth,
    })}`);
  }
}

async function assertSolverFrameAlignment(page, label) {
  const layout = await readWorkspaceGeometry(page, {
    profile: "#profileSection",
    solver: "#solverMode:not(.is-hidden)",
  });
  assertWorkspaceMeasure(layout, "profile", 96, `${label} profile`);
  assertWorkspaceMeasure(layout, "solver", 96, `${label} solver`);
  if (Math.abs(layout.elements.profile.left - layout.elements.solver.left) > 1
      || Math.abs(layout.elements.profile.width - layout.elements.solver.width) > 1) {
    throw new Error(`${label} profile and solver frames were not aligned: ${JSON.stringify(layout)}`);
  }
}

async function assertAdvancedSolverLayout(page, expectedColumns, label) {
  const layout = await page.locator(".solver-advanced-config").evaluate((details) => {
    const view = details.ownerDocument.defaultView;
    const summary = details.querySelector("summary");
    const grid = details.querySelector(".rail-config-grid--advanced");
    const input = details.querySelector('input[inputmode="decimal"]');
    const reset = details.querySelector(".rail-config-reset");
    const detailsRect = details.getBoundingClientRect();
    const summaryRect = summary.getBoundingClientRect();
    const gridRect = grid.getBoundingClientRect();
    const inputRect = input.getBoundingClientRect();
    const resetRect = reset.getBoundingClientRect();
    return {
      columnCount: view.getComputedStyle(grid).gridTemplateColumns.split(" ").length,
      detailsClientWidth: details.clientWidth,
      detailsScrollWidth: details.scrollWidth,
      detailsWidth: detailsRect.width,
      gridWidth: gridRect.width,
      inputWidth: inputRect.width,
      resetWidth: resetRect.width,
      rootFontSize: Number.parseFloat(view.getComputedStyle(document.documentElement).fontSize),
      summaryWidth: summaryRect.width,
    };
  });
  const expectedGridWidth = Math.min(
    layout.detailsClientWidth,
    64 * layout.rootFontSize,
  );
  if (Math.abs(layout.summaryWidth - layout.detailsWidth) > 1
      || Math.abs(layout.gridWidth - expectedGridWidth) > 2
      || layout.columnCount !== expectedColumns
      || layout.detailsScrollWidth > layout.detailsClientWidth + 1) {
    throw new Error(`${label} advanced settings geometry was unexpected: ${JSON.stringify({
      ...layout,
      expectedColumns,
      expectedGridWidth,
    })}`);
  }
  if (expectedColumns === 2 && layout.inputWidth > (10 * layout.rootFontSize) + 1) {
    throw new Error(`${label} numeric solver input was too wide: ${JSON.stringify(layout)}`);
  }
  if (layout.resetWidth > (20 * layout.rootFontSize) + 1) {
    throw new Error(`${label} reset control was too wide: ${JSON.stringify(layout)}`);
  }
}

async function assertContentAwareWorkspaceBreakpoints(page) {
  await page.setViewportSize({ width: 2560, height: 1440 });

  const calculatorLayout = await readWorkspaceGeometry(page, {
    calculator: "#calculatorMode:not(.is-hidden)",
    profile: "#profileSection",
  });
  assertFullWorkspaceWidth(calculatorLayout, "calculator", "QHD calculator");
  assertFullWorkspaceWidth(calculatorLayout, "profile", "QHD calculator profile");
  const summaryLayout = await page.locator("#summaryScroll").evaluate((summary) => {
    const panel = summary.querySelector(".summary-panel:not([hidden])");
    const table = panel.querySelector(".nutrient-grid--summary");
    const panelStyle = summary.ownerDocument.defaultView.getComputedStyle(panel);
    const rowLabel = table.querySelector("tbody .row-label");
    const nutrientWidths = [...table.querySelectorAll("tbody td")]
      .map((cell) => cell.getBoundingClientRect().width)
      .filter((width) => width > 0);
    return {
      panelWidth: panel.getBoundingClientRect().width,
      panelContentWidth: panel.clientWidth
        - Number.parseFloat(panelStyle.paddingLeft)
        - Number.parseFloat(panelStyle.paddingRight),
      summaryClientWidth: summary.clientWidth,
      tableWidth: table.getBoundingClientRect().width,
      rowLabelWidth: rowLabel.getBoundingClientRect().width,
      nutrientWidths,
      rootFontSize: Number.parseFloat(
        summary.ownerDocument.defaultView.getComputedStyle(summary.ownerDocument.documentElement).fontSize,
      ),
    };
  });
  const nutrientWidthRange = Math.max(...summaryLayout.nutrientWidths)
    - Math.min(...summaryLayout.nutrientWidths);
  if (Math.abs(summaryLayout.panelWidth - summaryLayout.summaryClientWidth) > 2
      || Math.abs(summaryLayout.tableWidth - summaryLayout.panelContentWidth) > 2
      || Math.abs(summaryLayout.rowLabelWidth - (8 * summaryLayout.rootFontSize)) > 2
      || nutrientWidthRange > 2) {
    throw new Error(`QHD result bar did not distribute the summary across its available width: ${JSON.stringify({
      ...summaryLayout,
      nutrientWidthRange,
    })}`);
  }

  await page.locator("[data-shell-view='editor']").click();
  await page.locator("#fertilizerEditorMode:not(.is-hidden)").waitFor();
  const editorLayout = await readWorkspaceGeometry(page, {
    editor: "#fertilizerEditorMode:not(.is-hidden)",
  });
  assertFullWorkspaceWidth(editorLayout, "editor", "QHD fertilizer editor");

  await page.locator("[data-shell-view='water']").click();
  await page.locator("#waterSection:not(.is-hidden)").waitFor();
  const waterLayout = await readWorkspaceGeometry(page, { water: "#waterSection" });
  assertWorkspaceMeasure(waterLayout, "water", 72, "QHD water analysis");
  const wideWaterColumns = await page.locator("#waterValuesTable thead th").evaluateAll(
    (cells) => cells.map((cell) => cell.getBoundingClientRect().width),
  );
  const expectedWaterColumns = [18, 10].map((rem) => rem * waterLayout.rootFontSize);
  if (Math.abs(wideWaterColumns[1] - expectedWaterColumns[0]) > 2
      || Math.abs(wideWaterColumns[2] - expectedWaterColumns[1]) > 2) {
    throw new Error(`QHD water columns did not use their content widths: ${JSON.stringify({
      wideWaterColumns,
      expectedWaterColumns,
    })}`);
  }

  await page.locator("[data-shell-view='solver']").click();
  await page.locator("#solverMode:not(.is-hidden)").waitFor();
  await page.locator("#solverTargetsResultsEmpty:not(.is-hidden)").waitFor();
  await assertSolverFrameAlignment(page, "QHD empty solver");
  await page.locator("#solverOverrides > summary").click();
  await page.locator(".solver-advanced-config > summary").click();
  await assertAdvancedSolverLayout(page, 2, "QHD open");
  await assertNoPageOverflow(page, "QHD open solver details");
  await page.locator("#solverOverrides > summary").click();
  await page.locator(".solver-advanced-config > summary").click();

  for (const [width, expectedColumns, expectedStacked] of [
    [1280, 2, false],
    [981, 2, false],
    [960, 1, true],
    [640, 1, true],
  ]) {
    await page.setViewportSize({ width, height: 900 });
    await assertSolverFrameAlignment(page, `${width}px empty solver`);
    const comparison = await readWorkspaceGeometry(page, {
      targets: ".solver-panel--targets",
      results: ".solver-panel--target-results",
    });
    const stacked = comparison.elements.results.top >= comparison.elements.targets.bottom - 1;
    if (stacked !== expectedStacked) {
      throw new Error(`${width}px solver stacked state was ${stacked}, expected ${expectedStacked}`);
    }
    await page.locator(".solver-advanced-config > summary").click();
    await assertAdvancedSolverLayout(page, expectedColumns, `${width}px open`);
    await assertNoPageOverflow(page, `${width}px open solver details`);
    await page.locator(".solver-advanced-config > summary").click();

    if (width === 1280) {
      await page.locator("[data-shell-view='water']").click();
      await page.locator("#waterSection:not(.is-hidden)").waitFor();
      const narrowWaterLayout = await readWorkspaceGeometry(page, { water: "#waterSection" });
      assertWorkspaceMeasure(narrowWaterLayout, "water", 72, "1280px water analysis");
      const narrowWaterColumns = await page.locator("#waterValuesTable thead th").evaluateAll(
        (cells) => cells.map((cell) => cell.getBoundingClientRect().width),
      );
      if (Math.max(...narrowWaterColumns) - Math.min(...narrowWaterColumns) > 2) {
        throw new Error(`1280px water columns did not retain their equal layout: ${JSON.stringify(narrowWaterColumns)}`);
      }
      await page.locator("[data-shell-view='solver']").click();
      await page.locator("#solverMode:not(.is-hidden)").waitFor();
    }
  }

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.locator("[data-shell-view='fertilizers']").click();
  await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
}

async function exerciseCalculatorFertilizerSearch(page) {
  const firstInput = page.locator("#fertilizerSelectTable .searchable-combobox-input").first();

  await firstInput.fill("haka");
  const hakaphosOptions = page.locator(".searchable-combobox-option");
  const hakaphosNames = await hakaphosOptions.allTextContents();
  if (hakaphosNames.length < 2 || hakaphosNames.some((name) => !name.toLowerCase().includes("haka"))) {
    throw new Error(`Hakaphos search returned unexpected options: ${JSON.stringify(hakaphosNames)}`);
  }
  await firstInput.press("Escape");
  if (await firstInput.inputValue() !== "") {
    throw new Error("Escape committed the fertilizer search text");
  }

  await firstInput.fill("313");
  await page.locator(".searchable-combobox-option").click();
  await page.waitForFunction(() => document.querySelector(
    "#fertilizerSelectTable .searchable-combobox-input",
  )?.value.includes("313"));
  const selected313 = await firstInput.inputValue();

  await firstInput.fill("special");
  const specialNames = await page.locator(".searchable-combobox-option").allTextContents();
  if (specialNames.length < 2 || specialNames.some((name) => !name.toLowerCase().includes("special"))) {
    throw new Error(`Special search returned unexpected options: ${JSON.stringify(specialNames)}`);
  }
  await firstInput.press("Escape");

  await firstInput.fill("no-such-fertilizer");
  await page.locator(".searchable-combobox-listbox.is-empty").waitFor();
  await firstInput.press("Tab");
  await page.waitForFunction((expected) => document.querySelector(
    "#fertilizerSelectTable .searchable-combobox-input",
  )?.value === expected, selected313);

  await firstInput.fill("");
  await firstInput.press("Enter");
  await page.waitForFunction(() => document.querySelector(
    "#fertilizerSelectTable .searchable-combobox-input",
  )?.value === "");
}

async function chooseCalculatorFertilizer(page, rowIndex, query) {
  const input = page.locator("#fertilizerSelectTable .searchable-combobox-input").nth(rowIndex);
  await input.fill(query);
  await input.press("Enter");
  await page.waitForFunction(({ index, expected }) => {
    const inputs = document.querySelectorAll("#fertilizerSelectTable .searchable-combobox-input");
    return inputs[index]?.value.toLowerCase().includes(expected);
  }, { index: rowIndex, expected: query.toLowerCase() });
}

async function exerciseSelectedCalculatorRowRemoval(page) {
  await chooseCalculatorFertilizer(page, 0, "313");
  await page.locator("#addFertilizerRow").click();
  await page.locator("#addFertilizerRow").click();
  await chooseCalculatorFertilizer(page, 1, "haka");
  await chooseCalculatorFertilizer(page, 2, "solusop");
  await page.locator("#copyCalculatorResults:not([disabled])").waitFor();

  await page.locator("#calculatorTable tbody input").nth(1).focus();
  for (const selector of ["#fertilizerSelectTable tbody tr", "#calculatorTable tbody tr"]) {
    if (await page.locator(selector).nth(1).getAttribute("aria-selected") !== "true") {
      throw new Error(`Focused calculator row was not selected in ${selector}`);
    }
  }

  await page.locator("#removeFertilizerRow").click();
  await page.locator("#copyCalculatorResults:disabled").waitFor();
  await page.locator("#copyCalculatorResults:not([disabled])").waitFor();
  const remainingNames = await page.locator(
    "#fertilizerSelectTable .searchable-combobox-input",
  ).evaluateAll((inputs) => inputs.map((input) => input.value));
  if (remainingNames.length !== 2
      || remainingNames.some((name) => name.toLowerCase().includes("haka"))
      || !remainingNames.some((name) => name.includes("313"))
      || !remainingNames.some((name) => name.toLowerCase().includes("solusop"))) {
    throw new Error(`Selected calculator row was not removed exactly: ${JSON.stringify(remainingNames)}`);
  }

  await page.locator("#removeFertilizerRow").click();
  await page.locator("#removeFertilizerRow").click();
  const finalRowCount = await page.locator("#fertilizerSelectTable tbody tr").count();
  if (finalRowCount !== 1) {
    throw new Error(`Calculator removed its final component row: ${finalRowCount}`);
  }
}

async function exerciseExistingEditorRowRemoval(page) {
  const rows = page.locator("#fertilizerEditorTable tbody tr");
  const initialCount = await rows.count();
  const removedName = await rows.nth(1).locator('input[data-field="name"]').inputValue();
  await rows.nth(1).click();
  await page.locator("#fertEditorDeleteRow").click();
  const remainingNames = await page.locator(
    '#fertilizerEditorTable input[data-field="name"]',
  ).evaluateAll((inputs) => inputs.map((input) => input.value));
  if (remainingNames.length !== initialCount - 1 || remainingNames.includes(removedName)) {
    throw new Error(`Editor did not remove the selected row: ${JSON.stringify({
      removedName,
      initialCount,
      remainingCount: remainingNames.length,
    })}`);
  }
  await page.locator("#fertEditorLoad").click();
  await page.waitForFunction((expected) => document.querySelectorAll(
    "#fertilizerEditorTable tbody tr",
  ).length === expected, initialCount);
}

async function assertProfilePickerLayout(page, selector, expectedStacked, label) {
  const layout = await page.locator(selector).evaluate((select) => {
    const row = select.closest(".profile-picker-row");
    const actions = row?.querySelector(".profile-picker-actions");
    if (!row || !actions) return null;
    const rowRect = row.getBoundingClientRect();
    const selectRect = select.getBoundingClientRect();
    const actionsRect = actions.getBoundingClientRect();
    return {
      contained: selectRect.left >= rowRect.left - 1 && selectRect.right <= rowRect.right + 1,
      rowClientWidth: row.clientWidth,
      rowScrollWidth: row.scrollWidth,
      stacked: actionsRect.top >= selectRect.bottom - 1,
    };
  });
  if (!layout || !layout.contained || layout.rowScrollWidth > layout.rowClientWidth + 1) {
    throw new Error(`${label} overflows its picker row: ${JSON.stringify(layout)}`);
  }
  if (layout.stacked !== expectedStacked) {
    throw new Error(`${label} stacked state was ${layout.stacked}, expected ${expectedStacked}`);
  }
}

async function assertSelectedOptionTooltip(page, selector, label) {
  const select = page.locator(selector);
  const selectedText = (await select.locator("option:checked").innerText()).trim();
  const title = await select.getAttribute("title");
  if (title !== selectedText) {
    throw new Error(`${label} tooltip was ${JSON.stringify(title)}, expected ${JSON.stringify(selectedText)}`);
  }
}

async function assertProfilePickerBreakpoints(page, selector, label) {
  for (const [width, expectedStacked] of [[1280, false], [960, true], [640, true]]) {
    await page.setViewportSize({ width, height: 900 });
    await assertProfilePickerLayout(
      page,
      selector,
      expectedStacked,
      `${label} at ${width}px`,
    );
  }
  await page.setViewportSize({ width: 1280, height: 900 });
}

async function assertHistoryPreviewLayout(page, historyEntry) {
  if (await historyEntry.getAttribute("title")) {
    throw new Error("Solver history row still exposes a competing native tooltip");
  }
  await historyEntry.hover();
  const historyPreview = page.locator(".solver-history-preview:not(.is-hidden)");
  await historyPreview.waitFor();
  const previewLayout = await historyPreview.evaluate((element) => ({
    overflow: element.ownerDocument.defaultView.getComputedStyle(element).overflow,
    scrollHeight: element.scrollHeight,
    clientHeight: element.clientHeight,
  }));
  if (previewLayout.overflow !== "hidden" || previewLayout.scrollHeight > previewLayout.clientHeight + 1) {
    throw new Error(`Solver history hover preview is scrollable: ${JSON.stringify(previewLayout)}`);
  }
}

async function assertThemePalette(page, theme, expected) {
  const palette = await page.locator("body").evaluate((element) => {
    const styles = element.ownerDocument.defaultView.getComputedStyle(element);
    return {
      panel: styles.getPropertyValue("--app-panel").trim(),
      text: styles.getPropertyValue("--app-text").trim(),
      solver: styles.getPropertyValue("--app-solver").trim(),
    };
  });
  if (Object.entries(expected).some(([token, value]) => palette[token] !== value)) {
    throw new Error(`${theme} palette was not applied: ${JSON.stringify(palette)}`);
  }
}

async function waitForSmokeCondition(page, predicate, errorMessage) {
  for (let attempt = 0; attempt < 20 && !predicate(); attempt += 1) {
    await page.waitForTimeout(25);
  }
  if (!predicate()) {
    throw new Error(typeof errorMessage === "function" ? errorMessage() : errorMessage);
  }
}

async function exerciseProfileFavorite(page, button) {
  if (await button.getAttribute("aria-pressed") === "true") {
    await button.click();
    await page.locator("#favoriteProfile[aria-pressed='false']").waitFor();
  }
  await button.click();
  await page.locator("#favoriteProfile[aria-pressed='true']").waitFor();
  await button.click();
}

async function assertCrossViewLocalization(page) {
  const languageSelect = page.locator("#languageSelect");
  const originalLocale = await languageSelect.inputValue();
  const calculatorTypeCell = page.locator("#fertilizerSelectTable tbody td:nth-child(3)").first();

  await languageSelect.selectOption("zh");
  const chineseType = (await calculatorTypeCell.innerText()).trim();
  const germanType = new Map([
    ["固体", "Fest"],
    ["液体", "Flüssig"],
  ]).get(chineseType);
  if (!germanType) {
    throw new Error(`Calculator type was not localized in Chinese: ${JSON.stringify(chineseType)}`);
  }

  await page.locator("[data-shell-view='solver']").click();
  await page.locator("#solverMode:not(.is-hidden)").waitFor();
  await languageSelect.selectOption("de");
  await page.locator("[data-shell-view='fertilizers']").click();
  await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
  const refreshedType = (await calculatorTypeCell.innerText()).trim();
  if (refreshedType !== germanType) {
    throw new Error(`Calculator type stayed stale after returning from Solver: ${JSON.stringify({
      expected: germanType,
      actual: refreshedType,
    })}`);
  }

  await languageSelect.selectOption("zh");
  await page.locator("[data-shell-view='solver']").click();
  await page.locator("#solverMode:not(.is-hidden)").waitFor();
  const firstPriority = (await page.locator("#solverTargetsTable select").first()
    .locator("option").first().innerText()).trim();
  if (firstPriority !== "1 · 必须") {
    throw new Error(`Solver priority stayed stale after returning from Calculator: ${JSON.stringify(firstPriority)}`);
  }

  await languageSelect.selectOption(originalLocale);
  await page.locator("[data-shell-view='fertilizers']").click();
  await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
}

async function exerciseTargetProfileLoadModes(page, getLoadCount, savedFixedGrams) {
  await page.locator("#profileSelect").selectOption("Browser_solver_setup.yml");
  await page.locator("#includeSolverSetup").uncheck();
  await page.locator("#loadProfile").click();
  await waitForSmokeCondition(
    page,
    () => getLoadCount() === 1,
    "Target-only profile load did not complete",
  );
  if (await page.locator("#solverFixedTable input").count()) {
    throw new Error("Target-only profile load unexpectedly restored the Solver setup");
  }
  if (await page.locator("#includeSolverSetup").isChecked()) {
    throw new Error("Target-only profile load changed the setup checkbox");
  }

  await page.locator("#includeSolverSetup").check();
  await page.locator("#loadProfile").click();
  await page.waitForFunction(() => Array.from(
    document.querySelectorAll("#solverFixedTable input"),
    (input) => Number(input.value),
  ).some((value) => value === 2));
  if (getLoadCount() !== 2) {
    throw new Error(`Setup profile load count was ${getLoadCount()}, expected 2`);
  }
  const restoredFixedValues = await page.locator("#solverFixedTable input")
    .evaluateAll((inputs) => inputs.map((input) => input.value));
  if (!restoredFixedValues.some((value) => Number(value) === 2)) {
    throw new Error(
      `Loading a target profile did not restore its fixed amount: ${JSON.stringify({
        saved: savedFixedGrams,
        restored: restoredFixedValues,
      })}`,
    );
  }
}

(async () => {
  if (!executablePath) {
    throw new Error("Chrome or Chromium is required; set HORTICALC_BROWSER_PATH if it is installed elsewhere");
  }
  const browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  const dialogs = [];
  const smokeHistory = [];
  let acceptNextDialog = false;
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().startsWith("Failed to load resource:")) {
      errors.push(message.text());
    }
  });
  page.on("dialog", async (dialog) => {
    dialogs.push(dialog.message());
    if (acceptNextDialog) {
      acceptNextDialog = false;
      await dialog.accept();
    } else {
      await dialog.dismiss();
    }
  });

  await page.route("**/preferences", async (route) => {
    if (route.request().method() !== "PUT") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: route.request().postData() || "{}",
    });
  });
  await page.route("**/solver-history**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() === "DELETE") {
      smokeHistory.splice(0, smokeHistory.length, ...smokeHistory.filter((entry) => entry.pinned));
      await route.fulfill({ status: 200, contentType: "application/json", body: '{"status":"ok"}' });
      return;
    }
    if (request.method() === "PUT") {
      const entryId = decodeURIComponent(pathname.split("/").pop());
      const entry = smokeHistory.find(({ id }) => id === entryId);
      if (entry) entry.pinned = Boolean(request.postDataJSON().pinned);
      await route.fulfill({
        status: entry ? 200 : 404,
        contentType: "application/json",
        body: JSON.stringify(entry ? { status: "ok", pinned: entry.pinned } : { detail: "not found" }),
      });
      return;
    }
    if (pathname === "/solver-history") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          limit: 1000,
          entries: [...smokeHistory].sort((left, right) => Number(right.pinned) - Number(left.pinned)).map((entry) => ({
            id: entry.id,
            created_at: entry.created_at,
            pinned: Boolean(entry.pinned),
            liters: entry.result.liters,
            solver_model: entry.result.solver_model,
            targets_mg_per_l: {
              N_total: entry.result.targets_mg_per_l.N_total || 0,
              P: entry.result.targets_mg_per_l.P || 0,
              K: entry.result.targets_mg_per_l.K || 0,
            },
            fertilizer_count: entry.result.fertilizers.length,
          })),
        }),
      });
      return;
    }
    const entryId = decodeURIComponent(pathname.split("/").pop());
    const entry = smokeHistory.find(({ id }) => id === entryId);
    await route.fulfill({
      status: entry ? 200 : 404,
      contentType: "application/json",
      body: JSON.stringify(entry || { detail: "not found" }),
    });
  });

  try {
    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await page.waitForTimeout(250);
    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
    await page.locator("#apiStatus[data-state]:not([data-state='loading'])").waitFor();
    if (dialogs.length) throw new Error(`Application dialogs:\n${dialogs.join("\n")}`);
    const apiState = await page.locator("#apiStatus").getAttribute("data-state");
    if (apiState !== "ready") {
      throw new Error(`API startup state was ${apiState}: ${await page.locator("#apiStatus").innerText()}`);
    }
    const health = await page.evaluate(() => globalThis.fetch("/health").then((response) => response.json()));
    const displayedVersion = await page.locator("#appVersion").innerText();
    if (displayedVersion !== `v${health.version}`) {
      throw new Error(`Displayed version was ${displayedVersion}, expected v${health.version}`);
    }
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
    await assertNoPageOverflow(page, "desktop calculator");
    await assertFlexibleDesktopFrame(page);
    await assertUiScaleControls(page);
    await assertContentAwareWorkspaceBreakpoints(page);
    await exerciseCalculatorFertilizerSearch(page);
    await exerciseSelectedCalculatorRowRemoval(page);

    const profileFavorite = page.locator("#favoriteProfile");
    await page.locator("#favoriteProfile:disabled").waitFor();
    await page.locator("#profileSelect").selectOption({ index: 1 });
    await assertSelectedOptionTooltip(page, "#profileSelect", "calculator profile picker");
    await assertProfilePickerBreakpoints(page, "#profileSelect", "calculator profile picker");
    await exerciseProfileFavorite(page, profileFavorite);
    await page.locator("#loadProfile").click();

    await page.locator("#calculateBtn").click();
    await page.locator("#copyCalculatorResults:not([disabled])").waitFor();

    const volumeUnit = page.locator("#configVolumeUnit");
    if (await volumeUnit.locator("option").count() > 1) {
      await volumeUnit.selectOption({ index: 1 }, { force: true });
      if (await volumeUnit.inputValue() === "") throw new Error("Volume unit selection was not applied");
    }

    const themes = [
      "horticalc-dark", "horticalc-light", "high-contrast", "soil",
      "gch-classic", "vt-green", "blue-matrix", "tokyo-night",
      "solarized-light", "dracula", "gruvbox-dark", "catppuccin-mocha",
      "monokai-classic", "windows-95", "amber-crt",
    ];
    const newThemePalettes = {
      "solarized-light": { panel: "#fdf6e3", text: "#073642", solver: "#6c71c4" },
      dracula: { panel: "#282a36", text: "#f8f8f2", solver: "#ff79c6" },
      "gruvbox-dark": { panel: "#282828", text: "#fbf1c7", solver: "#d3869b" },
      "catppuccin-mocha": { panel: "#1e1e2e", text: "#cdd6f4", solver: "#cba6f7" },
      "monokai-classic": { panel: "#272822", text: "#f8f8f2", solver: "#ae81ff" },
      "windows-95": { panel: "#c0c0c0", text: "#000", solver: "#800080" },
      "amber-crt": { panel: "#0b0700", text: "#ffc247", solver: "#ff8f1f" },
    };
    for (const theme of themes) {
      await page.locator("#themeSelect").selectOption(theme, { force: true });
      const appliedTheme = await page.locator("body").getAttribute("data-theme");
      if (appliedTheme !== theme) throw new Error(`Theme ${theme} was not applied`);
      if (newThemePalettes[theme]) await assertThemePalette(page, theme, newThemePalettes[theme]);
    }

    await page.locator("[data-shell-view='water']").click();
    await page.locator("#waterSection:not(.is-hidden)").waitFor();
    await page.locator("#waterProfileSelect").selectOption({ index: 1 });
    await assertSelectedOptionTooltip(page, "#waterProfileSelect", "water profile picker");
    await assertProfilePickerBreakpoints(page, "#waterProfileSelect", "water profile picker");

    await page.locator("[data-shell-view='editor']").click();
    await page.locator("#fertilizerEditorMode:not(.is-hidden)").waitFor();
    await page.locator("#fertilizerEditorTable thead th:last-child[title]:not([title=''])").waitFor();
    await exerciseExistingEditorRowRemoval(page);

    await page.locator("[data-shell-view='solver']").focus();
    await page.keyboard.press("Enter");
    await page.locator("#solverMode:not(.is-hidden)").waitFor();
    await page.locator("#profileSelect").selectOption({ index: 1 });
    await page.locator("#deleteProfile:disabled").waitFor();
    await exerciseProfileFavorite(page, profileFavorite);
    await page.locator("#loadProfile").click();
    await page.locator("#solverAllowedFromRecipe").click();

    let savedTargetPayload = null;
    let savedTargetLoadCount = 0;
    let acceptedOverwriteCount = 0;
    await page.route("**/nutrient-solutions/Browser_solver_setup*", async (route) => {
      if (route.request().method() === "DELETE") {
        savedTargetPayload = null;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ok", filename: "Browser_solver_setup.yml" }),
        });
        return;
      }
      savedTargetLoadCount += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(savedTargetPayload || {}),
      });
    });
    await page.route("**/nutrient-solutions", async (route) => {
      if (route.request().method() === "POST") {
        const requestPayload = route.request().postDataJSON();
        if (savedTargetPayload && !requestPayload.overwrite) {
          await route.fulfill({
            status: 409,
            contentType: "application/json",
            body: JSON.stringify({
              detail: {
                code: "nutrient_solution_exists",
                name: savedTargetPayload.name,
                filename: "Browser_solver_setup.yml",
                has_solver_setup: true,
              },
            }),
          });
          return;
        }
        const storedPayload = { ...requestPayload };
        delete storedPayload.overwrite;
        if (requestPayload.overwrite) acceptedOverwriteCount += 1;
        savedTargetPayload = storedPayload;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ok", filename: "Browser_solver_setup.yml" }),
        });
        return;
      }
      const response = await route.fetch();
      const profiles = await response.json();
      if (savedTargetPayload) {
        profiles.push({
          name: savedTargetPayload.name,
          filename: "Browser_solver_setup.yml",
          deletable: true,
        });
      }
      await route.fulfill({ response, json: profiles });
    });

    await page.locator("#solverOverrides").evaluate((element) => { element.open = true; });
    const firstFixedAmount = page.locator("#solverFixedTable input").first();
    await firstFixedAmount.fill("2");
    await page.locator("#includeSolverSetup").uncheck();
    await page.locator("#solverSetupSaveWarning:not(.is-hidden)").waitFor();
    await page.locator("#profileName").fill("Browser solver setup");
    await page.locator("#saveProfile").click();
    if (dialogs.length !== 1 || !dialogs[0].includes("1")) {
      throw new Error(`Expected fixed-amount save warning, got: ${JSON.stringify(dialogs)}`);
    }
    dialogs.length = 0;
    if (savedTargetPayload) throw new Error("Dismissed target-only warning still saved the profile");

    await page.locator("#includeSolverSetup").check();
    await page.locator("#saveProfile").click();
    await page.locator("#profileSelect option", { hasText: "Browser solver setup" })
      .waitFor({ state: "attached" });
    if (!savedTargetPayload?.water_profile || savedTargetPayload.liters <= 0) {
      throw new Error(`Saved Solver setup is incomplete: ${JSON.stringify(savedTargetPayload)}`);
    }
    if (Object.values(savedTargetPayload.fixed_grams || {}).length !== 1) {
      throw new Error(`Saved fixed amounts are incomplete: ${JSON.stringify(savedTargetPayload)}`);
    }

    await page.locator("#solverAllowedClear").click();
    if (await page.locator("#solverFixedTable input").count()) {
      throw new Error("Clearing allowed fertilizers did not clear the fixed-amount table");
    }
    await exerciseTargetProfileLoadModes(
      page,
      () => savedTargetLoadCount,
      savedTargetPayload.fixed_grams,
    );

    dialogs.length = 0;
    acceptNextDialog = true;
    await page.locator("#saveProfile").click();
    await waitForSmokeCondition(
      page,
      () => acceptedOverwriteCount === 1 && dialogs.length === 1,
      () => `Confirmed profile overwrite did not resubmit safely: ${JSON.stringify({
        acceptedOverwriteCount,
        dialogs,
      })}`,
    );
    dialogs.length = 0;

    await page.locator("#solverFixedTable input").first().fill("0");
    await page.locator("#includeSolverSetup").uncheck();
    await page.locator("#saveProfile").click();
    await waitForSmokeCondition(page, () => dialogs.length > 0, "Expected stored-setup removal warning");
    if (dialogs.length !== 1 || !dialogs[0].toLowerCase().includes("setup")) {
      throw new Error(`Expected stored-setup removal warning, got: ${JSON.stringify(dialogs)}`);
    }
    dialogs.length = 0;
    await page.locator("#includeSolverSetup").check();
    await page.locator("#solverFixedTable input").first().fill("2");

    const litersInput = page.locator("#configLiters");
    const previousVolume = Number(await litersInput.inputValue());
    await litersInput.fill(String(previousVolume * 2));
    const scaledFixedValues = (await page.locator("#solverFixedTable input")
      .evaluateAll((inputs) => inputs.map((input) => input.value))).map(Number);
    if (!scaledFixedValues.some((value) => Math.abs(value - 4) <= 0.0001)) {
      throw new Error(`Fixed amount did not scale from 2 to 4: ${JSON.stringify(scaledFixedValues)}`);
    }

    dialogs.length = 0;
    acceptNextDialog = true;
    await page.locator("#deleteProfile:not(:disabled)").click();
    await waitForSmokeCondition(
      page,
      () => savedTargetPayload === null && dialogs.length === 1,
      "Confirmed profile deletion did not remove the saved target",
    );
    await page.locator("#profileSelect option[value='Browser_solver_setup.yml']")
      .waitFor({ state: "detached" });
    await page.locator("#deleteProfile:disabled").waitFor();
    dialogs.length = 0;

    let solveRequestCount = 0;
    await page.route("**/solve", async (route) => {
      solveRequestCount += 1;
      const requestNumber = solveRequestCount;
      const requestPayload = route.request().postDataJSON();
      const response = await route.fetch();
      const responsePayload = await response.json();
      smokeHistory.unshift({
        schema_version: 1,
        id: `smoke-${requestNumber}`,
        created_at: new Date().toISOString(),
        setup: {
          liters: requestPayload.liters,
          targets: requestPayload.targets,
          water_profile: requestPayload.water_profile,
          fertilizers_allowed: requestPayload.fertilizers_allowed,
          fixed_grams: requestPayload.fixed_grams,
          urea_as_nh4: requestPayload.urea_as_nh4,
          solver_config: requestPayload.solver_config,
        },
        result: responsePayload,
        fertilizer_kinds: Object.fromEntries(responsePayload.fertilizers.map(({ name }) => [name, "solid"])),
        calculation: {},
        pinned: false,
      });
      if (requestNumber === 1) await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({ response, json: responsePayload });
    });
    const potassiumInput = page.locator("#solverTargetsTable tbody tr")
      .filter({ has: page.locator("td:first-child", { hasText: /^K$/ }) })
      .locator('input[type="text"]');
    await potassiumInput.fill("50");
    await page.locator("#solveBtn").click();
    await potassiumInput.fill("100");
    await page.locator("#solveBtn").click();
    await page.locator("#copySolverResults:not([disabled])").waitFor();
    await assertSolverFrameAlignment(page, "1280px calculated solver");
    const potassiumResult = page.locator("#solverTargetsResultsTable tbody tr")
      .filter({ has: page.locator("td:first-child > span", { hasText: /^K$/ }) });
    await potassiumResult.locator("td:nth-child(2)").filter({ hasText: "100" }).waitFor();
    await page.waitForTimeout(650);
    if (!(await potassiumResult.locator("td:nth-child(2)").innerText()).includes("100")) {
      throw new Error("A stale solver response replaced the latest result");
    }
    await page.locator("#applySolverToCalculatorInline").click();
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
    await page.locator("[data-shell-view='solver']").click();
    await page.locator("#solverMode:not(.is-hidden)").waitFor();
    const firstHistoryRow = page.locator("#solverHistoryList .rail-history-row").first();
    await firstHistoryRow.locator(".rail-history-pin").click();
    await firstHistoryRow.locator(".rail-history-pin[aria-pressed='true']").waitFor();
    const historyEntry = page.locator("#solverHistoryList .rail-history-entry").first();
    await historyEntry.waitFor();
    await assertHistoryPreviewLayout(page, historyEntry);
    await potassiumInput.fill("1");
    await historyEntry.click();
    await page.locator("#solverHistoryDialog[open]").waitFor();
    await page.locator("#solverHistoryDialogOutput", { hasText: "100" }).waitFor();
    await page.locator("#copySolverHistoryEntry").click();
    await page.locator("#solverHistoryDialogStatus:not(:empty)").waitFor();
    await page.locator("#restoreSolverHistoryEntry").click();
    await page.waitForFunction(() => {
      const row = Array.from(document.querySelectorAll("#solverTargetsTable tbody tr"))
        .find((candidate) => candidate.querySelector("td")?.textContent.trim() === "K");
      return Number(row?.querySelector('input[type="text"]')?.value) === 100;
    });
    if (!(await page.locator("#copySolverResults").isDisabled())) {
      throw new Error("Restoring solver history unexpectedly retained a solved result");
    }
    dialogs.length = 0;
    acceptNextDialog = true;
  await page.locator(".rail-settings").evaluate((element) => { element.open = true; });
  await page.locator("#clearSolverHistory").click();
  await page.locator("#solverHistoryCount", { hasText: /^1$/ }).waitFor();
  await page.locator("#solverHistoryList .rail-history-pin[aria-pressed='true']").waitFor();
    dialogs.length = 0;
    await page.locator("[data-shell-view='fertilizers']").click();
    await page.waitForTimeout(250);
    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
    if (dialogs.length) throw new Error(`Application dialogs:\n${dialogs.join("\n")}`);
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
    await assertCrossViewLocalization(page);

    for (const width of [900, 600, 500]) {
      await page.setViewportSize({ width, height: 900 });
      await page.waitForTimeout(50);
      await assertNoPageOverflow(page, `${width}px layout`);
      if (width === 500) {
        await page.locator("#solverHistoryList .rail-history-entry").first().click();
        await page.locator("#solverHistoryDialog[open]").waitFor();
        await page.locator("#solverHistoryDialog form button[value='close']").click();
        await page.locator("#solverHistoryDialog").waitFor({ state: "hidden" });
      }
    }

    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
