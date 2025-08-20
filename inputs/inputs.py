from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import os

import pandas as pd  # type: ignore

from utils.config import SETTINGS
from utils.dropbox_client import get_dropbox


# Expose root dir for other modules
ROOT_DIR: str = str(SETTINGS.root_dir)

# Dropbox client, so pages can import dbx/HAS_DROPBOX from here without importing Dash app
dbx, HAS_DROPBOX = get_dropbox()


def process_date_column(df: pd.DataFrame, date_column: str = 'time') -> pd.DataFrame:
    """Ensure a 'time' datetime column exists.

    Tries common patterns: existing 'time' column, alternative names
    like 'Timestamp', 'Date', 'Unnamed: 0', or a datetime index. As a
    last resort, creates an hourly range starting at 1970-01-01.
    """
    if df is None or df.empty:
        return df

    df2 = df.copy()

    # Prefer an existing 'time' column
    if 'time' in df2.columns:
        # Normalize to tz-naive consistently (assume UTC if tz provided)
        s = pd.to_datetime(df2['time'], errors='coerce', utc=True)
        try:
            s = s.dt.tz_convert(None)
        except Exception:
            # Already tz-naive
            s = s.tz_localize(None) if hasattr(s.dt, 'tz_localize') else s
        df2['time'] = s
        return df2

    # Try common alternative column names
    alt_names = ['Time', 'timestamp', 'Timestamp', 'date', 'Date', 'Datetime', 'datetime', 'Unnamed: 0', 'index']
    for name in alt_names:
        if name in df2.columns:
            df2 = df2.rename(columns={name: 'time'})
            s = pd.to_datetime(df2['time'], errors='coerce', utc=True)
            try:
                s = s.dt.tz_convert(None)
            except Exception:
                s = s.tz_localize(None) if hasattr(s.dt, 'tz_localize') else s
            df2['time'] = s
            return df2

    # If index is datetime-like, lift it into a column
    try:
        if pd.api.types.is_datetime64_any_dtype(df2.index):
            df2 = df2.reset_index().rename(columns={'index': 'time'})
            s = pd.to_datetime(df2['time'], errors='coerce', utc=True)
            try:
                s = s.dt.tz_convert(None)
            except Exception:
                s = s.tz_localize(None) if hasattr(s.dt, 'tz_localize') else s
            df2['time'] = s
            return df2
    except Exception:
        pass

    # Fallback: synthesize an hourly timeline (will likely be filtered out later)
    try:
        df2.insert(0, 'time', pd.date_range('1970-01-01', periods=len(df2), freq='H'))
    except Exception:
        df2.insert(0, 'time', pd.Series([pd.NaT] * len(df2)))
    return df2


# Paths
data_tuning_dir = SETTINGS.root_dir / 'data' / 'tuning_final_files'
data_t7k_pca_dir = data_tuning_dir / 'texas7k' / 'pca'
data_t7k_dir = data_tuning_dir / 'texas7k'


def _safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        # Return empty with guessed column name from filename
        return pd.DataFrame()


# Read CSVs (best-effort; tolerate missing local data)
df_escores_rhos_solar_nonpca = _safe_read_csv(data_tuning_dir / 'escores_avg_on_tuning_solar_rhos.csv')
df_escores_rhos_load_nonpca = _safe_read_csv(data_tuning_dir / 'escores_avg_on_tuning_load_rhos.csv')
df_escores_rhos_wind_nonpca = _safe_read_csv(data_tuning_dir / 'escores_avg_on_tuning_wind_rhos.csv')

df_escores_rhos_solar_pca_t7k = _safe_read_csv(data_t7k_pca_dir / 'escores_avg_on_tuning_solar_rhos.csv')

df_escores_rhos_solar_nonpca_t7k = _safe_read_csv(data_t7k_dir / 'escores_avg_on_tuning_solar_rhos.csv')
df_escores_rhos_load_nonpca_t7k = _safe_read_csv(data_t7k_dir / 'escores_avg_on_tuning_load_rhos.csv')
df_escores_rhos_wind_nonpca_t7k = _safe_read_csv(data_t7k_dir / 'escores_avg_on_tuning_wind_rhos.csv')


# Find the list of asset ids
def _unique_plus_avg(df: pd.DataFrame, col: str) -> List[str]:
    if df.empty or col not in df.columns:
        return ['AVG']
    vals = list(pd.Series(df[col]).dropna().astype(str).unique())
    return vals + ['AVG']


solar_asset_ids = _unique_plus_avg(df_escores_rhos_solar_nonpca, 'solar')
load_asset_ids = _unique_plus_avg(df_escores_rhos_load_nonpca, 'load')
wind_asset_ids = _unique_plus_avg(df_escores_rhos_wind_nonpca, 'wind')

solar_asset_ids_t7k = _unique_plus_avg(df_escores_rhos_solar_nonpca_t7k, 'solar')
load_asset_ids_t7k = _unique_plus_avg(df_escores_rhos_load_nonpca_t7k, 'load')
wind_asset_ids_t7k = _unique_plus_avg(df_escores_rhos_wind_nonpca_t7k, 'wind')


# Create date values for RTS/T7K
date_values_rts = [str(i)[:10] for i in pd.date_range(start='2020-01-01', end='2020-12-29')]
date_values_t7k = [str(i)[:10] for i in pd.date_range(start='2018-01-02', end='2018-12-31')]

