import { qs } from "./dom.js";

export function createNotifications(i18n) {
  const apiStatus = qs("#apiStatus");
  const copySolverStatus = qs("#copySolverResultsStatus");
  const copyCalculatorStatus = qs("#copyCalculatorResultsStatus");
  const copyCalculatorButton = qs("#copyCalculatorResults");
  const solverApplyStatus = qs("#solverApplyStatus");
  let apiState = "ready";
  let solverTimer;
  let calculatorTimer;
  let applyTimer;

  function setApiStatus(message, state = "ready") {
    apiState = state;
    if (!apiStatus) return;
    apiStatus.textContent = message;
    apiStatus.dataset.state = state;
  }

  function refreshApiStatus() {
    const key = apiState === "loading"
      ? "status.loadingData"
      : apiState === "error"
        ? "status.dataIncomplete"
        : "status.apiReady";
    setApiStatus(i18n.t(key), apiState);
  }

  function timedStatus(element, message, timeout, timer, setTimer) {
    if (!element) return;
    element.textContent = message;
    if (timer) window.clearTimeout(timer);
    if (!message) {
      setTimer(undefined);
      return;
    }
    setTimer(window.setTimeout(() => {
      element.textContent = "";
      setTimer(undefined);
    }, timeout));
  }

  function setCopySolverStatus(message) {
    timedStatus(copySolverStatus, message, 2000, solverTimer, (value) => { solverTimer = value; });
  }
  function setCopyCalculatorStatus(message) {
    timedStatus(
      copyCalculatorStatus,
      message,
      2000,
      calculatorTimer,
      (value) => { calculatorTimer = value; },
    );
  }
  function setSolverApplyStatus(message) {
    timedStatus(solverApplyStatus, message, 2400, applyTimer, (value) => { applyTimer = value; });
  }

  function setCalculatorResultCurrent(isCurrent) {
    if (copyCalculatorButton) copyCalculatorButton.disabled = !isCurrent;
    if (!isCurrent) setCopyCalculatorStatus("");
  }

  async function copyText(text) {
    if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.setAttribute("readonly", "");
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      if (!document.execCommand("copy")) throw new Error(i18n.t("errors.copyFailed"));
    } finally {
      textArea.remove();
    }
  }

  function reportError(error, fallback = i18n.t("errors.unknown")) {
    window.alert(error?.message || fallback);
  }

  function finishStartup(errors) {
    setApiStatus(
      i18n.t(errors.length ? "status.dataIncomplete" : "status.apiReady"),
      errors.length ? "error" : "ready",
    );
  }

  return {
    copyText,
    finishStartup,
    refreshApiStatus,
    reportError,
    setApiStatus,
    setCalculatorResultCurrent,
    setCopyCalculatorStatus,
    setCopySolverStatus,
    setSolverApplyStatus,
  };
}
