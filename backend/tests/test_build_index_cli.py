from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_build_index_cli_imports_backend_package_from_outside_backend(tmp_path: Path):
    backend_root = Path(__file__).resolve().parents[1]
    script = backend_root / "scripts" / "build_index.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert "--index-version" in result.stdout
    assert "--min-sources" in result.stdout
