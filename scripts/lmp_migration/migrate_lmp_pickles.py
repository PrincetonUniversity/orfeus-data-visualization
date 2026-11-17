"""One-time migration of the legacy LMP pickles to Parquet (issue #1).

Input:  <src>/<YYYY-MM-DD>.p.gz  dill pickles written with pandas 1.x. Most are
        bzip2 despite the .gz name; gzip is also accepted. Other files are ignored.
Output: <dst>/<YYYY-MM-DD>/<table>.parquet  one file per DataFrame (zstd level 9)
        <dst>/<YYYY-MM-DD>/manifest.json    source checksum, table shapes, scalars
        <dst>/SHA256SUMS                    checksums of every output file

Every table is read back and compared exactly with the original before a day is
published. Each day is written to a temporary directory and renamed into place,
so an interrupted run never leaves a partial day. Re-running skips days whose
source file is unchanged, and fails for days whose source file changed.

Exit codes: 0 success, 1 one or more days failed or the output budget was hit,
2 invalid arguments.
"""
from __future__ import annotations

import argparse
import bz2
import contextlib
import gzip
import hashlib
import json
import os
import shutil
import sys
import types
import warnings
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import dill  # the legacy files were written with dill
import numpy as np
import pandas as pd
import pyarrow

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.lmp_store import MANIFEST_NAME, table_filename, validate_day

SOURCE_SUFFIX = ".p.gz"
CHECKSUMS_NAME = "SHA256SUMS"
TMP_PREFIX = ".tmp-"
MANIFEST_FORMAT = 1
PARQUET_OPTIONS: dict[str, Any] = {"engine": "pyarrow", "compression": "zstd", "compression_level": 9}

LEGACY_MODULE = "pandas.core.indexes.numeric"
LEGACY_INDEX_CLASSES = ("Int64Index", "UInt64Index", "Float64Index")


class MigrationError(Exception):
    """A single day could not be migrated; other days continue."""


class BudgetExceeded(Exception):
    """Writing more output would exceed --max-output-gb; the run stops."""


@contextlib.contextmanager
def legacy_pandas_aliases() -> Iterator[None]:
    """Map the pandas 1.x index classes the pickles reference onto pd.Index, then remove the alias."""
    if LEGACY_MODULE in sys.modules:
        yield
        return
    module = types.ModuleType(LEGACY_MODULE)
    for name in LEGACY_INDEX_CLASSES:
        setattr(module, name, pd.Index)
    sys.modules[LEGACY_MODULE] = module
    try:
        yield
    finally:
        sys.modules.pop(LEGACY_MODULE, None)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decompress(raw: bytes, name: str) -> bytes:
    if raw[:3] == b"BZh":
        return bz2.decompress(raw)
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    raise MigrationError(f"{name}: not bzip2 or gzip data")


def load_legacy(raw: bytes, name: str) -> dict[str, Any]:
    data = decompress(raw, name)
    try:
        with legacy_pandas_aliases(), warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning, message=r".*numpy\.core")
            obj = dill.loads(data)
    except Exception as exc:  # unpickling can raise almost anything
        raise MigrationError(f"{name}: cannot unpickle ({type(exc).__name__}: {exc})") from exc
    if not isinstance(obj, dict):
        raise MigrationError(f"{name}: expected a dict, found {type(obj).__name__}")
    return obj


