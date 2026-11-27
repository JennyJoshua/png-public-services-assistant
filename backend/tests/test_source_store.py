from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from app.source_store import (
    SourceStoreError,
    _database_url,
    database_source_store_enabled,
    row_to_page,
)


def sample_row(**overrides):
    row = {
        "source_id": uuid4(),
        "registered_url": "https://pngcir.gov.pg/nid-registration-information",
        "institution": "PNGCIR",
        "topic": "Online birth and NID registration, witness rules",
        "source_class": "approved_authoritative",
        "status": "active",
        "version_id": uuid4(),
        "page_title": "National Identity Registration",
        "final_url": "https://pngcir.gov.pg/nid-registration-information",
        "content_type": "text/html; charset=utf-8",
        "publication_date": date(2026, 1, 27),
        "fetched_at": datetime(2026, 11, 27, 7, 0, tzinfo=timezone.utc),
        "content_sha256": "a" * 64,
        "extracted_text": "Official source content for the National Identity Registration service.",
    }
    row.update(overrides)
    return row


def test_database_mode_defaults_to_memory_without_database_url(monkeypatch):
    monkeypatch.delenv("SUPABASE_DATABASE_URL", raising=False)
    monkeypatch.delenv("SOURCE_STORE_MODE", raising=False)
    assert database_source_store_enabled() is False


def test_database_url_configuration_enables_database_mode(monkeypatch):
    monkeypatch.setenv(
        "SUPABASE_DATABASE_URL",
        "postgresql://postgres.example:secret@pooler.example:5432/postgres",
    )
    monkeypatch.delenv("SOURCE_STORE_MODE", raising=False)
    assert database_source_store_enabled() is True
    assert _database_url().startswith("postgresql://")


def test_explicit_database_mode_without_url_fails_closed(monkeypatch):
    monkeypatch.setenv("SOURCE_STORE_MODE", "database")
    monkeypatch.delenv("SUPABASE_DATABASE_URL", raising=False)
    assert database_source_store_enabled() is True
    with pytest.raises(SourceStoreError, match="not configured"):
        _database_url()


def test_invalid_store_mode_is_rejected(monkeypatch):
    monkeypatch.setenv("SOURCE_STORE_MODE", "remote")
    with pytest.raises(SourceStoreError, match="must be either"):
        database_source_store_enabled()


def test_database_row_maps_to_existing_page_contract_and_registry_metadata():
    row = sample_row()
    page = row_to_page(row)

    assert page["institution"] == "PNGCIR"
    assert page["agency"] == "PNGCIR"
    assert page["topic"] == row["topic"]
    assert page["url"] == row["registered_url"]
    assert page["title"] == row["page_title"]
    assert page["text"] == row["extracted_text"]
    assert page["content_hash"] == "a" * 64
    assert page["publication_date"] == "2026-01-27"
    assert page["last_checked_at"] == "2026-11-27T07:00:00+00:00"
    assert page["_registry_source_class"] == "approved_authoritative"
    assert page["_registry_status"] == "active"
    assert page["_registry_source_id"] == str(row["source_id"])
    assert page["_registry_version_id"] == str(row["version_id"])


def test_row_mapping_preserves_null_publication_date():
    page = row_to_page(sample_row(publication_date=None))
    assert page["publication_date"] is None
