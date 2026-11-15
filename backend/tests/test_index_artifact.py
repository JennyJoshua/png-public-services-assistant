import hashlib
import json

import pytest

from app.index_artifact import (
    IndexArtifactError,
    build_index_artifact,
    document_id_for_url,
    load_index_artifact,
    source_id_for_url,
)
from app.source_registry import SOURCES


def sample_records():
    source = SOURCES[0]
    text = "Synthetic fixture only: applicants lodge a completed form at the registry office."
    return [{
        "source_id": source_id_for_url(source.url),
        "document_id": document_id_for_url(source.url),
        "passage_id": "passage-fixture-001",
        "source_url": source.url,
        "institution": source.institution,
        "title": "Synthetic test fixture — not source content",
        "section_path": ["Synthetic example", "Lodgement"],
        "position": 0,
        "text": text,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }]


GENERATED_AT = "2026-11-15T00:00:00Z"


def write_artifact(tmp_path, payload):
    path = tmp_path / "index.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_artifact_build_is_deterministic_for_identical_inputs():
    first = build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT)
    second = build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT)
    assert first == second


def test_artifact_loads_records_as_immutable_tuples(tmp_path):
    path = tmp_path / "index.json"
    path.write_bytes(build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT))
    before = path.read_bytes()
    artifact = load_index_artifact(path)
    assert artifact.index_version == "fixture-1"
    assert artifact.records[0].passage_id == "passage-fixture-001"
    assert artifact.records[0].section_path == ("Synthetic example", "Lodgement")
    assert path.read_bytes() == before
    with pytest.raises((AttributeError, TypeError)):
        artifact.records[0].text = "mutated"


def test_loader_rejects_unknown_schema_version(tmp_path):
    payload = json.loads(build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT))
    payload["schema_version"] = 999
    path = write_artifact(tmp_path, payload)
    with pytest.raises(IndexArtifactError, match="unsupported schema_version"):
        load_index_artifact(path)


@pytest.mark.parametrize("invalid", [True, 1.0, "1", None])
def test_loader_rejects_non_integer_schema_version(tmp_path, invalid):
    payload = json.loads(build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT))
    payload["schema_version"] = invalid
    with pytest.raises(IndexArtifactError, match="schema_version must be an integer"):
        load_index_artifact(write_artifact(tmp_path, payload))


@pytest.mark.parametrize("invalid", [True, 1.0, "1", -1])
def test_loader_rejects_invalid_record_count(tmp_path, invalid):
    payload = json.loads(build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT))
    payload["record_count"] = invalid
    with pytest.raises(IndexArtifactError, match="record_count"):
        load_index_artifact(write_artifact(tmp_path, payload))


def test_loader_rejects_corrupt_record_digest(tmp_path):
    payload = json.loads(build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT))
    payload["records"][0]["text"] = "tampered text"
    path = write_artifact(tmp_path, payload)
    with pytest.raises(IndexArtifactError, match="records_sha256"):
        load_index_artifact(path)


def test_builder_rejects_duplicate_passage_ids():
    records = sample_records() * 2
    with pytest.raises(IndexArtifactError, match="passage_id values must be unique"):
        build_index_artifact(records, index_version="fixture-1", generated_at=GENERATED_AT)


def test_builder_rejects_duplicate_document_positions():
    records = sample_records()
    duplicate = dict(records[0], passage_id="passage-fixture-002")
    records.append(duplicate)
    with pytest.raises(IndexArtifactError, match="positions must be unique"):
        build_index_artifact(records, index_version="fixture-1", generated_at=GENERATED_AT)


def test_builder_rejects_unapproved_source_url():
    records = sample_records()
    records[0]["source_url"] = "https://example.gov.pg/registration"
    with pytest.raises(IndexArtifactError, match="approved source registry"):
        build_index_artifact(records, index_version="fixture-1", generated_at=GENERATED_AT)


def test_builder_rejects_mismatched_source_identity():
    records = sample_records()
    records[0]["source_id"] = "src_wrong"
    with pytest.raises(IndexArtifactError, match="source_id"):
        build_index_artifact(records, index_version="fixture-1", generated_at=GENERATED_AT)


@pytest.mark.parametrize("timestamp", ["", "not-a-date", "2026-11-15T00:00:00", "2026-11-15"])
def test_builder_rejects_invalid_or_timezone_naive_timestamp(timestamp):
    with pytest.raises(IndexArtifactError, match="generated_at"):
        build_index_artifact(sample_records(), index_version="fixture-1", generated_at=timestamp)


def test_loader_rejects_duplicate_json_keys(tmp_path):
    valid = build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT).decode()
    duplicate = valid.replace('"schema_version":1', '"schema_version":1,"schema_version":1', 1)
    path = tmp_path / "duplicate.json"
    path.write_text(duplicate, encoding="utf-8")
    with pytest.raises(IndexArtifactError, match="duplicate JSON object key"):
        load_index_artifact(path)


def test_loader_rejects_non_standard_json_constants(tmp_path):
    path = tmp_path / "nan.json"
    path.write_text('{"schema_version":NaN}', encoding="utf-8")
    with pytest.raises(IndexArtifactError, match="non-standard JSON constant"):
        load_index_artifact(path)


def test_loader_rejects_non_string_source_url_without_leaking_type_error(tmp_path):
    payload = json.loads(build_index_artifact(sample_records(), index_version="fixture-1", generated_at=GENERATED_AT))
    payload["records"][0]["source_url"] = 42
    from app.index_artifact import _canonical_json, _sha256
    payload["records_sha256"] = _sha256(_canonical_json(payload["records"]))
    with pytest.raises(IndexArtifactError, match="source_url"):
        load_index_artifact(write_artifact(tmp_path, payload))
