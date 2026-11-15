"""Ephemeral CI probe for index-artifact size, load cost and file rollback.

This is a measurement/test helper, not production delivery code. Its filesystem
simulation runs only inside a temporary directory on the GitHub Actions runner.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def simulate_replace_and_rollback(artifact_path: Path) -> dict[str, str]:
    """Exercise same-filesystem replacement and rollback without touching source data."""
    from app.index_artifact import IndexArtifactError, load_index_artifact

    original_bytes = artifact_path.read_bytes()
    original = load_index_artifact(artifact_path)

    with tempfile.TemporaryDirectory(prefix="png-index-probe-") as temp_dir:
        root = Path(temp_dir)
        active = root / "active-index.json"
        backup = root / "backup-index.json"
        candidate = root / "candidate-index.json"
        invalid_candidate = root / "invalid-candidate-index.json"

        active.write_bytes(original_bytes)
        backup.write_bytes(original_bytes)

        payload: dict[str, Any] = json.loads(original_bytes.decode("utf-8"))
        payload["index_version"] = f"{original.index_version}-replacement-probe"
        candidate.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

        # A candidate must validate before it is allowed to replace the active file.
        load_index_artifact(candidate)
        invalid_payload = dict(payload)
        invalid_payload["records_sha256"] = "0" * 64
        invalid_candidate.write_text(
            json.dumps(invalid_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        try:
            load_index_artifact(invalid_candidate)
        except IndexArtifactError:
            pass
        else:
            raise RuntimeError("corrupt candidate unexpectedly passed validation")

        if active.read_bytes() != original_bytes:
            raise RuntimeError("invalid candidate changed the active artifact")

        os.replace(candidate, active)
        replaced = load_index_artifact(active)
        if replaced.index_version != f"{original.index_version}-replacement-probe":
            raise RuntimeError("replacement did not activate the validated candidate")

        os.replace(backup, active)
        restored = load_index_artifact(active)
        if restored.index_version != original.index_version or active.read_bytes() != original_bytes:
            raise RuntimeError("rollback did not restore the original artifact")

    return {
        "invalid_candidate_rejected": "PASS",
        "replacement": "PASS",
        "rollback": "PASS",
        "scope": "temporary directory on GitHub Actions runner only",
    }


def _worker(artifact_path: Path) -> int:
    import resource
    from time import perf_counter

    from app.index_artifact import load_index_artifact

    started = perf_counter()
    artifact = load_index_artifact(artifact_path)
    load_ms = (perf_counter() - started) * 1000
    # GitHub Actions uses Ubuntu; ru_maxrss is reported in KiB on Linux.
    peak_rss_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    print(json.dumps({
        "index_version": artifact.index_version,
        "record_count": len(artifact.records),
        "load_validate_ms": round(load_ms, 3),
        "worker_peak_rss_bytes": peak_rss_bytes,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }, sort_keys=True))
    return 0


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        return _worker(Path(sys.argv[2]))

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/profile_index_artifact.py <artifact-path>")

    artifact_path = Path(sys.argv[1]).resolve()
    if not artifact_path.is_file():
        raise SystemExit(f"Artifact does not exist: {artifact_path}")

    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker", str(artifact_path)],
        cwd=BACKEND_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    process_wall_ms = (time.perf_counter() - started) * 1000
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or completed.stdout or "Artifact profiling subprocess failed")

    worker = json.loads(completed.stdout.strip().splitlines()[-1])
    simulation = simulate_replace_and_rollback(artifact_path)

    print(f"ARTIFACT_BYTES={artifact_path.stat().st_size}")
    print(f"RECORD_COUNT={worker['record_count']}")
    print(f"LOAD_VALIDATE_MS={worker['load_validate_ms']}")
    print(f"PROCESS_STARTUP_IMPORT_AND_LOAD_MS={process_wall_ms:.3f}")
    print(f"WORKER_PEAK_RSS_BYTES={worker['worker_peak_rss_bytes']}")
    print(f"PROFILE_PYTHON_VERSION={worker['python_version']}")
    print(f"PROFILE_PLATFORM={worker['platform']}")
    print(f"INVALID_CANDIDATE_REJECTION={simulation['invalid_candidate_rejected']}")
    print(f"TEMP_FILE_REPLACEMENT={simulation['replacement']}")
    print(f"TEMP_FILE_ROLLBACK={simulation['rollback']}")
    print(f"FILESYSTEM_TEST_SCOPE={simulation['scope']}")
    print("NOTICE=CI runner measurements only; not Render startup, memory or filesystem evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
