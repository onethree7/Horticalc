from __future__ import annotations

import shutil
import subprocess

from tests.frontend_assets import read_frontend_file


def test_frontend_decimal_helpers_execute_with_dot_and_comma() -> None:
    node = shutil.which("node")
    assert node is not None
    subprocess.run(
        [
            node,
            "--input-type=module",
            "-e",
            """
import assert from 'node:assert/strict';
import { parseDecimalInput, decimalInputValue } from './frontend/app/formatting.js';
assert.equal(parseDecimalInput('1,25'), 1.25);
assert.equal(parseDecimalInput('1.25'), 1.25);
assert.equal(parseDecimalInput(''), null);
assert.equal(decimalInputValue('bad', 7), 7);
""",
        ],
        check=True,
    )


def test_frontend_uses_decimal_text_inputs_and_dot_formatters() -> None:
    index_html = read_frontend_file("index.html")
    constants = read_frontend_file("app/constants.js")
    water = read_frontend_file("app/water.js")
    assert 'type="number"' not in index_html
    assert 'inputmode="decimal"' in index_html
    assert 'new Intl.NumberFormat("en-US"' in constants
    assert 'new Intl.NumberFormat("en-US"' in water
    assert "useGrouping: false" in constants
