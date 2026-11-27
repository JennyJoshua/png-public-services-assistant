import asyncio

from app import source_content
from app.source_store import SourceStoreError


def test_database_mode_reads_durable_pages_instead_of_memory_cache(monkeypatch):
    expected = [{
        "institution": "PNGCIR",
        "topic": "Online birth and NID registration, witness rules",
        "url": "https://pngcir.gov.pg/nid-registration-information",
        "_registry_status": "active",
    }]
    monkeypatch.setattr(source_content, "database_source_store_enabled", lambda: True)
    monkeypatch.setattr(source_content, "fetch_active_source_pages", lambda: _async_value(expected))
    monkeypatch.setitem(source_content._CACHE, "https://memory.example/page", {"text": "stale"})

    pages = asyncio.run(source_content.get_source_pages())

    assert pages == expected
    assert pages != list(source_content._CACHE.values())


def test_database_outage_returns_no_pages_and_never_falls_back_to_memory(monkeypatch):
    async def fail():
        raise SourceStoreError("database unavailable")

    monkeypatch.setattr(source_content, "database_source_store_enabled", lambda: True)
    monkeypatch.setattr(source_content, "fetch_active_source_pages", fail)
    monkeypatch.setitem(source_content._CACHE, "https://memory.example/page", {"text": "stale"})

    pages = asyncio.run(source_content.get_source_pages())

    assert pages == []


def test_invalid_database_mode_returns_no_pages(monkeypatch):
    def invalid():
        raise SourceStoreError("invalid mode")

    monkeypatch.setattr(source_content, "database_source_store_enabled", invalid)
    monkeypatch.setitem(source_content._CACHE, "https://memory.example/page", {"text": "stale"})

    pages = asyncio.run(source_content.get_source_pages())

    assert pages == []


def _async_value(value):
    async def inner():
        return value
    return inner()
