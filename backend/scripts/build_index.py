"""CLI for building a local artifact from approved PNG public-service sources."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Running a file by path places backend/scripts on sys.path, not backend.
# Add the backend package root explicitly so this CLI works from any cwd.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.index_builder import (  # noqa: E402
    IndexBuildError,
    build_representative_index,
    write_build_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local artifact from approved PNG public-service sources.")
    parser.add_argument("--index-version", required=True, help="Human-readable immutable index release ID")
    parser.add_argument("--output", default="data/public-services-index-v1.json")
    parser.add_argument("--manifest", default="data/public-services-index-v1.manifest.json")
    parser.add_argument("--min-sources", type=int, default=3, help="Minimum successful source pages required")
    args = parser.parse_args()

    if args.min_sources < 1:
        parser.error("--min-sources must be at least 1")

    try:
        artifact, manifest = asyncio.run(
            build_representative_index(index_version=args.index_version)
        )
        if manifest["indexed_source_count"] < args.min_sources:
            raise IndexBuildError(
                f"only {manifest['indexed_source_count']} source(s) indexed; "
                f"minimum required is {args.min_sources}; no outputs written"
            )
        write_build_outputs(artifact, manifest, args.output, args.manifest)
    except (IndexBuildError, OSError) as exc:
        parser.exit(1, f"Index build failed: {exc}\n")

    print(
        f"Built {manifest['record_count']} passages from "
        f"{manifest['indexed_source_count']}/{manifest['registry_source_count']} "
        f"approved source pages.\nArtifact: {args.output}\nManifest: {args.manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
