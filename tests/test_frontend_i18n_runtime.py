from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "frontend" / "i18n" / "runtime.js"


def test_locale_runtime_detects_browser_language_and_honors_saved_choice() -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required for executable frontend tests"
    runtime_path = json.dumps(str(RUNTIME))
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync({runtime_path}, "utf8");

function loadRuntime({{ languages, storedLocale = null }}) {{
  const document = {{
    documentElement: {{ lang: "" }},
    querySelector: () => null,
    querySelectorAll: () => [],
  }};
  const window = {{
    HORTICALC_I18N: {{ de: {{}}, en: {{}}, nl: {{}}, es: {{}}, zh: {{}} }},
    dispatchEvent: () => undefined,
  }};
  const context = {{
    window,
    document,
    navigator: {{ languages, language: languages[0] }},
    localStorage: {{
      getItem: () => storedLocale,
      setItem: () => undefined,
    }},
    CustomEvent: class CustomEvent {{}},
  }};
  vm.runInNewContext(source, context);
  return window.HorticalcI18n.getLocale();
}}

assert.equal(loadRuntime({{ languages: ["es-MX", "en-US"] }}), "es");
assert.equal(loadRuntime({{ languages: ["fr-FR"] }}), "en");
assert.equal(loadRuntime({{ languages: ["de-DE"], storedLocale: "zh" }}), "zh");
"""

    subprocess.run([node, "-e", script], cwd=ROOT, check=True)
