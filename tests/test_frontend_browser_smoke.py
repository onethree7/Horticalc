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
SESSION_TOKEN = "t" * 43


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
@pytest.mark.parametrize("smoke_script", ["frontend_smoke.cjs", "state_smoke.cjs"])
def test_frontend_workflows_execute_without_browser_errors(isolated_app_root: Path, smoke_script: str) -> None:
    assert (ROOT / "node_modules" / "playwright").exists() or os.environ.get("NODE_PATH"), (
        "Run npm ci to install the Playwright browser test dependency"
    )

    port = _free_port()
    shutil.copytree(ROOT / "frontend", isolated_app_root / "frontend")
    url = f"http://127.0.0.1:{port}"
    server_environment = {
        **os.environ,
        "HORTICALC_TEST_DISABLE_SOLVER_HISTORY": "1",
        "HORTICALC_SESSION_TOKEN": SESSION_TOKEN,
    }
    server = subprocess.Popen(
        [
            os.fspath(Path(os.sys.executable)),
            "-c",
            "import sys; from pathlib import Path; from horticalc import paths; "
            "paths.app_root = lambda: Path(sys.argv[1]); import uvicorn; "
            "uvicorn.run('api.app:app', host='127.0.0.1', port=int(sys.argv[2]))",
            str(isolated_app_root),
            str(port),
        ],
        cwd=ROOT,
        env=server_environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server(url)
        environment = {**os.environ, "HORTICALC_TEST_URL": f"{url}/?session={SESSION_TOKEN}"}
        result = subprocess.run(
            ["node", os.fspath(ROOT / "scripts" / smoke_script)], cwd=ROOT, env=environment, check=False, timeout=120
        )
        assert result.returncode == 0
    finally:
        server.terminate()
        server.wait(timeout=5)
