"""Strict schema and read-only loader for versioned PNG public-service indexes.

Artifacts are validated against the exact curated source registry. This module is
not connected to the live retrieval path; loading an artifact never changes it.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.source_registry import SOURCES

SCHEMA_VERSION = 1
_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_APPROVED_SOURCES = {source.url: source for source in SOURCES}


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
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def source_id_for_url(source_url: str) -> str:
    """Return the stable source identifier for an exact approved registry URL."""
    if source_url not in _APPROVED_SOURCES:
        raise IndexArtifactError("source_url is not present in the approved source registry")
    return "src_" + _sha256(source_url.encode("utf-8"))[:16]


def document_id_for_url(source_url: str) -> str:
    """Return the stable document identifier for a registered seed URL."""
    source_id = source_id_for_url(source_url)
    return "doc_" + _sha256((source_id + "\0" + source_url).encode("utf-8"))[:16]


def _parse_timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IndexArtifactError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise IndexArtifactError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise IndexArtifactError(f"{field} must include a timezone")
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IndexArtifactError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise IndexArtifactError(f"non-standard JSON constant is not allowed: {value}")


def _validate_record(raw: Any, position: int) -> IndexRecord:
    if not isinstance(raw, dict):
        raise IndexArtifactError(f"record {position} must be an object")
    required = {
        "source_id", "document_id", "passage_id", "source_url", "institution",
        "title", "section_path", "position", "text", "content_hash",
    }
    if set(raw) != required:
        raise IndexArtifactError(f"record {position} has missing or unexpected fields")

    for field in ("source_id", "document_id", "passage_id", "source_url",
                  "institution", "title", "text", "content_hash"):
        if not isinstance(raw[field], str) or not raw[field].strip():
            raise IndexArtifactError(f"record {position}.{field} must be a non-empty string")

    source = _APPROVED_SOURCES.get(raw["source_url"])
    if source is None:
        raise IndexArtifactError(f"record {position}.source_url is not in the approved source registry")
    parsed_url = urlparse(raw["source_url"])
    if (parsed_url.scheme != "https" or not parsed_url.hostname
            or parsed_url.username or parsed_url.password or parsed_url.fragment):
        raise IndexArtifactError(f"record {position}.source_url must be a clean HTTPS URL")
    if raw["source_id"] != source_id_for_url(raw["source_url"]):
        raise IndexArtifactError(f"record {position}.source_id does not match the approved source")
    if raw["document_id"] != document_id_for_url(raw["source_url"]):
        raise IndexArtifactError(f"record {position}.document_id does not match its source URL")
    if raw["institution"] != source.institution:
        raise IndexArtifactError(f"record {position}.institution does not match the approved source")

    section_path = raw["section_path"]
    if not isinstance(section_path, list) or any(
        not isinstance(item, str) or not item.strip() for item in section_path
    ):
        raise IndexArtifactError(f"record {position}.section_path must be a list of non-empty strings")

    record_position = raw["position"]
    if isinstance(record_position, bool) or not isinstance(record_position, int) or record_position < 0:
        raise IndexArtifactError(f"record {position}.position must be a non-negative integer")

    if not _HEX_SHA256.fullmatch(raw["content_hash"]):
        raise IndexArtifactError(f"record {position}.content_hash must be a lowercase SHA-256 digest")
    expected_hash = _sha256(raw["text"].encode("utf-8"))
    if raw["content_hash"] != expected_hash:
        raise IndexArtifactError(f"record {position}.content_hash does not match text")

    return IndexRecord(
        source_id=raw["source_id"], document_id=raw["document_id"],
        passage_id=raw["passage_id"], source_url=raw["source_url"],
        institution=raw["institution"], title=raw["title"],
        section_path=tuple(section_path), position=record_position,
        text=raw["text"], content_hash=raw["content_hash"],
    )


def _validate_record_set(records: tuple[IndexRecord, ...]) -> None:
    passage_ids: set[str] = set()
    document_positions: set[tuple[str, int]] = set()
    document_sources: dict[str, str] = {}
    for record in records:
        if record.passage_id in passage_ids:
            raise IndexArtifactError("passage_id values must be unique")
        passage_ids.add(record.passage_id)
        position_key = (record.document_id, record.position)
        if position_key in document_positions:
            raise IndexArtifactError("passage positions must be unique within each document")
        document_positions.add(position_key)
        previous_source = document_sources.setdefault(record.document_id, record.source_id)
        if previous_source != record.source_id:
            raise IndexArtifactError("a document_id cannot refer to multiple sources")


def build_index_artifact(
    records: list[dict[str, Any]], *, index_version: str, generated_at: str
) -> bytes:
    """Build deterministic UTF-8 artifact bytes from explicitly versioned records."""
    if not isinstance(index_version, str) or not index_version.strip():
        raise IndexArtifactError("index_version must be a non-empty string")
    _parse_timestamp(generated_at, "generated_at")
    if not isinstance(records, list):
        raise IndexArtifactError("records must be a list")
    validated = tuple(_validate_record(record, i) for i, record in enumerate(records))
    _validate_record_set(validated)
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "index_version": index_version,
        "generated_at": generated_at,
        "record_count": len(records),
        "records_sha256": _sha256(_canonical_json(records)),
        "records": records,
    }
    return _canonical_json(envelope) + b"\n"


def load_index_artifact(path: str | Path) -> IndexArtifact:
    """Load a validated artifact without writing to or mutating the source file."""
    try:
        raw_bytes = Path(path).read_bytes()
        payload = json.loads(
            raw_bytes.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except IndexArtifactError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise IndexArtifactError(f"could not read valid index artifact: {exc}") from exc

    if not isinstance(payload, dict):
        raise IndexArtifactError("artifact root must be an object")
    expected_fields = {
        "schema_version", "index_version", "generated_at", "record_count",
        "records_sha256", "records",
    }
    if set(payload) != expected_fields:
        raise IndexArtifactError("artifact has missing or unexpected fields")

    schema_version = payload["schema_version"]
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise IndexArtifactError("schema_version must be an integer")
    if schema_version != SCHEMA_VERSION:
        raise IndexArtifactError(f"unsupported schema_version: {schema_version!r}")
    if not isinstance(payload["index_version"], str) or not payload["index_version"].strip():
        raise IndexArtifactError("index_version must be a non-empty string")
    _parse_timestamp(payload["generated_at"], "generated_at")

    record_count = payload["record_count"]
    if isinstance(record_count, bool) or not isinstance(record_count, int) or record_count < 0:
        raise IndexArtifactError("record_count must be a non-negative integer")
    if not isinstance(payload["records"], list):
        raise IndexArtifactError("records must be a list")
    if record_count != len(payload["records"]):
        raise IndexArtifactError("record_count does not match records")

    digest = payload["records_sha256"]
    if not isinstance(digest, str) or not _HEX_SHA256.fullmatch(digest):
        raise IndexArtifactError("records_sha256 must be a lowercase SHA-256 digest")
    if digest != _sha256(_canonical_json(payload["records"])):
        raise IndexArtifactError("records_sha256 does not match records")

    records = tuple(_validate_record(item, i) for i, item in enumerate(payload["records"]))
    _validate_record_set(records)
    return IndexArtifact(
        schema_version=schema_version, index_version=payload["index_version"],
        generated_at=payload["generated_at"], records_sha256=digest, records=records,
    )
