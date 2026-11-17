"""Tests for utils/validate_lmp_data.py, the Parquet replacement for validate_lmp_pickle.py."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from legacy_fixtures import legacy_payload

from utils import lmp_store, validate_lmp_data

DAY = "2018-01-02"


def _write_day(root: Path, day: str = DAY, drop_lmp: bool = False) -> None:
    payload = legacy_payload(day)
    if drop_lmp:
        payload["bus_detail"] = payload["bus_detail"].drop(columns=["LMP"])
    out = lmp_store.day_dir(root, day)
    out.mkdir(parents=True)
    for name in lmp_store.APP_TABLES:
        payload[name].to_parquet(out / lmp_store.table_filename(name))


def test_valid_day_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_day(tmp_path)
    assert validate_lmp_data.main(["--data-root", str(tmp_path), DAY]) == 0
    assert "PASS" in capsys.readouterr().out


def test_missing_column_fails(tmp_path: Path) -> None:
    _write_day(tmp_path, drop_lmp=True)
    assert validate_lmp_data.main(["--data-root", str(tmp_path), DAY]) == 1


def test_missing_day_fails(tmp_path: Path) -> None:
    assert validate_lmp_data.main(["--data-root", str(tmp_path), DAY]) == 2


def test_all_checks_every_day(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_day(tmp_path, "2018-01-02")
    _write_day(tmp_path, "2018-01-03", drop_lmp=True)
    assert validate_lmp_data.main(["--data-root", str(tmp_path), "--all"]) == 1
    out = capsys.readouterr().out
    assert "2018-01-02" in out and "2018-01-03" in out


def test_all_with_no_days_fails(tmp_path: Path) -> None:
    assert validate_lmp_data.main(["--data-root", str(tmp_path), "--all"]) == 2


def test_grid_coverage_reported(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_day(tmp_path)
    bus_csv = tmp_path / "bus.csv"
    pd.DataFrame({"Bus Name": ["Bus A", "Bus B"], "Bus ID": [1, 2]}).to_csv(bus_csv, index=False)
    assert validate_lmp_data.main(["--data-root", str(tmp_path), "--bus-csv", str(bus_csv), DAY]) == 0
    assert "bus merge coverage: 66.7%" in capsys.readouterr().out
