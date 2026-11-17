#!/usr/bin/env python3
"""Validate migrated LMP Parquet data (bus_detail and line_detail) for one day or all days.

Usage:
    python utils/validate_lmp_data.py 2018-01-02
    python utils/validate_lmp_data.py --all

Exit codes: 0 all valid, 1 a day failed validation, 2 data missing or bad arguments.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.lmp_store import load_bus_line, parquet_dataset_dir, validate_day

REQUIRED_BUS_COLS = {"Bus", "Hour", "LMP", "Demand", "Date", "Mismatch"}
REQUIRED_LINE_COLS = {"Line", "Hour", "Flow"}
GRID_DIR = Path("data/Vatic_Grids/Texas-7k/TX_Data/SourceData")


def check_day(bus_detail: pd.DataFrame, line_detail: pd.DataFrame, day: str) -> list[str]:
    """Return a list of problems; empty means valid."""
    problems = []
    missing_bus = REQUIRED_BUS_COLS - set(bus_detail.columns)
    missing_line = REQUIRED_LINE_COLS - set(line_detail.columns)
    if missing_bus:
        problems.append(f"bus_detail missing columns: {sorted(missing_bus)}")
    if missing_line:
        problems.append(f"line_detail missing columns: {sorted(missing_line)}")
    if problems:
        return problems
    for name, frame in (("bus_detail", bus_detail), ("line_detail", line_detail)):
        if not set(frame["Hour"].unique()) <= set(range(24)):
            problems.append(f"{name} Hour not within 0..23")
    for col in ("LMP", "Demand"):
        if not pd.api.types.is_numeric_dtype(bus_detail[col]):
            problems.append(f"bus_detail[{col}] not numeric")
    if not pd.api.types.is_numeric_dtype(line_detail["Flow"]):
        problems.append("line_detail[Flow] not numeric")
    dates = set(pd.to_datetime(bus_detail["Date"]).dt.strftime("%Y-%m-%d"))
    if dates != {day}:
        problems.append(f"bus_detail Date values {sorted(dates)} do not match {day}")
    return problems


def report_coverage(bus_detail: pd.DataFrame, line_detail: pd.DataFrame,
                    bus_csv: Path | None, branch_csv: Path | None) -> None:
    if bus_csv and bus_csv.exists():
        names = set(pd.read_csv(bus_csv, usecols=["Bus Name"])["Bus Name"])
        print(f"  bus merge coverage: {bus_detail['Bus'].isin(names).mean():.1%} matched to Bus Name")
    if branch_csv and branch_csv.exists():
        uids = set(pd.read_csv(branch_csv, usecols=["UID"])["UID"])
        print(f"  line merge coverage: {line_detail['Line'].isin(uids).mean():.1%} matched to UID")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("day", nargs="?", help="day to validate, YYYY-MM-DD")
    target.add_argument("--all", action="store_true", help="validate every migrated day")
    parser.add_argument("--data-root", type=Path, default=Path("data"), help="data directory (default: data)")
    parser.add_argument("--bus-csv", type=Path, default=GRID_DIR / "bus.csv", help="optional bus.csv for coverage")
    parser.add_argument("--branch-csv", type=Path, default=GRID_DIR / "branch.csv",
                        help="optional branch.csv for coverage")
    args = parser.parse_args(argv)

    if args.all:
        dataset = parquet_dataset_dir(args.data_root)
        days = sorted(p.name for p in dataset.iterdir() if p.is_dir() and not p.name.startswith(".")) \
            if dataset.is_dir() else []
        if not days:
            print(f"ERROR: no migrated days under {dataset}", file=sys.stderr)
            return 2
    else:
        try:
            days = [validate_day(args.day)]
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    failed = 0
    for day in days:
        try:
            bus_detail, line_detail = load_bus_line(args.data_root, day)
        except (ValueError, OSError) as exc:
            print(f"{day}: ERROR cannot load ({type(exc).__name__}: {exc})", file=sys.stderr)
            if not args.all:
                return 2
            failed += 1
            continue
        problems = check_day(bus_detail, line_detail, day)
        if problems:
            failed += 1
            print(f"{day}: FAIL " + "; ".join(problems))
            continue
        print(f"{day}: PASS bus_detail {bus_detail.shape}, line_detail {line_detail.shape}")
        if not args.all:
            report_coverage(bus_detail, line_detail, args.bus_csv, args.branch_csv)
    print(f"Validated {len(days)} day(s), {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
