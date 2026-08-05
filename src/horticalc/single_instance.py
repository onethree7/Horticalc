from __future__ import annotations

import json
import logging
import os
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PORT_RANGE = range(8000, 8101)
HEALTH_ENDPOINT = "/health"
ACTIVATION_ENDPOINT = "/_launcher/activate"
ACTIVATION_HEADER = "X-Horticalc-Activation"
HEALTH_TIMEOUT_SECONDS = 30.0
ACTIVATION_TIMEOUT_SECONDS = 5.0
LOCKFILE_NAME = "horticalc.lock.json"
LOCK_READ_GRACE_SECONDS = 0.5


@dataclass(frozen=True)
class ExistingInstance:
    pid: int
    port: int
    activation_token: str


def lockfile_path(root: Path) -> Path:
    return root / "user" / LOCKFILE_NAME


def _health_url(port: int) -> str:
    return f"http://127.0.0.1:{port}{HEALTH_ENDPOINT}"


def health_ok(port: int) -> bool:
    try:
        with urllib.request.urlopen(_health_url(port), timeout=1) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, ValueError):
        return False


def _write_json_stream(handle, payload: dict[str, Any]) -> None:
    json.dump(payload, handle, indent=2)
    handle.flush()
    os.fsync(handle.fileno())


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=path.parent,
            prefix=f".{path.name}.tmp-",
        ) as temp_file:
            temp_path = Path(temp_file.name)
            _write_json_stream(temp_file, payload)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            with suppress(OSError):
                temp_path.unlink(missing_ok=True)


def _lock_payload(port: int, activation_token: str, pid: int | None = None) -> dict[str, Any]:
    return {
        "pid": pid or os.getpid(),
        "port": port,
        "started_at": time.time(),
        "activation_token": activation_token,
    }


def read_lockfile(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    port = payload.get("port")
    pid = payload.get("pid")
    activation_token = payload.get("activation_token")
    if not isinstance(port, int) or port not in PORT_RANGE:
        return None
    if not isinstance(pid, int) or pid <= 0:
        return None
    if not isinstance(activation_token, str) or len(activation_token) < 32:
        return None
    return payload


def write_lockfile(path: Path, port: int, activation_token: str, pid: int | None = None) -> None:
    _atomic_write_json(path, _lock_payload(port, activation_token, pid))


def claim_lockfile(path: Path, port: int, activation_token: str, pid: int | None = None) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            _write_json_stream(handle, _lock_payload(port, activation_token, pid))
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return True


def remove_lockfile(path: Path, expected_pid: int | None = None) -> None:
    if expected_pid is not None:
        payload = read_lockfile(path)
        if payload is None or payload.get("pid") != expected_pid:
            return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logging.exception("Failed to remove lockfile: %s", path)


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes

            process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not process:
                return False
            ctypes.windll.kernel32.CloseHandle(process)
            return True
        except (AttributeError, OSError):
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def wait_for_existing_server(
    lock_path: Path,
    timeout_seconds: float = HEALTH_TIMEOUT_SECONDS,
    malformed_grace_seconds: float = LOCK_READ_GRACE_SECONDS,
) -> ExistingInstance | None:
    health_deadline = time.monotonic() + timeout_seconds
    malformed_deadline = time.monotonic() + malformed_grace_seconds
    while lock_path.exists():
        payload = read_lockfile(lock_path)
        if payload is None:
            if time.monotonic() < malformed_deadline:
                time.sleep(0.05)
                continue
            remove_lockfile(lock_path)
            return None

        instance = ExistingInstance(
            pid=payload["pid"],
            port=payload["port"],
            activation_token=payload["activation_token"],
        )
        if health_ok(instance.port):
            return instance
        if not _pid_is_running(instance.pid):
            remove_lockfile(lock_path, expected_pid=instance.pid)
            return None
        if time.monotonic() >= health_deadline:
            raise RuntimeError(f"Existing Horticalc process {instance.pid} did not become healthy.")
        time.sleep(0.1)
    return None


def activate_existing_instance(
    instance: ExistingInstance,
    timeout_seconds: float = ACTIVATION_TIMEOUT_SECONDS,
) -> bool:
    url = f"http://127.0.0.1:{instance.port}{ACTIVATION_ENDPOINT}"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        request = urllib.request.Request(
            url,
            data=b"",
            method="POST",
            headers={ACTIVATION_HEADER: instance.activation_token},
        )
        try:
            with urllib.request.urlopen(request, timeout=1) as response:
                return response.status == 204
        except urllib.error.HTTPError as exc:
            if exc.code != 503:
                return False
        except (urllib.error.URLError, ValueError):
            pass
        time.sleep(0.1)
    return False
