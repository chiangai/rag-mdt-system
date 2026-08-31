from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable


SOURCE_ENV = "HERCARE_KG_SOURCE_DIR"


def resolve_source_dir(value: str | None = None) -> Path:
    """Resolve the read-only KG asset root and reject ambiguous relative paths."""
    raw = value if value is not None else os.getenv(SOURCE_ENV)
    if not raw:
        raise ValueError(f"{SOURCE_ENV} must point to an absolute source directory")
    source_dir = Path(raw)
    if not source_dir.is_absolute():
        raise ValueError(f"{SOURCE_ENV} must be absolute: {raw!r}")
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise ValueError(f"{SOURCE_ENV} is not a directory: {source_dir}")
    return source_dir


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def discover_assets(source_dir: Path) -> list[Path]:
    return sorted(path for path in source_dir.glob("global_kg*.json") if path.is_file())


def build_manifest(source_dir: Path, assets: Iterable[Path]) -> dict:
    source_dir = source_dir.resolve()
    files: list[dict[str, str | int]] = []
    for raw_path in sorted((Path(item).resolve() for item in assets), key=lambda item: str(item)):
        try:
            relative = raw_path.relative_to(source_dir)
        except ValueError as exc:
            raise ValueError(f"asset is outside {SOURCE_ENV}: {raw_path}") from exc
        if not raw_path.is_file():
            raise ValueError(f"asset is not a file: {raw_path}")
        files.append(
            {
                "relative_path": relative.as_posix(),
                "size_bytes": raw_path.stat().st_size,
                "sha256": sha256_file(raw_path),
            }
        )
    return {"schema_version": "1", "source_dir": str(source_dir), "files": files}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit read-only HerCare KG source assets")
    parser.add_argument("--source-dir", help=f"absolute path; defaults to {SOURCE_ENV}")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_dir = resolve_source_dir(args.source_dir)
    manifest = build_manifest(source_dir, discover_assets(source_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
