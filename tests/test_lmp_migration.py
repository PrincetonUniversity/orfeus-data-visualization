"""Tests for scripts/lmp_migration/migrate_lmp_pickles.py (issue #1)."""
from __future__ import annotations

import bz2
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import dill
import pandas as pd
import pytest
from conftest import REPO_ROOT
from legacy_fixtures import LEGACY_MODULE, write_legacy_file

SCRIPT = REPO_ROOT / "scripts" / "lmp_migration" / "migrate_lmp_pickles.py"
DAYS = ["2018-01-02", "2018-01-03"]


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migrate_lmp_pickles", SCRIPT)
    assert spec and spec.loader, f"cannot load {SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def mig() -> ModuleType:
    return _load_script()


@pytest.fixture()
def src(tmp_path: Path) -> tuple[Path, dict[str, dict]]:
    d = tmp_path / "src"
    d.mkdir()
    payloads = {}
    for i, day in enumerate(DAYS):
        _, payloads[day] = write_legacy_file(d, day, seed=i)
    (d / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1")
    return d, payloads


def _files(root: Path) -> dict[str, float]:
    return {str(p.relative_to(root)): p.stat().st_mtime_ns for p in sorted(root.rglob("*")) if p.is_file()}


def test_fixture_needs_legacy_shim(src: tuple[Path, dict]) -> None:
    # Reproduces issue #1: pandas 2.x cannot load these files without a shim.
    d, _ = src
    assert LEGACY_MODULE not in sys.modules
    raw = bz2.decompress((d / f"{DAYS[0]}.p.gz").read_bytes())
    with pytest.raises(ModuleNotFoundError, match="pandas.core.indexes.numeric"):
        dill.loads(raw)


def test_migrates_every_table_exactly(mig: ModuleType, src: tuple[Path, dict], tmp_path: Path) -> None:
    d, payloads = src
    dst = tmp_path / "dst"
    assert mig.main(["--src", str(d), "--dst", str(dst)]) == 0
    for day, payload in payloads.items():
        out = dst / day
        manifest = json.loads((out / "manifest.json").read_text())
        frames = {k: v for k, v in payload.items() if isinstance(v, pd.DataFrame)}
        assert sorted(manifest["tables"]) == sorted(frames)
        assert manifest["scalars"] == {"total_runtime": payload["total_runtime"]}
        assert manifest["source_file"] == f"{day}.p.gz"
        for name, expected in frames.items():
            got = pd.read_parquet(out / f"{name}.parquet")
            pd.testing.assert_frame_equal(got, expected, check_exact=True)
            assert manifest["tables"][name]["rows"] == len(expected)
    assert LEGACY_MODULE not in sys.modules, "legacy shim leaked into the process"


def test_writes_checksums_for_all_outputs(mig: ModuleType, src: tuple[Path, dict], tmp_path: Path) -> None:
    d, payloads = src
    dst = tmp_path / "dst"
    assert mig.main(["--src", str(d), "--dst", str(dst)]) == 0
    sums = (dst / "SHA256SUMS").read_text().splitlines()
    listed = sorted(line.split("  ", 1)[1] for line in sums)
    expected = sorted(p for p in _files(dst) if p != "SHA256SUMS")
    n_tables = sum(isinstance(v, pd.DataFrame) for v in payloads[DAYS[0]].values())
    assert listed == expected and len(listed) == len(DAYS) * (n_tables + 1)
    for line in sums:
        digest, rel = line.split("  ", 1)
        assert digest == hashlib.sha256((dst / rel).read_bytes()).hexdigest()


def test_rerun_skips_unchanged_dates(mig: ModuleType, src: tuple[Path, dict], tmp_path: Path,
                                     capsys: pytest.CaptureFixture[str]) -> None:
    d, _ = src
    dst = tmp_path / "dst"
    assert mig.main(["--src", str(d), "--dst", str(dst)]) == 0
    before = {k: v for k, v in _files(dst).items() if k != "SHA256SUMS"}
    capsys.readouterr()
    assert mig.main(["--src", str(d), "--dst", str(dst)]) == 0
    after = {k: v for k, v in _files(dst).items() if k != "SHA256SUMS"}
    assert after == before
    assert "skipped=2" in capsys.readouterr().out


def test_changed_source_is_an_error(mig: ModuleType, src: tuple[Path, dict], tmp_path: Path) -> None:
    d, _ = src
    dst = tmp_path / "dst"
    assert mig.main(["--src", str(d), "--dst", str(dst)]) == 0
    write_legacy_file(d, DAYS[0], seed=99)
    assert mig.main(["--src", str(d), "--dst", str(dst)]) == 1


def test_dry_run_reads_everything_writes_nothing(mig: ModuleType, src: tuple[Path, dict], tmp_path: Path,
                                                 capsys: pytest.CaptureFixture[str]) -> None:
    d, _ = src
    dst = tmp_path / "dst"
    assert mig.main(["--src", str(d), "--dst", str(dst), "--dry-run"]) == 0
    assert not dst.exists()
    assert "would-migrate=2" in capsys.readouterr().out


def test_output_budget_stops_run_and_cleans_up(mig: ModuleType, src: tuple[Path, dict], tmp_path: Path) -> None:
    d, _ = src
    dst = tmp_path / "dst"
    assert mig.main(["--src", str(d), "--dst", str(dst), "--max-output-gb", "0.000001"]) == 1
    leftovers = [p.name for p in dst.iterdir()] if dst.exists() else []
    assert not [n for n in leftovers if n.startswith(".tmp-") or n in DAYS]


def test_limit_processes_first_n(mig: ModuleType, src: tuple[Path, dict], tmp_path: Path) -> None:
    d, _ = src
    dst = tmp_path / "dst"
    assert mig.main(["--src", str(d), "--dst", str(dst), "--limit", "1"]) == 0
    assert (dst / DAYS[0]).is_dir() and not (dst / DAYS[1]).exists()


def test_corrupt_file_fails_but_others_migrate(mig: ModuleType, src: tuple[Path, dict], tmp_path: Path) -> None:
    d, _ = src
    (d / "2018-01-04.p.gz").write_bytes(b"not a pickle")
    dst = tmp_path / "dst"
    assert mig.main(["--src", str(d), "--dst", str(dst)]) == 1
    assert all((dst / day / "manifest.json").exists() for day in DAYS)
    assert not (dst / "2018-01-04").exists()


def test_unsupported_value_type_fails(mig: ModuleType, tmp_path: Path) -> None:
    d = tmp_path / "src"
    d.mkdir()
    (d / "2018-01-02.p.gz").write_bytes(bz2.compress(dill.dumps({"bus_detail": [1, 2, 3]})))
    assert mig.main(["--src", str(d), "--dst", str(tmp_path / "dst")]) == 1


@pytest.mark.parametrize("name", ["2018-01-02.backup.p.gz", "2018-13-40.p.gz", "latest.p.gz"])
def test_rejects_files_not_named_by_date(mig: ModuleType, tmp_path: Path, name: str) -> None:
    d = tmp_path / "src"
    d.mkdir()
    write_legacy_file(d, "2018-01-02")
    (d / "2018-01-02.p.gz").rename(d / name)
    assert mig.main(["--src", str(d), "--dst", str(tmp_path / "dst")]) == 1


def test_empty_source_is_an_error(mig: ModuleType, tmp_path: Path) -> None:
    d = tmp_path / "src"
    d.mkdir()
    assert mig.main(["--src", str(d), "--dst", str(tmp_path / "dst")]) == 1


def test_missing_source_is_an_error(mig: ModuleType, tmp_path: Path) -> None:
    assert mig.main(["--src", str(tmp_path / "nope"), "--dst", str(tmp_path / "dst")]) == 2
