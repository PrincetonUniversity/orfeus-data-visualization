"""Tests for utils/lmp_store.py, the app's LMP Parquet reader (issue #1)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from legacy_fixtures import legacy_payload

from utils import lmp_store

DAY = "2018-01-02"


def _write_day(data_root: Path, day: str) -> dict:
    payload = legacy_payload(day)
    out = lmp_store.parquet_dataset_dir(data_root) / day
    out.mkdir(parents=True)
    for name in lmp_store.APP_TABLES:
        payload[name].to_parquet(out / f"{name}.parquet")
    return payload


def test_layout_matches_documented_path(tmp_path: Path) -> None:
    assert lmp_store.day_dir(tmp_path, DAY) == (
        tmp_path / "lmps_data_visualization" / "t7k_v0.4.0-a2_rsvf-20-parquet" / DAY
    )


def test_load_bus_line_returns_flat_frames(tmp_path: Path) -> None:
    payload = _write_day(tmp_path, DAY)
    bus, line = lmp_store.load_bus_line(tmp_path, DAY)
    pd.testing.assert_frame_equal(bus, payload["bus_detail"].reset_index())
    pd.testing.assert_frame_equal(line, payload["line_detail"].reset_index())
    assert {"Date", "Hour", "Bus", "LMP", "Demand"} <= set(bus.columns)
    assert {"Hour", "Line", "Flow"} <= set(line.columns)


def test_missing_day_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        lmp_store.load_bus_line(tmp_path, DAY)


@pytest.mark.parametrize("bad", ["../../etc/passwd", "2018-02-30", "2018-1-2", "", "2018-01-02/..", None, 20180102])
def test_rejects_invalid_day(tmp_path: Path, bad: object) -> None:
    with pytest.raises(ValueError):
        lmp_store.load_bus_line(tmp_path, bad)  # type: ignore[arg-type]
