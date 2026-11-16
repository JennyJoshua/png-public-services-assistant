"""Isolated Render runtime probe for versioned index loading and rollback.

This module is used only by the dedicated non-production Render test service.
It does not connect the index to the public-services chat retrieval path.
"""
from __future__ import annotations

import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.index_artifact import IndexArtifactError, load_index_artifact

INDEX_PATH = Path(__file__).resolve().parents[1] / "data" / "render-probe-index.json"


def profile_index(artifact_path: Path) -> dict:
    started = time.perf_counter()
    artifact = load_index_artifact(artifact_path)
    load_validate_ms = (time.perf_counter() - started) * 1000

    import resource
    peak_rss_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)

    original_bytes = artifact_path.read_bytes()
    replacement_passed = False
    rollback_passed = False
    invalid_rejected = False

    with tempfile.TemporaryDirectory(prefix="render-index-probe-") as temp_dir:
        root = Path(temp_dir)
        active = root / "active-index.json"
        backup = root / "backup-index.json"
        candidate = root / "candidate-index.json"
        invalid = root / "invalid-index.json"

        active.write_bytes(original_bytes)
        backup.write_bytes(original_bytes)

        candidate_bytes = original_bytes.replace(
            b'"index_version":"render-probe-fixture-v1"',
            b'"index_version":"render-probe-fixture-v1-replacement"',
            1,
        )
        if candidate_bytes == original_bytes:
            raise RuntimeError("Could not prepare replacement candidate")
        candidate.write_bytes(candidate_bytes)

        invalid_bytes = candidate_bytes.replace(
            b'"records_sha256":"', b'"records_sha256":"0000', 1
        )
        invalid.write_bytes(invalid_bytes)
        try:
            load_index_artifact(invalid)
        except IndexArtifactError:
            invalid_rejected = True
        if not invalid_rejected:
            raise RuntimeError("Invalid candidate unexpectedly passed validation")
        if active.read_bytes() != original_bytes:
            raise RuntimeError("Invalid candidate modified the active index")

        load_index_artifact(candidate)
        os.replace(candidate, active)
        replacement_passed = (
            load_index_artifact(active).index_version
            == "render-probe-fixture-v1-replacement"
        )
        if not replacement_passed:
            raise RuntimeError("Validated replacement did not become active")

        os.replace(backup, active)
        restored = load_index_artifact(active)
        rollback_passed = (
            restored.index_version == artifact.index_version
            and active.read_bytes() == original_bytes
        )
        if not rollback_passed:
            raise RuntimeError("Rollback did not restore the original index")

    return {
        "index_version": artifact.index_version,
        "record_count": len(artifact.records),
        "artifact_bytes": artifact_path.stat().st_size,
        "load_validate_ms": round(load_validate_ms, 3),
        "worker_peak_rss_bytes": peak_rss_bytes,
        "invalid_candidate_rejection": "PASS" if invalid_rejected else "FAIL",
        "temporary_replacement": "PASS" if replacement_passed else "FAIL",
        "temporary_rollback": "PASS" if rollback_passed else "FAIL",
        "filesystem_scope": "temporary directory within this Render instance",
        "data_classification": "synthetic test fixture; no source passage content",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    started = time.perf_counter()
    if not INDEX_PATH.is_file():
        raise RuntimeError(f"Required test index is missing: {INDEX_PATH}")
    app.state.probe = profile_index(INDEX_PATH)
    app.state.startup_total_ms = round((time.perf_counter() - started) * 1000, 3)
    yield


app = FastAPI(
    title="PNG Public Services — Render Index Delivery Probe",
    version="0.1.0",
    description="Non-production synthetic index delivery and runtime measurement endpoint.",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    if not hasattr(app.state, "probe"):
        raise HTTPException(status_code=503, detail="Probe has not completed startup")
    return {"status": "ok", "service": "render-index-delivery-probe"}


@app.get("/probe")
async def probe() -> dict:
    if not hasattr(app.state, "probe"):
        raise HTTPException(status_code=503, detail="Probe has not completed startup")
    return {**app.state.probe, "startup_profile_ms": app.state.startup_total_ms}
