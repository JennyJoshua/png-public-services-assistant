"""Non-production Render probe for packaged index loading and filesystem behavior.

This module is isolated from the production API and never serves passage text.
"""
from __future__ import annotations

import json
import os
import platform
import resource
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from app.index_artifact import IndexArtifactError, load_index_artifact

MODULE_IMPORTED_AT = time.perf_counter()
ARTIFACT_PATH = Path(
    os.getenv("INDEX_ARTIFACT_PATH", "data/public-services-index-v1.json")
)


def _peak_rss_bytes() -> int:
    # Render's Linux runtime reports ru_maxrss in KiB.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)


def _filesystem_probe(artifact_path: Path) -> dict[str, str]:
    """Test invalid-candidate rejection, atomic replacement and rollback beside artifact."""
    original_bytes = artifact_path.read_bytes()
    original = load_index_artifact(artifact_path)

    # Keep the probe on the artifact's filesystem; TemporaryDirectory cleans up on exit.
    with tempfile.TemporaryDirectory(
        prefix=".render-index-probe-", dir=str(artifact_path.parent)
    ) as temp_dir:
        root = Path(temp_dir)
        active = root / "active-index.json"
        backup = root / "backup-index.json"
        candidate = root / "candidate-index.json"
        invalid = root / "invalid-index.json"

        active.write_bytes(original_bytes)
        backup.write_bytes(original_bytes)

        payload: dict[str, Any] = json.loads(original_bytes.decode("utf-8"))
        payload["index_version"] = f"{original.index_version}-replacement-probe"
        candidate.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

        invalid_payload = dict(payload)
        invalid_payload["records_sha256"] = "0" * 64
        invalid.write_text(
            json.dumps(invalid_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        try:
            load_index_artifact(invalid)
        except IndexArtifactError:
            pass
        else:
            raise RuntimeError("invalid candidate unexpectedly passed validation")

        if active.read_bytes() != original_bytes:
            raise RuntimeError("invalid candidate changed the active artifact")

        # Validate before replacement, then exercise same-directory atomic rename.
        candidate_index = load_index_artifact(candidate)
        if candidate_index.index_version != f"{original.index_version}-replacement-probe":
            raise RuntimeError("candidate did not validate as expected")
        os.replace(candidate, active)
        replaced = load_index_artifact(active)
        if replaced.index_version != f"{original.index_version}-replacement-probe":
            raise RuntimeError("replacement did not activate the candidate")

        os.replace(backup, active)
        restored = load_index_artifact(active)
        if restored.index_version != original.index_version or active.read_bytes() != original_bytes:
            raise RuntimeError("rollback did not restore the original artifact")

    return {
        "invalid_candidate_rejection": "PASS",
        "same_directory_atomic_replacement": "PASS",
        "rollback": "PASS",
        "scope": "temporary directory beside packaged artifact; automatically removed",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    started = time.perf_counter()
    if not ARTIFACT_PATH.is_file():
        raise RuntimeError(f"Packaged index artifact is missing: {ARTIFACT_PATH}")

    load_started = time.perf_counter()
    artifact = load_index_artifact(ARTIFACT_PATH)
    load_validate_ms = (time.perf_counter() - load_started) * 1000
    filesystem = _filesystem_probe(ARTIFACT_PATH)
    ready_ms = (time.perf_counter() - MODULE_IMPORTED_AT) * 1000

    app.state.probe = {
        "status": "ready",
        "index_version": artifact.index_version,
        "record_count": len(artifact.records),
        "artifact_bytes": ARTIFACT_PATH.stat().st_size,
        "records_sha256": artifact.records_sha256,
        "load_validate_ms": round(load_validate_ms, 3),
        "module_import_to_ready_ms": round(ready_ms, 3),
        "worker_peak_rss_bytes": _peak_rss_bytes(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "filesystem": filesystem,
        "notice": (
            "Non-production probe only. Measurements describe this Render instance; "
            "they do not imply production index integration."
        ),
    }
    print("RENDER_INDEX_PROBE=" + json.dumps(app.state.probe, sort_keys=True))
    yield


app = FastAPI(
    title="PNG Public Services — Render Index Delivery Probe",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "png-public-services-render-index-probe", "status": "ready"}


@app.get("/health")
async def health() -> dict[str, str]:
    if not hasattr(app.state, "probe"):
        raise HTTPException(status_code=503, detail="Index probe is not ready")
    return {"status": "ok"}


@app.get("/probe")
async def probe() -> dict[str, Any]:
    if not hasattr(app.state, "probe"):
        raise HTTPException(status_code=503, detail="Index probe is not ready")
    return app.state.probe
