"""Layout and loading of the LMP Parquet dataset (issue #1).

Each simulated day is a directory of Parquet files, one per table, plus a
manifest written by scripts/lmp_migration/migrate_lmp_pickles.py:

    <data_root>/lmps_data_visualization/<dataset>-parquet/<YYYY-MM-DD>/
        bus_detail.parquet
        line_detail.parquet
        ... (other simulation tables)
        manifest.json

The app reads only bus_detail and line_detail.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Union

import pandas as pd

LMP_DIRNAME = "lmps_data_visualization"
DATASET = "t7k_v0.4.0-a2_rsvf-20"
PARQUET_SUFFIX = "-parquet"
MANIFEST_NAME = "manifest.json"
APP_TABLES = ("bus_detail", "line_detail")

_DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_TABLE_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

PathLike = Union[str, Path]


def validate_day(day: object) -> str:
    """Return day if it is a real calendar date written as YYYY-MM-DD, else raise ValueError.

    Days come from user input (the date dropdown), so this also blocks path traversal.
    """
    if not isinstance(day, str) or not _DAY_RE.fullmatch(day):
        raise ValueError("day must be a YYYY-MM-DD string")
    _dt.date.fromisoformat(day)  # raises ValueError for impossible dates such as 2018-02-30
    return day


def table_filename(table: str) -> str:
    """Return the Parquet file name for a table, rejecting names unsafe as file names."""
    if not _TABLE_RE.fullmatch(table):
        raise ValueError(f"invalid table name: {table!r}")
    return f"{table}.parquet"


def parquet_dataset_dir(data_root: PathLike, dataset: str = DATASET) -> Path:
    return Path(data_root) / LMP_DIRNAME / f"{dataset}{PARQUET_SUFFIX}"


def day_dir(data_root: PathLike, day: str, dataset: str = DATASET) -> Path:
    return parquet_dataset_dir(data_root, dataset) / validate_day(day)


def load_bus_line(data_root: PathLike, day: str, dataset: str = DATASET) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (bus_detail, line_detail) for one day with the index levels as columns.

    Raises ValueError for an invalid day and FileNotFoundError when the day is missing.
    """
    directory = day_dir(data_root, day, dataset)
    bus, line = (pd.read_parquet(directory / table_filename(t)).reset_index() for t in APP_TABLES)
    return bus, line
