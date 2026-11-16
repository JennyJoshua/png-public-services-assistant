""""Validation and read-only loading for packaged, versioned RAG index artifacts.

This module is deliberately not wired into the live retrieval path yet. It is a
small Batch 0 prototype for validating the deployment-artifact contract.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = 1


class IndexArtifactError(ValueError):
    """Raised when a packaged index is invalid or unsupported."""


@dataclass(frozen=True)
class IndexRecord:
    source_id: str
    document_id: str
    passage_id: str
    source_url: str
    institution: str
    title: str
    section_path: tuple[str, ...]
    position: int
    text: str
    content_hash: str


@dataclass(frozen=True)
class IndexArtifact:
    schema_version: int
    index_version: str
    generated_at: str
    records_sha256: str
    records: tuple[IndexRecord, ...]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_record(raw: Any, position: int) -> IndexRecord:
    if not isinstance(raw, dict):
        raise IndexArtifactError(f"record {position} must be an object")
    required = {
        "source_id", "document_id", "passage_id", "source_url", "institution",
        "title", "section_path", "position", "text", "content_hash",
    }
    if set(raw) != required:
        raise IndexArtifactError(f"record {position} has missing or unexpected fields")
    for field in (
        "source_id", "document_id", "passage_id", "institution", "title",
        "text", "content_hash",
    ):
        if not isinstance(raw[field], str) or not raw[field].strip():
            raise IndexArtifactError(
                f"record {position}.{field} must be a non-empty string"
            )
    parsed_url = urlparse(raw["source_url"])
    if (
        parsed_url.scheme != "https"
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
    ):
        raise IndexArtifactError(
            f"record {position}.source_url must be an HTTPS URL"
        )
    section_path = raw["section_path"]
    if not isinstance(section_path, list) or any(
        not isinstance(item, str) or not item.strip() for item in section_path
    ):
        raise IndexArtifactError(
            f"record {position}.section_path must be a list of non-empty strings"
        )
    record_position = raw["position"]
    if (
        isinstance(record_position, bool)
        or not isinstance(record_position, int)
        or record_position < 0
    ):
        raise IndexArtifactError(
            f"record {position}.position must be a non-negative integer"
        )
    expected_hash = _sha256(raw["text"].encode("utf-8"))
    if raw["content_hash"] != expected_hash:
        raise IndexArtifactError(
            f"record {position}.content_hash does not match text"
        )
    return IndexRecord(
        source_id=raw["source_id"],
        document_id=raw["document_id"],
        passage_id=raw["passage_id"],
        source_url=raw["source_url"],
        institution=raw["institution"],
        title=raw["title"],
        section_path=tuple(section_path),
        position=record_position,
        text=raw["text"],
        content_hash=raw["content_hash"],
    )


def build_index_artifact(
    records: list[dict[str, Any]], *, index_version: str, generated_at: str
) -> bytes:
    """Build deterministic UTF-8 artifact bytes from explicit, versioned inputs."""
    if not isinstance(index_version, str) or not index_version.strip():
        raise IndexArtifactError("index_version must be a non-empty string")
    if not isinstance(generated_at, str) or not generated_at.strip():
        raise IndexArtifactError("generated_at must be a non-empty string")
    validated = [_validate_record(record, i) for i, record in enumerate(records)]
    if len({item.passage_id for item in validated}) != len(validated):
        raise IndexArtifactError("passage_id values must be unique")
    canonical_records = _canonical_json(records)
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "index_version": index_version,
        "generated_at": generated_at,
        "record_count": len(records),
        "records_sha256": _sha256(canonical_records),
        "records": records,
    }
    return _canonical_json(envelope) + b"\\n"


def load_index_artifact(path: str | Path) -> IndexArtifact:
    """Load and validate a packaged artifact using read-only file access."""
    artifact_path = Path(path)
    try:
        raw_bytes = artifact_path.read_bytes()
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IndexArtifactError(
            f"could not read valid index artifact: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise IndexArtifactError("artifact root must be an object")
    expected_fields = {
        "schema_version", "index_version", "generated_at", "record_count",
        "records_sha256", "records",
    }
    if set(payload) != expected_fields:
        raise IndexArtifactError("artifact has missing or unexpected fields")
    schema_version = payload["schema_version"]
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != SCHEMA_VERSION
    ):
        raise IndexArtifactError(
            f"unsupported schema_version: {schema_version!r}"
        )
    if not isinstance(payload["index_version"], str) or not payload["index_version"].strip():
        raise IndexArtifactError("index_version must be a non-empty string")
    if not isinstance(payload["generated_at"], str) or not payload["generated_at"].strip():
        raise IndexArtifactError("generated_at must be a non-empty string")
    if not isinstance(payload["records"], list):
        raise IndexArtifactError("records must be a list")
    record_count = payload["record_count"]
    if isinstance(record_count, bool) or not isinstance(record_count, int) or record_count < 0:
        raise IndexArtifactError("record_count must be a non-negative integer")
    if record_count != len(payload["records"]):
        raise IndexArtifactError("record_count does not match records")
    records_bytes = _canonical_json(payload["records"])
    if payload["records_sha256"] != _sha256(records_bytes):
        raise IndexArtifactError("records_sha256 does not match records")
    records = tuple(
        _validate_record(item, i) for i, item in enumerate(payload["records"])
    )
    if len({item.passage_id for item in records}) != len(records):
        raise IndexArtifactError("passage_id values must be unique")
    return IndexArtifact(
        schema_version=SCHEMA_VERSION,
        index_version=payload["index_version"],
        generated_at=payload["generated_at"],
        records_sha256=payload["records_sha256"],
        records=records,
    )
