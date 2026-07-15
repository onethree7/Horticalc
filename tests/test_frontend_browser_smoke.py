from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = ROOT / "scripts" / "frontend_smoke.cjs"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{url}/health", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise AssertionError("Timed out waiting for the frontend test server")


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_frontend_workflows_execute_without_browser_errors() -> None:
    assert (ROOT / "node_modules" / "playwright").exists() or os.environ.get("NODE_PATH"), (
        "Run npm ci to install the Playwright browser test dependency"
    )

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    server = subprocess.Popen(
        [
            os.fspath(Path(os.sys.executable)),
            "-m",
            "uvicorn",
            "api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server(url)
        environment = {**os.environ, "HORTICALC_TEST_URL": url}
        subprocess.run(["node", os.fspath(SMOKE_SCRIPT)], cwd=ROOT, env=environment, check=True)
    finally:
        server.terminate()
        server.wait(timeout=5)
