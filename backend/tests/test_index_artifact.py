import hashlib
import json
from pathlib import Path

import pytest

from app.index_artifact import (
    IndexArtifactError,
    build_index_artifact,
    load_index_artifact,
)


def sample_records():
    text = "Applicants must lodge the completed form at the registry office."
    return [{
        "source_id": "source-test-001",
        "document_id": "document-test-001",
        "passage_id": "passage-test-001",
        "source_url": "https://example.gov.pg/registration",
        "institution": "Example Public Agency (synthetic test fixture)",
        "title": "Registration guidance (synthetic test fixture)",
        "section_path": ["How to apply", "Lodgement"],
        "position": 0,
        "text": text,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }]


def test_artifact_build_is_deterministic_for_identical_inputs():
    first = build_index_artifact(sample_records(), index_version="fixture-1", generated_at="2026-11-15T00:00:00Z")
    second = build_index_artifact(sample_records(), index_version="fixture-1", generated_at="2026-11-15T00:00:00Z")
    assert first == second


def test_artifact_loads_records_as_immutable_tuples(tmp_path):
    path = tmp_path / "index.json"
    path.write_bytes(build_index_artifact(sample_records(), index_version="fixture-1", generated_at="2026-11-15T00:00:00Z"))
    before = path.read_bytes()
    artifact = load_index_artifact(path)
    assert artifact.index_version == "fixture-1"
    assert artifact.records[0].passage_id == "passage-test-001"
    assert artifact.records[0].section_path == ("How to apply", "Lodgement")
    assert path.read_bytes() == before
    with pytest.raises((AttributeError, TypeError)):
        artifact.records[0].text = "mutated"


def test_loader_rejects_unknown_schema_version(tmp_path):
    path = tmp_path / "index.json"
    payload = json.loads(build_index_artifact(sample_records(), index_version="fixture-1", generated_at="2026-11-15T00:00:00Z"))
    payload["schema_version"] = 999
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IndexArtifactError, match="unsupported schema_version"):
        load_index_artifact(path)


def test_loader_rejects_corrupt_record_digest(tmp_path):
    path = tmp_path / "index.json"
    payload = json.loads(build_index_artifact(sample_records(), index_version="fixture-1", generated_at="2026-11-15T00:00:00Z"))
    payload["records"][0]["text"] = "tampered text"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IndexArtifactError, match="records_sha256"):
        load_index_artifact(path)


def test_builder_rejects_duplicate_passage_ids():
    records = sample_records() * 2
    with pytest.raises(IndexArtifactError, match="passage_id values must be unique"):
        build_index_artifact(records, index_version="fixture-1", generated_at="2026-11-15T00:00:00Z")


def test_builder_rejects_non_https_source_url():
    records = sample_records()
    records[0]["source_url"] = "http://example.gov.pg/registration"
    with pytest.raises(IndexArtifactError, match="HTTPS URL"):
        build_index_artifact(records, index_version="fixture-1", generated_at="2026-11-15T00:00:00Z")


def test_packaged_fixture_loads_from_backend_data_directory():
    fixture = Path(__file__).parents[1] / "data" / "index" / "fixture-v1.json"
    artifact = load_index_artifact(fixture)
    assert artifact.index_version == "fixture-1"
    assert len(artifact.records) == 1
    assert "Synthetic fixture only" in artifact.records[0].text
