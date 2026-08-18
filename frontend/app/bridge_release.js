/*
 * Migration-only integration for the final legacy WebView release.
 * Copy this file and webview_state_bridge.js into the legacy frontend and call
 * installNativeStateExport() once after the settings view is mounted. Nothing
 * from this module is bundled into the native Rust executable.
 */

import { exportUiState } from "./webview_state_bridge.js";

export function installNativeStateExport({
  documentRef = globalThis.document,
  anchorSelector = ["#settingsActions", ".rail-settings-controls"],
  buttonId = "exportNativeState",
  label = "Export native state",
  filename = "ui_state.json",
} = {}) {
  if (!documentRef?.createElement) return false;
  if (documentRef.getElementById?.(buttonId)) return false;
  const selectors = Array.isArray(anchorSelector) ? anchorSelector : [anchorSelector];
  const parent = selectors
    .map((selector) => documentRef.querySelector?.(selector))
    .find(Boolean);
  if (!parent) return false;
  const button = documentRef.createElement("button");
  button.type = "button";
  button.id = buttonId;
  button.setAttribute?.("aria-label", label);
  button.dataset && (button.dataset.migrationBridge = "native-state");
  button.textContent = label;
  button.addEventListener("click", () => {
    exportUiState({ documentRef, filename });
  });
  parent.appendChild(button);
  return true;
}
