"""The LMP page reads Parquet via utils.lmp_store and no longer unpickles files (issue #1)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest
from conftest import REPO_ROOT
from legacy_fixtures import legacy_payload

from utils import lmp_store

DAY = "2018-01-02"
LMPS_SOURCE = REPO_ROOT / "pages" / "data_visualization" / "lmps.py"


@pytest.fixture(scope="module")
def lmps() -> ModuleType:
    os.environ.setdefault("STUB_MODE", "1")
    import app  # noqa: F401  (registers the Dash pages, including the LMP page)

    # Dash loads pages by module name without importing their parent packages.
    return sys.modules["pages.data_visualization.lmps"]


def _write_day(data_root: Path) -> dict:
    payload = legacy_payload(DAY)
    out = lmp_store.day_dir(data_root, DAY)
    out.mkdir(parents=True)
    for name in lmp_store.APP_TABLES:
        payload[name].to_parquet(out / lmp_store.table_filename(name))
    return payload


def test_page_reads_lmps_from_parquet(lmps: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _write_day(tmp_path)
    monkeypatch.setattr(lmps, "LMP_DATA_ROOT", tmp_path)
    bus_detail, line_detail = lmps.build_lmp_plot_file(DAY, bus=pd.DataFrame(), branch=pd.DataFrame())
    expected_bus = payload["bus_detail"].reset_index()
    expected_line = payload["line_detail"].reset_index()
    pd.testing.assert_series_equal(bus_detail["LMP"], expected_bus["LMP"])
    pd.testing.assert_series_equal(line_detail["Flow"], expected_line["Flow"])


@pytest.mark.parametrize("day", ["2018-01-03", "../../../etc/passwd", "2018-02-30", ""])
def test_missing_or_invalid_day_falls_back_to_stub(lmps: ModuleType, tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch, day: str) -> None:
    _write_day(tmp_path)
    monkeypatch.setattr(lmps, "LMP_DATA_ROOT", tmp_path)
    bus_detail, line_detail = lmps.build_lmp_plot_file(day, bus=pd.DataFrame(), branch=pd.DataFrame())
    assert (bus_detail["LMP"] == 0.0).all() and len(bus_detail) == 24
    assert (line_detail["Flow"] == 0.0).all()


def test_legacy_pickle_code_removed() -> None:
    source = LMPS_SOURCE.read_text(encoding="utf-8")
    for needle in ("import pickle", "import bz2", "import gzip", "dill", "_prepare_pandas_compat", ".p.gz"):
        assert needle not in source, f"lmps.py still contains {needle!r}"
    assert not (REPO_ROOT / "utils" / "validate_lmp_pickle.py").exists()


def test_app_does_not_depend_on_dill() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "dill" not in requirements
    assert "pyarrow" in requirements
