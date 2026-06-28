from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REQUEST_GATE = ROOT / "frontend" / "request_gate.js"


def test_latest_request_gate_executes_expected_semantics() -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required for executable frontend tests"
    module_path = json.dumps(str(REQUEST_GATE))
    script = f"""
const assert = require("node:assert/strict");
const {{ createLatestRequestGate }} = require({module_path});

const gate = createLatestRequestGate();
const first = gate.reserve();
const second = gate.reserve();
assert.equal(gate.isCurrent(first), false);
assert.equal(gate.isCurrent(second), true);
gate.invalidate();
assert.equal(gate.isCurrent(second), false);

const independent = createLatestRequestGate();
const token = independent.reserve();
assert.equal(independent.isCurrent(token), true);
assert.equal(gate.isCurrent(token), false);
"""

    subprocess.run([node, "-e", script], cwd=ROOT, check=True)
