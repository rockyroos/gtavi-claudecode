"""Self-check: scripts must not crash printing emoji on a cp1252 console (Windows default). python tests/test_common.py"""
import os, subprocess, sys
from pathlib import Path

scripts = Path(__file__).parent.parent / "scripts"
env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
for mod in ("common", "questions", "payouts"):  # questions/payouts do not otherwise import common
    r = subprocess.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, r'{scripts}'); import {mod}; print('\U0001f534 ok')"],
                       capture_output=True, env=env)
    assert r.returncode == 0 and "ok" in r.stdout.decode("utf-8"), (mod, r.stderr[-300:])
print("ok")
