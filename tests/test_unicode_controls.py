import subprocess
import sys


def test_no_unicode_control_characters() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_unicode_controls.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