energy_types = ['load', 'wind', 'solar']
energy_types_asset_ids = {
    'load': load_asset_ids,
    'wind': wind_asset_ids,
    'solar': solar_asset_ids,
}
energy_types_asset_ids_wind_solar = {
    'wind': wind_asset_ids,
    'solar': solar_asset_ids,
}
energy_types_asset_ids_t7k = {
    'load': load_asset_ids_t7k,
    'wind': wind_asset_ids_t7k,
    'solar': solar_asset_ids_t7k,
}
energy_types_asset_ids_t7k_csv = {
    'load': [i.replace(' ', '_') for i in load_asset_ids_t7k],
    'wind': [i.replace(' ', '_') for i in wind_asset_ids_t7k],
    'solar': [i.replace(' ', '_') for i in solar_asset_ids_t7k],
}
energy_types_asset_ids_wind_solar_t7k = {
    'wind': wind_asset_ids_t7k,
    'solar': solar_asset_ids_t7k,
}
energy_types_asset_ids_rts_csv = {
    'load': load_asset_ids[:-1],
    'wind': wind_asset_ids[:-1],
    'solar': solar_asset_ids[:-1],
}


def _stub_hourly_df(start: str, end: str, cols: List[str]) -> pd.DataFrame:
    rng = pd.date_range(start=start, end=end, freq='H')
    df = pd.DataFrame(index=rng, data={c: 0.0 for c in cols})
    df = df.reset_index().rename(columns={'index': 'time'})
    return df


def _safe_read_dropbox_csv(dbx_path: str, fallback_local: Optional[str], stub_cols: List[str],
                           start: str, end: str) -> pd.DataFrame:
    # Placeholder: current project primarily uses local files. Implement if Dropbox CSVs are needed.
    if fallback_local:
        return _safe_read_local_csv(fallback_local, stub_cols, start, end)
    return _stub_hourly_df(start, end, stub_cols)


def _safe_read_local_csv(local_rel_path: str, stub_cols: List[str], start: str, end: str) -> pd.DataFrame:
    path = SETTINGS.root_dir / local_rel_path
    try:
        df = pd.read_csv(path)

        # If the file is empty or has no columns, synthesize a stub
        if df is None or df.empty or len(df.columns) == 0:
            return _stub_hourly_df(start, end, stub_cols)

        # Normalize possible time column names
        time_col = None
        for name in ['time', 'Time', 'timestamp', 'Timestamp', 'date', 'Date', 'Datetime', 'datetime', 'Unnamed: 0', 'index']:
            if name in df.columns:
                time_col = name
                break

        if time_col is not None:
            if time_col != 'time':
                df = df.rename(columns={time_col: 'time'})
            s = pd.to_datetime(df['time'], errors='coerce', utc=True)
            try:
                s = s.dt.tz_convert(None)
            except Exception:
                s = s.tz_localize(None) if hasattr(s.dt, 'tz_localize') else s
            df['time'] = s
            start_dt = pd.to_datetime(start)
            end_dt = pd.to_datetime(end)
            return df[(df['time'] >= start_dt) & (df['time'] <= end_dt)]

        # If we couldn't find a time column, return a stub with provided columns
        return _stub_hourly_df(start, end, stub_cols)
    except Exception:
        return _stub_hourly_df(start, end, stub_cols)


# Risk Allocation (local only)
folder_path_local = 'data/reliability_cost_index_data'

# Type-level RTS (expects columns like WIND, PV, RTPV)
type_allocs_rts = _safe_read_local_csv(
    os.path.join(folder_path_local, 'rts', 'daily_type-allocs_rts_type_allocs.csv'),
    stub_cols=['WIND', 'PV', 'RTPV'],
    start='2020-01-01 00:00', end='2020-12-31 23:00')

# Asset-level RTS (unknown asset ids -> provide placeholders)
asset_allocs_rts = _safe_read_local_csv(
    os.path.join(folder_path_local, 'rts', 'daily_type-allocs_rts_asset_allocs.csv'),
    stub_cols=['Asset-1', 'Asset-2'],
    start='2020-01-01 00:00', end='2020-12-31 23:00')

# Type-level T7K (WIND, PV)
type_allocs_t7k = _safe_read_local_csv(
    os.path.join(folder_path_local, 't7k', 'daily_type-allocs_t7k_type_allocs.csv'),
    stub_cols=['WIND', 'PV'],
    start='2018-01-01 00:00', end='2018-12-31 23:00')

# Asset-level T7K
asset_allocs_t7k = _safe_read_local_csv(
    os.path.join(folder_path_local, 't7k', 'daily_type-allocs_t7k_asset_allocs.csv'),
    stub_cols=['Asset-1', 'Asset-2'],
    start='2018-01-01 00:00', end='2018-12-31 23:00')

type_allocs_rts = process_date_column(type_allocs_rts)
asset_allocs_rts = process_date_column(asset_allocs_rts)
type_allocs_t7k = process_date_column(type_allocs_t7k)
asset_allocs_t7k = process_date_column(asset_allocs_t7k)

# read grid data
bus = pd.read_csv(os.path.join(ROOT_DIR,
                               'data', 'Vatic_Grids', 'Texas-7k', 'TX_Data', 'SourceData', 'bus.csv'))
branch = pd.read_csv(os.path.join(ROOT_DIR,
                                  'data', 'Vatic_Grids', 'Texas-7k', 'TX_Data', 'SourceData', 'branch.csv'))
gens = pd.read_csv(os.path.join(ROOT_DIR,
                                'data', 'Vatic_Grids', 'Texas-7k', 'TX_Data', 'SourceData', 'gen.csv'))

branch['Cont Rating'] = branch['Cont Rating'].replace(0, 1e6)
# Consider the case that one bus may have multiple generators, put the list of enerators inside array
gens_busid = gens[['Bus ID', 'GEN UID']].groupby(['Bus ID'])[
    'GEN UID'].unique().reset_index()
bus = pd.merge(bus, gens_busid, how='left', on='Bus ID')
bus['GEN UID'] = bus['GEN UID'].fillna('Not Gen')

