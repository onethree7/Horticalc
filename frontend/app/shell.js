function setMode(mode) {
  const isSolver = mode === "solver";
  const isEditor = mode === "fertilizers";
  const isWater = mode === "water";
  calculatorMode.classList.toggle("is-hidden", isSolver || isEditor || isWater);
  solverMode.classList.toggle("is-hidden", !isSolver);
  fertilizerEditorMode.classList.toggle("is-hidden", !isEditor);
  waterSection.classList.toggle("is-hidden", !isWater);
  profileSection.classList.toggle("is-hidden", isEditor || isWater);
  if (!isEditor && !isWater) {
    setProfileMode(mode);
  }
}

function scrollToPanelAnchor(anchor, shouldFocus = true) {
  const target = qs(`[data-panel-anchor="${anchor}"]`);
  if (!target) {
    return;
  }
  const scroller = target.closest(".workspace");
  if (scroller) {
    const scrollerTop = scroller.getBoundingClientRect().top;
    const targetTop = target.getBoundingClientRect().top;
    const scrollTop = scroller.scrollTop + targetTop - scrollerTop - 12;
    scroller.scrollTo({ top: Math.max(0, scrollTop), behavior: "smooth" });
  } else {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  if (shouldFocus) {
    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  }
}

function showShellView(view, options = {}) {
  const config = shellViewConfigs[view] || shellViewConfigs.fertilizers;
  const shouldScroll = options.scroll !== false;
  currentShellView = shellViewConfigs[view] ? view : "fertilizers";
  setMode(config.mode);
  releaseInactiveHeavyViews();
  renderActiveHeavyView();
  qsa("[data-shell-view]").forEach((button) => {
    const isActive = button.dataset.shellView === view;
    button.classList.toggle("is-active", isActive);
    if (isActive) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  });
  updateLiveResultBar();
  if (shouldScroll) {
    window.setTimeout(() => scrollToPanelAnchor(config.anchor), 0);
  }
}

function bindShellNavigation() {
  qsa("[data-shell-view]").forEach((button) => {
    if (button.dataset.shellBound === "true") {
      return;
    }
    button.dataset.shellBound = "true";
    button.addEventListener("click", () => {
      showShellView(button.dataset.shellView || "fertilizers");
    });
  });
}

function updateLiveResultBar(data = lastCalculation) {
  if (!liveLastCalc) {
    return;
  }
  if (!data) {
    liveLastCalc.textContent = t("status.noCalculation");
    return;
  }

  liveLastCalc.textContent = t("status.updatedAt", {
    time: new Date().toLocaleTimeString(i18n.getLocale()),
  });
}

function setProfileMode(mode) {
  const nextMode = mode === "solver" ? "solver" : "calculator";
  if (nextMode !== currentProfileMode) {
    profileRequests.invalidate();
  }
  currentProfileMode = nextMode;
  const config = profileConfigs[currentProfileMode];
  profileSectionTitle.dataset.i18n = config.titleKey;
  profileSectionHint.dataset.i18n = config.hintKey;
  profileSectionTitle.textContent = t(config.titleKey);
  profileSectionHint.textContent = t(config.hintKey);
  solverProfileActions.classList.toggle("is-hidden", currentProfileMode !== "solver");
  renderProfileOptions();
}

function renderProfileOptions() {
  profileSelect.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = t("common.selectEmpty");
  profileSelect.appendChild(empty);

  const profiles = currentProfileMode === "solver" ? nutrientSolutions : recipeProfiles;
  profiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.filename;
    option.textContent = profile.name || profile.filename;
    profileSelect.appendChild(option);
  });
}
