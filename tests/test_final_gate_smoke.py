import subprocess
import sys


def test_final_gate_smoke_script_runs():
    proc = subprocess.run(
        [sys.executable, "scripts/smoke_final_gate.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
