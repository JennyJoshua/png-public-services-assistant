import hashlib

import pytest

from app.index_artifact import (
    IndexArtifactError,
    build_index_artifact,
    document_id_for_url,
    load_index_artifact,
    source_id_for_url,
)
from app.source_registry import SOURCES
from scripts.profile_index_artifact import simulate_replace_and_rollback


def synthetic_artifact(tmp_path):
    source = SOURCES[0]
    text = "Synthetic CI fixture only; this is not copied from an official source."
    record = {
        "source_id": source_id_for_url(source.url),
        "document_id": document_id_for_url(source.url),
        "passage_id": "probe-passage-001",
        "source_url": source.url,
        "institution": source.institution,
        "title": "Synthetic delivery probe",
        "section_path": ["Synthetic fixture"],
        "position": 0,
        "text": text,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    path = tmp_path / "synthetic-index.json"
    path.write_bytes(build_index_artifact(
        [record],
        index_version="synthetic-probe-v1",
        generated_at="2026-11-15T00:00:00Z",
    ))
    return path


def test_loader_reports_missing_artifact_as_controlled_error(tmp_path):
    with pytest.raises(IndexArtifactError, match="could not read valid index artifact"):
        load_index_artifact(tmp_path / "missing-index.json")


def test_temporary_replacement_rejects_corrupt_candidate_and_rolls_back(tmp_path):
    artifact_path = synthetic_artifact(tmp_path)
    result = simulate_replace_and_rollback(artifact_path)

    assert result == {
        "invalid_candidate_rejected": "PASS",
        "replacement": "PASS",
        "rollback": "PASS",
        "scope": "temporary directory on GitHub Actions runner only",
    }
    assert load_index_artifact(artifact_path).index_version == "synthetic-probe-v1"