def split_payload(obj: dict[str, Any], name: str) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    tables: dict[str, pd.DataFrame] = {}
    scalars: dict[str, Any] = {}
    for key, value in obj.items():
        if not isinstance(key, str):
            raise MigrationError(f"{name}: non-string key {key!r}")
        try:
            table_filename(key)
        except ValueError as exc:
            raise MigrationError(f"{name}: {exc}") from exc
        if isinstance(value, pd.DataFrame):
            tables[key] = value
        elif isinstance(value, np.generic):
            scalars[key] = value.item()
        elif value is None or isinstance(value, (bool, int, float, str)):
            scalars[key] = value
        else:
            raise MigrationError(f"{name}: key {key!r} has unsupported type {type(value).__name__}")
    if not tables:
        raise MigrationError(f"{name}: no DataFrames found")
    return tables, scalars


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def write_day(tables: dict[str, pd.DataFrame], scalars: dict[str, Any], out: Path,
              source_name: str, source_sha: str) -> None:
    out.mkdir(parents=True)
    manifest_tables: dict[str, Any] = {}
    for key, frame in tables.items():
        path = out / table_filename(key)
        frame.to_parquet(path, **PARQUET_OPTIONS)
        back = pd.read_parquet(path)
        try:
            pd.testing.assert_frame_equal(back, frame, check_exact=True)
        except AssertionError as exc:
            raise MigrationError(f"{source_name}: table {key!r} did not round-trip exactly") from exc
        manifest_tables[key] = {"rows": int(frame.shape[0]), "columns": int(frame.shape[1]),
                                "sha256": sha256_file(path)}
    manifest = {
        "format": MANIFEST_FORMAT,
        "source_file": source_name,
        "source_sha256": source_sha,
        "tables": manifest_tables,
        "scalars": scalars,
        "written_with": {"pandas": pd.__version__, "pyarrow": pyarrow.__version__},
    }
    (out / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def migrate_one(src_file: Path, dst: Path, dry_run: bool, budget: dict[str, int]) -> str:
    name = src_file.name
    try:
        day = validate_day(name[: -len(SOURCE_SUFFIX)])
    except ValueError as exc:
        raise MigrationError(f"{name}: file name is not <YYYY-MM-DD>{SOURCE_SUFFIX}") from exc
    raw = src_file.read_bytes()
    source_sha = sha256_bytes(raw)
    final = dst / day
    if final.exists():
        try:
            recorded = json.loads((final / MANIFEST_NAME).read_text(encoding="utf-8"))["source_sha256"]
        except (OSError, ValueError, KeyError) as exc:
            raise MigrationError(f"{name}: {final} exists without a valid manifest") from exc
        if recorded != source_sha:
            raise MigrationError(f"{name}: source changed since it was migrated; remove {final} to redo it")
        return "skipped"

    tables, scalars = split_payload(load_legacy(raw, name), name)
    if dry_run:
        return "would-migrate"

    tmp = dst / f"{TMP_PREFIX}{day}"
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        write_day(tables, scalars, tmp, name, source_sha)
        size = dir_size(tmp)
        if budget["used"] + size > budget["max"]:
            raise BudgetExceeded(f"{name}: output would exceed the --max-output-gb budget "
                                 f"({(budget['used'] + size) / 1e9:.3f} GB > {budget['max'] / 1e9:.3f} GB)")
        os.rename(tmp, final)
        budget["used"] += size
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return "migrated"


def write_checksums(dst: Path) -> int:
    lines = []
    for path in sorted(dst.rglob("*")):
        rel = path.relative_to(dst)
        if not path.is_file() or rel.parts[0].startswith(TMP_PREFIX) or rel.as_posix() == CHECKSUMS_NAME:
            continue
        lines.append(f"{sha256_file(path)}  {rel.as_posix()}")
    tmp = dst / f"{CHECKSUMS_NAME}.tmp"
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, dst / CHECKSUMS_NAME)
    return len(lines)


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--src", required=True, type=Path, help="directory of legacy <date>.p.gz files")
    parser.add_argument("--dst", required=True, type=Path, help="output directory for the Parquet dataset")
    parser.add_argument("--dry-run", action="store_true", help="load and check every file, write nothing")
    parser.add_argument("--limit", type=int, default=None, help="process only the first N files (trial runs)")
    parser.add_argument("--max-output-gb", type=float, default=1.5,
                        help="stop before total output in --dst exceeds this size (default 1.5)")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0) and 2
    src: Path = args.src.resolve()
    dst: Path = args.dst.resolve()
    if not src.is_dir():
        print(f"ERROR: --src is not a directory: {src}", file=sys.stderr)
        return 2
    if dst == src or src in dst.parents:
        print("ERROR: --dst must not be inside --src", file=sys.stderr)
        return 2
    if args.limit is not None and args.limit < 1:
        print("ERROR: --limit must be at least 1", file=sys.stderr)
        return 2
    if args.max_output_gb <= 0:
        print("ERROR: --max-output-gb must be positive", file=sys.stderr)
        return 2

    sources = sorted(p for p in src.iterdir() if p.is_file() and p.name.endswith(SOURCE_SUFFIX))
    ignored = sum(1 for p in src.iterdir() if p.is_file()) - len(sources)
    if not sources:
        print(f"ERROR: no *{SOURCE_SUFFIX} files in {src}", file=sys.stderr)
        return 1
    if args.limit is not None:
        sources = sources[: args.limit]

    mode = "DRY RUN, nothing is written" if args.dry_run else "writing"
    print(f"Migrating {len(sources)} file(s) from {src} to {dst} ({mode}); ignoring {ignored} other file(s)")
    print(f"pandas {pd.__version__}, pyarrow {pyarrow.__version__}, dill {dill.__version__}")
    if not args.dry_run:
        dst.mkdir(parents=True, exist_ok=True)
    budget = {"used": dir_size(dst), "max": int(args.max_output_gb * 1e9)}

    counts: dict[str, int] = {"migrated": 0, "skipped": 0, "would-migrate": 0}
    failures: list[str] = []
    stopped = False
    for index, src_file in enumerate(sources, 1):
        try:
            status = migrate_one(src_file, dst, args.dry_run, budget)
        except MigrationError as exc:
            failures.append(str(exc))
            print(f"[{index}/{len(sources)}] FAILED {exc}", file=sys.stderr)
            continue
        except BudgetExceeded as exc:
            failures.append(str(exc))
            print(f"[{index}/{len(sources)}] STOPPED {exc}", file=sys.stderr)
            stopped = True
            break
        counts[status] += 1
        print(f"[{index}/{len(sources)}] {status} {src_file.name}")

    if not args.dry_run and dst.exists():
        print(f"Wrote {CHECKSUMS_NAME} with {write_checksums(dst)} entries")
        print(f"Output size: {dir_size(dst) / 1e9:.3f} GB")
    summary = " ".join(f"{k}={v}" for k, v in counts.items())
    print(f"Summary: {summary} failed={len(failures)}{' (stopped early)' if stopped else ''}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
