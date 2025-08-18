import io
import os, sys
import pandas as pd
from typing import List, Optional
from datetime import date, timedelta, datetime

# Local Dropbox configuration to avoid importing the Dash app (prevents circular imports)
try:
    import dropbox  # type: ignore
except Exception:
    dropbox = None

APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

dbx = None
HAS_DROPBOX = False
if dropbox is not None and APP_KEY and APP_SECRET and REFRESH_TOKEN:
    try:
        dbx = dropbox.Dropbox(app_key=APP_KEY,
                              app_secret=APP_SECRET,
                              oauth2_refresh_token=REFRESH_TOKEN)
        HAS_DROPBOX = True
    except Exception:
        dbx = None
        HAS_DROPBOX = False

# Resolve project root based on this file location so it works from any CWD
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Import Dataset
# PCA Rhos

def process_date_column(df, date_column='index'):
    df[date_column] = df[date_column].apply(
        lambda x: datetime.strptime(x[:13], "%Y-%m-%d %H"))
    df = df.rename(columns={'index': 'time'})
    return df

data_tuning_dir = os.path.join(ROOT_DIR, 'data', 'tuning_final_files')
df_escores_rhos_solar_nonpca = pd.read_csv(
    os.path.join(data_tuning_dir, f"{'escores'}_avg_on_tuning_{'solar'}_rhos.csv"))

df_escores_rhos_load_nonpca = pd.read_csv(
    os.path.join(data_tuning_dir, f"{'escores'}_avg_on_tuning_{'load'}_rhos.csv"))

df_escores_rhos_wind_nonpca = pd.read_csv(
    os.path.join(data_tuning_dir, f"{'escores'}_avg_on_tuning_{'wind'}_rhos.csv"))

# Texas7K
# PCA
data_t7k_pca_dir = os.path.join(ROOT_DIR, 'data', 'tuning_final_files', 'texas7k', 'pca')
df_escores_rhos_solar_pca_t7k = pd.read_csv(
    os.path.join(data_t7k_pca_dir, f"{'escores'}_avg_on_tuning_{'solar'}_rhos.csv"))


# NonPCA
data_t7k_dir = os.path.join(ROOT_DIR, 'data', 'tuning_final_files', 'texas7k')
df_escores_rhos_solar_nonpca_t7k = pd.read_csv(
    os.path.join(data_t7k_dir, f"{'escores'}_avg_on_tuning_{'solar'}_rhos.csv"))

df_escores_rhos_load_nonpca_t7k = pd.read_csv(
    os.path.join(data_t7k_dir, f"{'escores'}_avg_on_tuning_{'load'}_rhos.csv"))

df_escores_rhos_wind_nonpca_t7k = pd.read_csv(
    os.path.join(data_t7k_dir, f"{'escores'}_avg_on_tuning_{'wind'}_rhos.csv"))

# Find the list of asset ids
# RTS
solar_asset_ids = list(df_escores_rhos_solar_nonpca['solar'].unique())
solar_asset_ids.append('AVG')

load_asset_ids = list(df_escores_rhos_load_nonpca['load'].unique())
load_asset_ids.append('AVG')

wind_asset_ids = list(df_escores_rhos_wind_nonpca['wind'].unique())
wind_asset_ids.append('AVG')

# Texas7k
solar_asset_ids_t7k = list(
    df_escores_rhos_solar_nonpca_t7k['solar'].unique())
solar_asset_ids_t7k.append('AVG')

load_asset_ids_t7k = list(
    df_escores_rhos_load_nonpca_t7k['load'].unique())
load_asset_ids_t7k.append('AVG')

wind_asset_ids_t7k = list(df_escores_rhos_wind_nonpca_t7k['wind'].unique())
wind_asset_ids_t7k.append('AVG')

# Create date values for Texas7k
date_values_rts = pd.date_range(start='2020-01-01', end='2020-12-29')
date_values_rts = [str(i)[:10] for i in date_values_rts]

date_values_t7k = pd.date_range(start='2018-01-02', end='2018-12-31')
date_values_t7k = [str(i)[:10] for i in date_values_t7k]

energy_types = ['load', 'wind', 'solar']
energy_types_asset_ids = {
    'load': load_asset_ids,
    'wind': wind_asset_ids,
    'solar': solar_asset_ids
}

energy_types_asset_ids_wind_solar = {
    'wind': wind_asset_ids,
    'solar': solar_asset_ids
}

energy_types_asset_ids_t7k = {
    'load': load_asset_ids_t7k,
    'wind': wind_asset_ids_t7k,
    'solar': solar_asset_ids_t7k
}

energy_types_asset_ids_t7k_csv = {
    'load': [i.replace(' ', '_') for i in load_asset_ids_t7k],
    'wind': [i.replace(' ', '_') for i in wind_asset_ids_t7k],
    'solar': [i.replace(' ', '_') for i in solar_asset_ids_t7k]
}

energy_types_asset_ids_wind_solar_t7k = {
    'wind': wind_asset_ids_t7k,
    'solar': solar_asset_ids_t7k
}

energy_types_asset_ids_rts_csv = {
    'load': load_asset_ids[:-1],
    'wind': wind_asset_ids[:-1],
    'solar': solar_asset_ids[:-1]
}

# Select the Day DF

def _stub_hourly_df(start: str, end: str, cols: List[str]) -> pd.DataFrame:
    """Create a stub hourly dataframe with an 'index' column and provided cols filled with 0."""
    rng = pd.date_range(start=start, end=end, freq='H')
    # Use formatted timestamps so x[:13] yields 'YYYY-MM-DD HH'
    df = pd.DataFrame({'index': rng.strftime('%Y-%m-%d %H:%M:%S')})
    for c in cols:
        df[c] = 0.0
    return df

def _safe_read_dropbox_csv(dbx_path: str, fallback_local: Optional[str], stub_cols: List[str],
                           start: str, end: str) -> pd.DataFrame:
    """Try Dropbox, else local CSV (relative to currentpath), else stub hourly df."""
    # Try Dropbox
    if HAS_DROPBOX and dbx is not None:
        try:
            _, res = dbx.files_download(dbx_path)
            with io.BytesIO(res.content) as stream:
                return pd.read_csv(stream, index_col=0).reset_index()
        except Exception:
            pass
    # Try local
    if fallback_local is not None:
        local_path = os.path.join(ROOT_DIR, fallback_local)
        if os.path.exists(local_path):
            try:
                return pd.read_csv(local_path, index_col=0).reset_index()
            except Exception:
                pass
    # Fallback: stub
    return _stub_hourly_df(start=start, end=end, cols=stub_cols)

def _safe_read_local_csv(local_rel_path: str, stub_cols: List[str], start: str, end: str) -> pd.DataFrame:
    """Read a local CSV relative to ROOT_DIR, else return a stub hourly DataFrame."""
    local_path = os.path.join(ROOT_DIR, local_rel_path)
    if os.path.exists(local_path):
        try:
            return pd.read_csv(local_path, index_col=0).reset_index()
        except Exception:
            pass
    return _stub_hourly_df(start=start, end=end, cols=stub_cols)

# Risk Allocation (local only)
folder_path_local = os.path.join('data', 'reliability_cost_index_data')

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

