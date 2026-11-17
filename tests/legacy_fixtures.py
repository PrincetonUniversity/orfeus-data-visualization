"""Build synthetic LMP files shaped like the real legacy pickles on TigerData.

The real files (see issue #1) are bzip2-compressed dill pickles named *.p.gz,
written with pandas 1.x. They hold a dict of MultiIndexed DataFrames plus a
float, and reference pandas.core.indexes.numeric.Int64Index, which pandas 2.x
removed. This module reproduces those properties without the real data.
"""
from __future__ import annotations

import bz2
import contextlib
import sys
import types
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dill
import numpy as np
import pandas as pd

LEGACY_MODULE = "pandas.core.indexes.numeric"


@contextlib.contextmanager
def _fake_legacy_index_module() -> Iterator[type]:
    """Temporarily provide Int64Index so a pickle records the legacy class path."""
    module = types.ModuleType(LEGACY_MODULE)

    class Int64Index(pd.Index):  # type: ignore[misc]
        pass

    Int64Index.__module__ = LEGACY_MODULE
    Int64Index.__qualname__ = "Int64Index"
    module.Int64Index = Int64Index  # type: ignore[attr-defined]
    assert LEGACY_MODULE not in sys.modules, "pandas unexpectedly provides the legacy module"
    sys.modules[LEGACY_MODULE] = module
    try:
        yield Int64Index
    finally:
        sys.modules.pop(LEGACY_MODULE, None)


def legacy_payload(day: str, seed: int = 0) -> dict[str, Any]:
    """Return a dict with the same keys, index names and dtypes as a real file."""
    rng = np.random.default_rng(seed)
    hours = list(range(24))
    buses = ["Bus A", "Bus B", "Bus C"]
    lines = ["L-1", "L-2"]
    gens = ["G1", "G2"]

    def mi(*levels: list[Any], names: list[str]) -> pd.MultiIndex:
        return pd.MultiIndex.from_product(levels, names=names)

    bus_idx = mi([day], hours, buses, names=["Date", "Hour", "Bus"])
    line_idx = mi([day], hours, lines, names=["Date", "Hour", "Line"])
    gen_idx = mi([day], hours, gens, names=["Date", "Hour", "Generator"])
    commit_cols = pd.MultiIndex.from_product([["Commit"], [str(h) for h in range(1, 4)]])
    return {
        "hourly_summary": pd.DataFrame(
            {"Price": rng.normal(size=24), "Number on/offs": rng.integers(0, 9, 24)},
            index=mi([day], hours, names=["Date", "Hour"]),
        ),
        "thermal_detail": pd.DataFrame(
            {"Dispatch": rng.normal(size=48), "Unit State": rng.integers(0, 2, 48).astype(bool)},
            index=gen_idx,
        ),
        "daily_commits": pd.DataFrame(
            rng.integers(0, 2, (2, 3)).astype(float),
            index=mi([day], [0], gens, names=["Date", "Hour", "Generator"]),
            columns=commit_cols,
        ),
        "bus_detail": pd.DataFrame(
            {"Demand": rng.normal(size=72), "Mismatch": 0.0, "LMP": rng.normal(20, 5, 72)},
            index=bus_idx,
        ),
        "line_detail": pd.DataFrame({"Flow": rng.normal(size=48)}, index=line_idx),
        "total_runtime": 998.2817,
    }


def write_legacy_file(directory: Path, day: str, seed: int = 0) -> tuple[Path, dict[str, Any]]:
    """Write <day>.p.gz as bzip2 + dill with an Int64Index reference. Returns (path, payload)."""
    payload = legacy_payload(day, seed)
    with _fake_legacy_index_module() as int64_index:
        legacy = dict(payload)
        frame = payload["hourly_summary"].reset_index(drop=True)
        frame.index = int64_index._simple_new(np.arange(24, dtype="int64"))
        legacy["hourly_summary_flat"] = frame
        with warnings.catch_warnings():
            # Expected: dill notes the fake class is not importable from pandas itself.
            warnings.simplefilter("ignore", dill.PicklingWarning)
            raw = dill.dumps(legacy, protocol=5, byref=True)  # reference classes by name, as the real files do
    payload["hourly_summary_flat"] = frame.set_axis(pd.Index(np.arange(24, dtype="int64")))
    path = directory / f"{day}.p.gz"
    path.write_bytes(bz2.compress(raw))
    return path, payload
