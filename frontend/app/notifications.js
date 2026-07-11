function setApiStatus(message, state = "ready") {
  if (!apiStatus) {
    return;
  }
  apiStatus.textContent = message;
  apiStatus.dataset.state = state;
}

function refreshApiStatusLabel() {
  if (!apiStatus) {
    return;
  }
  if (apiStatus.dataset.state === "loading") {
    setApiStatus(t("status.loadingData"), "loading");
  } else if (apiStatus.dataset.state === "error") {
    setApiStatus(t("status.dataIncomplete"), "error");
  } else {
    setApiStatus(t("status.apiReady"), "ready");
  }
}
function setCopySolverStatus(message) {
  if (!copySolverResultsStatus) {
    return;
  }
  copySolverResultsStatus.textContent = message;
  if (copySolverStatusTimer) {
    window.clearTimeout(copySolverStatusTimer);
  }
  copySolverStatusTimer = window.setTimeout(() => {
    copySolverResultsStatus.textContent = "";
    copySolverStatusTimer = null;
  }, 2000);
}

function setCopyCalculatorStatus(message) {
  if (!copyCalculatorResultsStatus) {
    return;
  }
  copyCalculatorResultsStatus.textContent = message;
  if (copyCalculatorStatusTimer) {
    window.clearTimeout(copyCalculatorStatusTimer);
  }
  if (!message) {
    copyCalculatorStatusTimer = null;
    return;
  }
  copyCalculatorStatusTimer = window.setTimeout(() => {
    copyCalculatorResultsStatus.textContent = "";
    copyCalculatorStatusTimer = null;
  }, 2000);
}

function setCalculatorResultCurrent(isCurrent) {
  calculatorResultCurrent = Boolean(isCurrent && lastCalculation);
  if (copyCalculatorResultsButton) {
    copyCalculatorResultsButton.disabled = !calculatorResultCurrent;
  }
  if (!calculatorResultCurrent) {
    setCopyCalculatorStatus("");
  }
}

function setSolverApplyStatus(message) {
  if (!solverApplyStatus) {
    return;
  }
  solverApplyStatus.textContent = message;
  if (solverApplyStatusTimer) {
    window.clearTimeout(solverApplyStatusTimer);
  }
  solverApplyStatusTimer = window.setTimeout(() => {
    solverApplyStatus.textContent = "";
    solverApplyStatusTimer = null;
  }, 2400);
}

function copyTextWithFallback(text) {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }

  return new Promise((resolve, reject) => {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.setAttribute("readonly", "");
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      const successful = document.execCommand("copy");
      document.body.removeChild(textArea);
      if (!successful) {
        reject(new Error(t("errors.copyFailed")));
        return;
      }
      resolve();
    } catch (error) {
      document.body.removeChild(textArea);
      reject(error);
    }
  });
}

function reportError(error, fallbackMessage = t("errors.unknown")) {
  const message = error?.message || fallbackMessage;
  alert(message);
}

function finishStartupStatus(errors) {
  if (errors.length) {
    setApiStatus(t("status.dataIncomplete"), "error");
  } else {
    setApiStatus(t("status.apiReady"), "ready");
  }
}
