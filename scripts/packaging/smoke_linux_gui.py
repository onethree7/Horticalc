#!/usr/bin/env python3
"""Exercise the packaged Linux GUI lifecycle inside an existing X display."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

WINDOW_TITLE = "Horticalc GUI"


def wait_until(predicate, timeout_seconds: float, description: str):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {description}")


def health_ok(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def visible_window_id(process_pid: int) -> str | None:
    result = subprocess.run(
        [
            "xdotool",
            "search",
            "--onlyvisible",
            "--pid",
            str(process_pid),
            "--name",
            f"^{WINDOW_TITLE}$",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    ids = result.stdout.split()
    return ids[0] if ids else None


def run_gui_smoke(executable: Path, app_root: Path) -> None:
    executable = executable.resolve()
    app_root = app_root.resolve()
    if not executable.is_file():
        raise RuntimeError(f"Packaged executable does not exist: {executable}")
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("DISPLAY is not set; run this check under Xvfb")

    lock_path = app_root / "user" / "horticalc.lock.json"
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as output:
        process = subprocess.Popen(
            [str(executable)],
            cwd=app_root,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_until(lock_path.exists, 30, "the launcher lock")
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            port = lock.get("port")
            if not isinstance(port, int):
                raise RuntimeError("Launcher lock does not contain an integer port")
            wait_until(lambda: health_ok(port), 30, "the local API health check")
            window_id = wait_until(
                lambda: visible_window_id(process.pid),
                45,
                f'the visible "{WINDOW_TITLE}" window owned by PID {process.pid}',
            )

            second_launch = subprocess.run(
                [str(executable)],
                cwd=app_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
            if second_launch.returncode != 0:
                raise RuntimeError(
                    "Second launch failed instead of activating the existing window:\n"
                    f"{second_launch.stdout}{second_launch.stderr}"
                )
            if process.poll() is not None:
                raise RuntimeError("Primary Horticalc process exited during second-instance activation")
            current_lock = json.loads(lock_path.read_text(encoding="utf-8"))
            if current_lock.get("pid") != process.pid:
                raise RuntimeError("Second launch replaced the primary launcher lock")
            if not health_ok(port):
                raise RuntimeError("Second launch disrupted the primary local API")
            window_id = wait_until(
                lambda: visible_window_id(process.pid),
                10,
                "the primary window after second-instance activation",
            )

            subprocess.run(["xdotool", "windowclose", window_id], check=True)
            process.wait(timeout=20)
            if process.returncode != 0:
                raise RuntimeError(f"Horticalc exited with status {process.returncode}")
            wait_until(lambda: not lock_path.exists(), 10, "launcher lock removal")
            wait_until(lambda: not health_ok(port), 10, "local API shutdown")
        except Exception:
            output.seek(0)
            captured = output.read()
            if captured:
                print("Packaged GUI output:\n" + captured)
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("app_root", type=Path)
    args = parser.parse_args()
    run_gui_smoke(args.executable, args.app_root)
    print("Packaged Linux GUI lifecycle smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
