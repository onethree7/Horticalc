import { qs } from "./dom.js";
import { buildSolverPrintableText } from "./solver_printable.js";

const HISTORY_DEFAULT_LIMIT = 1000;
const HISTORY_PREVIEW_MAX_LINES = 18;

function finiteTarget(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

export function missingHistoryFertilizers(setup = {}, availableFertilizers = []) {
  const available = new Set(availableFertilizers.map((fertilizer) => fertilizer.name));
  const names = new Set([
    ...(setup.fertilizers_allowed || []),
    ...Object.keys(setup.fixed_grams || {}),
  ]);
  return [...names].filter((name) => !available.has(name));
}

export function formatSolverHistorySummary(entry, { locale, units }) {
  const date = new Date(entry?.created_at);
  const timestamp = Number.isNaN(date.getTime())
    ? "–"
    : new Intl.DateTimeFormat(locale, {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  const targets = entry?.targets_mg_per_l || {};
  const formatTarget = (value) => String(Math.round(finiteTarget(value) * 10) / 10);
  const volume = units.formatVolumeValue(units.litersToDisplayVolume(Number(entry?.liters) || 0));
  const volumeUnit = units.getVolumeUnitDefinition().symbol;
  const nutrients = ["N_total", "P", "K"]
    .map((key) => `${key === "N_total" ? "N" : key}${formatTarget(targets[key])}`)
    .join("/");
  return `${timestamp} · ${volume} ${volumeUnit} · ${nutrients}`;
}

export function compactSolverHistoryPreview(text, moreLabel, maxLines = HISTORY_PREVIEW_MAX_LINES) {
  const lines = String(text || "").split("\n");
  if (lines.length <= maxLines) return lines.join("\n");
  return `${lines.slice(0, maxLines).join("\n")}\n\n… ${moreLabel}`;
}

export function createHistoryController({ api, i18n, notifications, units, onRestore }) {
  const card = qs("#solverHistoryCard");
  const list = qs("#solverHistoryList");
  const empty = qs("#solverHistoryEmpty");
  const count = qs("#solverHistoryCount");
  const dialog = qs("#solverHistoryDialog");
  const dialogMeta = qs("#solverHistoryDialogMeta");
  const dialogOutput = qs("#solverHistoryDialogOutput");
  const dialogStatus = qs("#solverHistoryDialogStatus");
  const copyButton = qs("#copySolverHistoryEntry");
  const restoreButton = qs("#restoreSolverHistoryEntry");
  const detailCache = new Map();
  const t = (key, params) => i18n.t(key, params);
  let entries = [];
  let limit = HISTORY_DEFAULT_LIMIT;
  let activePreviewId = "";
  let activeDialogDetail = null;
  let preview = null;
  let mounted = false;

  function detailText(detail) {
    const setup = detail?.setup || {};
    return buildSolverPrintableText({
      result: detail?.result || {},
      calculation: detail?.calculation || {},
      liters: setup.liters ?? detail?.result?.liters,
      osmosisPercent: setup.water_profile?.osmosis_percent || 0,
      fertilizerKinds: detail?.fertilizer_kinds || {},
      t,
      units,
    });
  }

  function renderEmpty(messageKey = limit === 0 ? "history.disabled" : "history.empty") {
    empty.textContent = t(messageKey);
    empty.dataset.i18n = messageKey;
    empty.classList.toggle("is-hidden", entries.length > 0);
  }

  function positionPreview(button) {
    const anchor = button.getBoundingClientRect();
    const bounds = preview.getBoundingClientRect();
    const gap = 10;
    let left = anchor.right + gap;
    if (left + bounds.width > window.innerWidth - gap) left = anchor.left - bounds.width - gap;
    left = Math.max(gap, Math.min(left, window.innerWidth - bounds.width - gap));
    const top = Math.max(gap, Math.min(anchor.top, window.innerHeight - bounds.height - gap));
    preview.style.left = `${left}px`;
    preview.style.top = `${top}px`;
  }

  async function fetchDetail(entryId) {
    if (!detailCache.has(entryId)) {
      detailCache.set(
        entryId,
        api.fetchSolverHistoryEntry(entryId, t("errors.loadSolverHistoryEntry"))
          .catch((error) => {
            detailCache.delete(entryId);
            throw error;
          }),
      );
    }
    return detailCache.get(entryId);
  }

  async function showPreview(button, entryId) {
    if (!window.matchMedia("(hover: hover)").matches) return;
    activePreviewId = entryId;
    preview.textContent = t("status.loadingData");
    preview.classList.remove("is-hidden");
    positionPreview(button);
    try {
      const detail = await fetchDetail(entryId);
      if (activePreviewId !== entryId) return;
      preview.textContent = compactSolverHistoryPreview(
        detailText(detail),
        t("history.previewMore"),
      );
      positionPreview(button);
    } catch {
      if (activePreviewId === entryId) preview.textContent = t("history.previewUnavailable");
    }
  }

  function hidePreview(entryId) {
    if (activePreviewId !== entryId) return;
    activePreviewId = "";
    preview.classList.add("is-hidden");
  }

  async function openDetail(entry) {
    activePreviewId = "";
    preview.classList.add("is-hidden");
    activeDialogDetail = null;
    dialogMeta.textContent = formatSolverHistorySummary(entry, { locale: i18n.getLocale(), units });
    dialogOutput.textContent = t("status.loadingData");
    dialogStatus.textContent = "";
    copyButton.disabled = true;
    restoreButton.disabled = true;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
    try {
      const detail = await fetchDetail(entry.id);
      activeDialogDetail = detail;
      dialogOutput.textContent = detailText(detail);
      copyButton.disabled = false;
      restoreButton.disabled = false;
    } catch (error) {
      dialogOutput.textContent = t("history.previewUnavailable");
      notifications.reportError(error, t("errors.loadSolverHistoryEntry"));
    }
  }

  function renderEntries() {
    const locale = i18n.getLocale();
    list.replaceChildren(...entries.map((entry) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "rail-history-entry";
      button.dataset.historyId = entry.id;
      button.setAttribute("role", "listitem");
      button.textContent = formatSolverHistorySummary(entry, { locale, units });
      button.addEventListener("pointerenter", () => showPreview(button, entry.id));
      button.addEventListener("pointerleave", () => hidePreview(entry.id));
      button.addEventListener("focus", () => showPreview(button, entry.id));
      button.addEventListener("blur", () => hidePreview(entry.id));
      button.addEventListener("click", () => openDetail(entry));
      return button;
    }));
    count.textContent = String(entries.length);
    renderEmpty();
  }

  async function refresh() {
    try {
      const data = await api.fetchSolverHistory(t("errors.loadSolverHistory"));
      entries = Array.isArray(data?.entries) ? data.entries : [];
      limit = Number.isInteger(data?.limit) ? data.limit : HISTORY_DEFAULT_LIMIT;
      renderEntries();
    } catch {
      entries = [];
      renderEntries();
      renderEmpty("history.unavailable");
    }
  }

  function refreshDisplay() {
    renderEntries();
    if (activeDialogDetail) dialogOutput.textContent = detailText(activeDialogDetail);
  }

  function bindDialog() {
    copyButton.addEventListener("click", async () => {
      try {
        await notifications.copyText(dialogOutput.textContent);
        dialogStatus.textContent = t("status.copied");
      } catch (error) {
        notifications.reportError(error, t("errors.copyFailed"));
        dialogStatus.textContent = t("status.copyFailed");
      }
    });
    restoreButton.addEventListener("click", async () => {
      if (!activeDialogDetail) return;
      try {
        await onRestore(activeDialogDetail.setup || {});
        notifications.setSolverApplyStatus(t("history.restored"));
        if (typeof dialog.close === "function") dialog.close();
        else dialog.removeAttribute("open");
      } catch (error) {
        notifications.reportError(error, t("errors.restoreSolverHistory"));
      }
    });
    dialog.addEventListener("close", () => {
      activeDialogDetail = null;
      dialogStatus.textContent = "";
    });
  }

  function mount() {
    if (mounted) return;
    mounted = true;
    preview = document.createElement("pre");
    preview.className = "solver-history-preview is-hidden";
    preview.setAttribute("aria-hidden", "true");
    document.body.appendChild(preview);
    bindDialog();
    if (card) card.open = true;
    refresh();
  }

  return {
    mount,
    refresh,
    refreshDisplay,
    refreshLocalized: refreshDisplay,
  };
}
