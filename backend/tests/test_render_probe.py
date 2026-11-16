from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app import render_probe
from app.index_artifact import load_index_artifact


def test_synthetic_render_fixture_matches_profile_size(tmp_path: Path) -> None:
    output = tmp_path / "render-probe-index.json"
    script = Path(__file__).resolve().parents[1] / "scripts" / "build_render_probe_fixture.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    artifact = load_index_artifact(output)
    assert output.stat().st_size == 91_106
    assert len(artifact.records) == 163
    assert "FIXTURE_CONTENT=SYNTHETIC_ONLY" in completed.stdout
    assert all("SYNTHETIC TEST DATA ONLY" in record.text for record in artifact.records)


def test_render_probe_reports_runtime_and_rollback_metrics(
    tmp_path: Path, monkeypatch
) -> None:
    output = tmp_path / "render-probe-index.json"
    script = Path(__file__).resolve().parents[1] / "scripts" / "build_render_probe_fixture.py"
    subprocess.run(
        [sys.executable, str(script), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    monkeypatch.setattr(render_probe, "INDEX_PATH", output)

    with TestClient(render_probe.app) as client:
        assert client.get("/health").json()["status"] == "ok"
        result = client.get("/probe").json()

    assert result["record_count"] == 163
    assert result["artifact_bytes"] == 91_106
    assert result["load_validate_ms"] >= 0
    assert result["worker_peak_rss_bytes"] > 0
    assert result["invalid_candidate_rejection"] == "PASS"
    assert result["temporary_replacement"] == "PASS"
    assert result["temporary_rollback"] == "PASS"
