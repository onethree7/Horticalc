import { qs, qsa } from "./dom.js";

const VIEW_CONFIG = {
  fertilizers: { mode: "calculator", anchor: "fertilizers" },
  water: { mode: "water", anchor: "water" },
  solver: { mode: "solver", anchor: "solver" },
  editor: { mode: "editor", anchor: "editor" },
};

export function createShellController({ i18n, onViewChange }) {
  const appVersion = qs("#appVersion");
  const calculatorMode = qs("#calculatorMode");
  const solverMode = qs("#solverMode");
  const editorMode = qs("#fertilizerEditorMode");
  const waterSection = qs("#waterSection");
  const profileSection = qs("#profileSection");
  const liveLastCalc = qs("#liveLastCalc");
  let currentView = "fertilizers";
  let lastCalculation = null;

  function setMode(mode) {
    calculatorMode.classList.toggle("is-hidden", mode !== "calculator");
    solverMode.classList.toggle("is-hidden", mode !== "solver");
    editorMode.classList.toggle("is-hidden", mode !== "editor");
    waterSection.classList.toggle("is-hidden", mode !== "water");
    profileSection.classList.toggle("is-hidden", mode === "editor" || mode === "water");
  }

  function scrollToAnchor(anchor) {
    const target = qs(`[data-panel-anchor="${anchor}"]`);
    if (!target) return;
    const scroller = target.closest(".workspace");
    if (scroller) {
      const top = scroller.scrollTop
        + target.getBoundingClientRect().top
        - scroller.getBoundingClientRect().top
        - 12;
      scroller.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
    } else {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  }

  function updateLiveResult(data = lastCalculation) {
    lastCalculation = data;
    if (!liveLastCalc) return;
    liveLastCalc.textContent = data
      ? i18n.t("status.updatedAt", { time: new Date().toLocaleTimeString(i18n.getLocale()) })
      : i18n.t("status.noCalculation");
  }

  function show(view, { scroll = true } = {}) {
    const nextView = VIEW_CONFIG[view] ? view : "fertilizers";
    const previousView = currentView;
    currentView = nextView;
    setMode(VIEW_CONFIG[nextView].mode);
    qsa("[data-shell-view]").forEach((button) => {
      const active = button.dataset.shellView === nextView;
      button.classList.toggle("is-active", active);
      if (active) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });
    onViewChange(nextView, previousView);
    updateLiveResult();
    if (scroll) window.setTimeout(() => scrollToAnchor(VIEW_CONFIG[nextView].anchor), 0);
  }

  function mount({ version = "" } = {}) {
    if (appVersion) appVersion.textContent = version ? `v${version}` : "";
    qsa("[data-shell-view]").forEach((button) => {
      button.addEventListener("click", () => show(button.dataset.shellView || "fertilizers"));
    });
    show("fertilizers", { scroll: false });
  }

  return {
    get currentView() { return currentView; },
    isActive(view) { return currentView === view; },
    mount,
    refreshLocalized() { updateLiveResult(); },
    show,
    updateLiveResult,
  };
}
