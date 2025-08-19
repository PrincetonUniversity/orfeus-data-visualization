#!/usr/bin/env python3
import argparse
import os
import sys
import bz2
import gzip
from pathlib import Path

import pandas as pd
import dill as pickle  # dill handles objects pickled with dill

REQUIRED_BUS_COLS = {"Bus", "Hour", "LMP", "Demand", "Date", "Mismatch"}
REQUIRED_LINE_COLS = {"Line", "Hour", "Flow"}


def _load_pickle_any(path: Path):
    try:
        with bz2.BZ2File(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        try:
            with gzip.open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e_gz:
            raise RuntimeError(f"Failed to load {path} via bz2 and gzip") from e_gz


def validate_lmp_pickle(path: Path, bus_csv: Path = None, branch_csv: Path = None) -> bool:
    print(f"Validating: {path}")
    obj = _load_pickle_any(path)

    if not isinstance(obj, dict):
        print("ERROR: Pickle root object is not a dict", file=sys.stderr)
        return False

    for key in ("bus_detail", "line_detail"):
        if key not in obj:
            print(f"ERROR: Missing key '{key}' in pickle", file=sys.stderr)
            return False
        if not isinstance(obj[key], pd.DataFrame):
            print(f"ERROR: '{key}' is not a pandas DataFrame", file=sys.stderr)
            return False

    bus_detail = obj["bus_detail"].reset_index()
    line_detail = obj["line_detail"].reset_index()

    # Required columns present
    missing_bus = REQUIRED_BUS_COLS - set(bus_detail.columns)
    missing_line = REQUIRED_LINE_COLS - set(line_detail.columns)
    if missing_bus:
        print(f"ERROR: bus_detail missing columns: {sorted(missing_bus)}", file=sys.stderr)
        return False
    if missing_line:
        print(f"ERROR: line_detail missing columns: {sorted(missing_line)}", file=sys.stderr)
        return False

    # Hour range sanity
    if not set(bus_detail["Hour"].unique()).issubset(set(range(24))):
        print("ERROR: bus_detail Hour not within 0..23", file=sys.stderr)
        return False
    if not set(line_detail["Hour"].unique()).issubset(set(range(24))):
        print("ERROR: line_detail Hour not within 0..23", file=sys.stderr)
        return False

    # Numeric types
    for col in ("LMP", "Demand"):
        if not pd.api.types.is_numeric_dtype(bus_detail[col]):
            print(f"ERROR: bus_detail[{col}] not numeric", file=sys.stderr)
            return False
    if not pd.api.types.is_numeric_dtype(line_detail["Flow"]):
        print("ERROR: line_detail[Flow] not numeric", file=sys.stderr)
        return False

    # Filename date vs data date (best-effort)
    file_date = path.name.replace(".p.gz", "")
    try:
        bd_dates = pd.to_datetime(bus_detail["Date"]).dt.strftime("%Y-%m-%d").unique()
        if file_date not in bd_dates:
            print(f"Warn: file date {file_date} not found in bus_detail['Date'] {bd_dates}")
    except Exception:
        print("Warn: could not parse bus_detail['Date'] to validate against filename")

    print(f"- bus_detail shape: {bus_detail.shape}, line_detail shape: {line_detail.shape}")
    print(f"- unique buses: {bus_detail['Bus'].nunique()}, unique lines: {line_detail['Line'].nunique()}")

    # Optional: confirm joinability to grid CSVs
    if bus_csv and bus_csv.exists():
        try:
            bus = pd.read_csv(bus_csv)
            merged_b = bus_detail.merge(bus[["Bus Name", "Bus ID"]], left_on="Bus", right_on="Bus Name", how="left")
            coverage_b = merged_b["Bus ID"].notna().mean()
            print(f"- bus merge coverage: {coverage_b:.1%} matched to Bus Name ({bus_csv})")
            if coverage_b == 0:
                print("Warn: no Bus names matched; check naming convention")
        except Exception as e:
            print(f"Warn: failed to read/merge bus CSV: {e}")

    if branch_csv and branch_csv.exists():
        try:
            branch = pd.read_csv(branch_csv)
            merged_l = line_detail.merge(branch[["UID"]], left_on="Line", right_on="UID", how="left")
            coverage_l = merged_l["UID"].notna().mean()
            print(f"- line merge coverage: {coverage_l:.1%} matched to UID ({branch_csv})")
            if coverage_l == 0:
                print("Warn: no Lines matched; ensure Line equals UID in your CSV")
        except Exception as e:
            print(f"Warn: failed to read/merge branch CSV: {e}")

    print("PASS")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate an LMP .p.gz pickle file for expected shape/content."
    )
    parser.add_argument(
        "pickle_path",
        help="Path to the .p.gz file (e.g., data/lmps_data_visualization/.../2018-01-02.p.gz)",
    )
    parser.add_argument(
        "--bus-csv",
        default="data/Vatic_Grids/Texas-7k/TX_Data/SourceData/bus.csv",
        help="Path to bus.csv (optional; improves validation)",
    )
    parser.add_argument(
        "--branch-csv",
        default="data/Vatic_Grids/Texas-7k/TX_Data/SourceData/branch.csv",
        help="Path to branch.csv (optional; improves validation)",
    )
    args = parser.parse_args()

    pkl = Path(args.pickle_path)
    if not pkl.exists():
        print(f"ERROR: Pickle not found: {pkl}", file=sys.stderr)
        return 2

    bus_csv = Path(args.bus_csv) if args.bus_csv else None
    branch_csv = Path(args.branch_csv) if args.branch_csv else None

    ok = validate_lmp_pickle(pkl, bus_csv=bus_csv, branch_csv=branch_csv)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())