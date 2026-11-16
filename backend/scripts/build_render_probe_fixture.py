"""Build a deterministic synthetic index fixture for isolated Render delivery tests.

This fixture contains no government or user data and is never used by production.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.index_artifact import build_index_artifact, document_id_for_url, source_id_for_url
from app.source_registry import SOURCES

TARGET_BYTES = 91_106
RECORD_COUNT = 163
INDEX_VERSION = "render-probe-fixture-v1"
GENERATED_AT = "2026-11-16T00:00:00+00:00"
SOURCE_URLS = (
    "https://pngcir.gov.pg/",
    "https://pngcir.gov.pg/nid-registration-information/",
    "https://pngcir.gov.pg/png-civil-identity-registry-fees/",
    "https://pngcir.gov.pg/contact/",
)


def build_fixture() -> bytes:
    approved = {source.url: source for source in SOURCES}
    records = []
    for index in range(RECORD_COUNT):
        source_url = SOURCE_URLS[index % len(SOURCE_URLS)]
        source = approved[source_url]
        text = (
            f"SYNTHETIC TEST DATA ONLY. Render index delivery probe passage {index + 1}. "
            + ("x" * 100)
        )
        records.append({
            "source_id": source_id_for_url(source_url),
            "document_id": document_id_for_url(source_url),
            "passage_id": f"render_probe_{index + 1:04d}",
            "source_url": source_url,
            "institution": source.institution,
            "title": "Synthetic Render Delivery Probe Fixture",
            "section_path": ["Synthetic fixture", f"Group {index % 4 + 1}"],
            "position": index // len(SOURCE_URLS),
            "text": text,
            "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })

    payload = build_index_artifact(
        records, index_version=INDEX_VERSION, generated_at=GENERATED_AT
    )
    if len(payload) > TARGET_BYTES:
        raise RuntimeError(
            f"Base fixture exceeds target: {len(payload)} > {TARGET_BYTES} bytes"
        )
    padding = TARGET_BYTES - len(payload)
    if padding:
        records[0]["text"] += "x" * padding
        records[0]["content_hash"] = hashlib.sha256(
            records[0]["text"].encode("utf-8")
        ).hexdigest()
        payload = build_index_artifact(
            records, index_version=INDEX_VERSION, generated_at=GENERATED_AT
        )
    if len(payload) != TARGET_BYTES:
        raise RuntimeError(f"Fixture size mismatch: {len(payload)} bytes")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = build_fixture()
    args.output.write_bytes(payload)
    print(f"FIXTURE_BYTES={len(payload)}")
    print(f"FIXTURE_RECORDS={RECORD_COUNT}")
    print("FIXTURE_CONTENT=SYNTHETIC_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
