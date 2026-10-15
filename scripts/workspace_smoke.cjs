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
  await page.setViewportSize({ width: 2560, height: 1440 });
  await control.selectOption("100", { force: true });
  await page.waitForFunction(
    () => document.documentElement.style.getPropertyValue("--app-ui-scale") === "1",
  );

  for (const scale of [75, 125, 150]) {
    await control.selectOption(String(scale), { force: true });
    await page.waitForFunction(
      (expected) => document.documentElement.style.getPropertyValue("--app-ui-scale") === expected,
      String(scale / 100),
    );
    const frame = await page.locator(".app-shell").evaluate((element) => {
      const rect = element.getBoundingClientRect();
      const bodyRect = document.body.getBoundingClientRect();
      return {
        bodyBottom: bodyRect.bottom,
        left: rect.left,
        right: rect.right,
        viewportHeight: document.documentElement.clientHeight,
        viewportWidth: document.documentElement.clientWidth,
      };
    });
    const rightInset = frame.viewportWidth - frame.right;
    if (frame.left < -1 || rightInset < -1 || frame.left > 12 || rightInset > 12
        || Math.abs(frame.left - rightInset) > 1) {
      throw new Error(`${scale}% UI scale moved the app frame edge: ${JSON.stringify(frame)}`);
    }
    if (frame.bodyBottom < frame.viewportHeight - 1) {
      throw new Error(`${scale}% UI scale did not cover the viewport height: ${JSON.stringify(frame)}`);
    }
    await assertNoPageOverflow(page, `${scale}% UI scale`);
  }

  await page.setViewportSize({ width: 1280, height: 900 });
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

async function assertNitrogenFormShares(page) {
  let shares;
  const handler = async (route) => {
    const response = await route.fetch();
    const result = await response.json();
    result.npk_metrics.n_form_pct = shares;
    await route.fulfill({ response, json: result });
  };
  await page.route("**/calculate", handler);
  try {
    const pill = page.locator("#ionRatioList .ion-ratio-pill", { hasText: "NO3:NH4:UR (%)" });
    for (const [values, expected] of [
      [{ no3: 80, nh4: 15, urea: 5 }, "80:15:5"],
      [{ no3: 0, nh4: 100, urea: 0 }, "0:100:0"],
      [{ no3: 0, nh4: 0, urea: 0 }, "0:0:0"],
    ]) {
      shares = values;
      await page.locator("#calculateBtn").click();
      await pill.getByText(expected, { exact: true }).waitFor();
    }
    if (await page.locator("#ionRatioList span", { hasText: "Na:Mg" }).count()) {
      throw new Error("The sidebar still shows Na:Mg instead of nitrogen forms");
    }
  } finally {
    await page.unroute("**/calculate", handler);
  }
  await page.locator("#calculateBtn").click();
  await page.locator("#copyCalculatorResults:not([disabled])").waitFor();
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
  for (const scale of [75, 100, 150]) {
    await page.locator("#uiScaleSelect").selectOption(String(scale), { force: true });
    const height = await page.locator("#fertilizerEditorTableWrap").evaluate((table) => {
      table.scrollTop = table.scrollHeight;
      const frame = table.closest(".workspace").getBoundingClientRect();
      const rect = table.getBoundingClientRect();
      const lastRow = table.querySelector("tbody tr:last-child").getBoundingClientRect();
      return {
        bottomGap: frame.bottom - rect.bottom,
        height: rect.height,
        remainingHeight: frame.bottom - rect.top,
        lastRowBottom: lastRow.bottom,
        tableBottom: rect.bottom,
      };
    });
    if (height.bottomGap < -1 || height.bottomGap > 20
        || height.height < height.remainingHeight - 20
        || height.lastRowBottom > height.tableBottom + 1) {
      throw new Error(`${scale}% editor leaves unused height or clips its final row: ${JSON.stringify(height)}`);
    }
  }
  await page.locator("#uiScaleSelect").selectOption("100", { force: true });

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

module.exports = {
  assertNoPageOverflow,
  assertFlexibleDesktopFrame,
  assertUiScaleControls,
  assertNitrogenFormShares,
  assertContentAwareWorkspaceBreakpoints,
  assertSolverFrameAlignment,
};
