# Codebook

This document describes the contents of the repository `data/` folder, how files are used by the application code, and notes about provenance and regeneration where possible. It's intended as a short codebook / README to help developers and analysts understand what each directory contains and where it is referenced in the codebase.

Path root: `data/`

Canonical storage: the data is stored in Princeton's TigerData service and is currently mounted on della at `/tigerdata/PERFORM/orfeus-data-visualization/data`. The app reads it from `data/` in the repository root (`/app/data` in the container).

Overview
--------
- `lmps_data_visualization/` — Texas-7k production-cost simulation outputs, one day per directory, stored as Parquet. Used by the LMP page.
- `reliability_cost_index_data/` — reliability and cost index outputs split by `rts` and `t7k`. Used by risk/allocation or reliability diagnostics pages.
- `scenarios_data/` — CSV scenario exports organized into `rts-scens-csv/` and `t7k-scens-csv/`. These are the scenario CSVs read by the Scenarios visualization pages.
- `tuning_final_files/` — CSVs and directories from model tuning and scoring runs (escores, varios, PCA outputs, Texas7k results). Used by tuning and risk allocation analyses and for cross-checking parameter sweeps.
- `Vatic_Grids/` — grid metadata or shapefiles for mapping: `RTS-GMLC/` and `Texas-7k/` directories. These are referenced by map visualizations and the LMP mapper.

Detailed directory descriptions
-------------------------------

1) `lmps_data_visualization/`
   - Structure: `lmps_data_visualization/<dataset-version>-parquet/<YYYY-MM-DD>/<table>.parquet`, plus `manifest.json` per day and `SHA256SUMS` for the dataset.
   - Example: `lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20-parquet/2018-01-02/bus_detail.parquet`
   - Tables per day (all indexed by `Date` and `Hour`; most also by an entity):
     - `bus_detail` (by `Bus`): `Demand`, `Mismatch`, `LMP`. Used by the app.
     - `line_detail` (by `Line`): `Flow`. Used by the app.
     - `hourly_summary`, `ruc_summary`, `runtimes`, `thermal_detail` and `renew_detail` (by `Generator`), `daily_commits` (by `Generator`; columns are `Commit`, `Output` and `Reserve` for periods `'1'`..`'48'`). Kept for completeness.
     - `manifest.json` also records the scalar `total_runtime`, the source file's SHA-256, and table shapes.
   - File format: Parquet (zstd). Open with `pandas.read_parquet`. See `utils/lmp_store.py`.
   - Legacy format: `<dataset-version>/<YYYY-MM-DD>.p.gz` files are dill pickles written with pandas 1.x. Despite the `.gz` name they are bzip2-compressed, and they need pandas 1.x index classes to load. `scripts/lmp_migration/` converts them to Parquet (issue #1). The app no longer reads them.
   - Used by: `pages/data_visualization/lmps.py` (LMP maps and charts) and `utils/validate_lmp_data.py`.
   - Surmised provenance: produced by running preprocessing scripts on raw market simulation outputs (Texas-7k model outputs). These are likely derived from simulation runs or feature extraction pipelines maintained with the project.

2) `reliability_cost_index_data/`
   - Subfolders: `rts/`, `t7k/`
   - File types: CSVs or other aggregated outputs (not listed exhaustively in the attachment). May contain per-asset reliability/cost indices computed from scenario ensembles.
   - Used by: risk allocation and reliability index pages (e.g., `pages/data_visualization/risk_allocation.py`) and possibly backend analyses under `utils/`.
   - Surmised provenance: post-processing output from reliability/cost evaluation scripts evaluating scenarios and asset responses.

3) `scenarios_data/`
   - Subfolders: `rts-scens-csv/`, `t7k-scens-csv/`
   - File format: CSV files with scenario time-series (likely one CSV per scenario or one CSV with scenario columns). Column names typically include timestamps and scenario IDs, forecasts, actuals, and summary statistics.
   - Used by: `pages/data_visualization/scenarios.py` reads these CSVs to build the scenario time-series plots, percentile calculations, and summary statistics (5%/95% etc.). The code expects these scenario CSVs to contain the ensemble traces needed for percentile and extreme envelope computations.
   - Surmised provenance: output from scenario-generation runs (ensemble simulations) — either external scenario generators or in-repo scripts that sampled model inputs.

4) `tuning_final_files/`
   - Files: several `escores_*` and `varios_*` CSVs; a `pca/` folder and a `texas7k/` folder.
   - Purpose: These are tuning and evaluation artifacts: scores, variance summaries, and PCA results that were produced while tuning model parameters (e.g., distance metrics, rhos). They are inspected by tuning notebooks or analysis scripts.
   - Used by: tuning analysis pages or scripts; could be read by `pages/data_visualization/risk_allocation.py` or other analysis helpers to show tuning performance or drive defaults.
   - Surmised provenance: Generated by the project's tuning pipeline (parameter sweeps), probably invoked by offline experiments; the file names suggest multiple scoring metrics (escores) and variance summaries (varios).

5) `Vatic_Grids/`
   - Subfolders: `RTS-GMLC/`, `Texas-7k/`
   - Purpose: grid geometry, mapping data, or node-to-lat/lon lookups. Used by LMP mapping code to place markers, color zones, or compute map overlays.
   - Used by: `pages/data_visualization/lmps.py`, mapping utilities under `utils/` (e.g., `ui.py` or mapping helper functions).
   - Surmised provenance: likely hand-curated or converted grid files (from original test systems: RTS-GMLC and Texas-7k synthetic grids) curated for visualization.

Quick mapping of code to data
----------------------------
- `pages/data_visualization/lmps.py`  -> reads `data/lmps_data_visualization/<dataset>-parquet/<day>/{bus,line}_detail.parquet` and `Vatic_Grids/*` for mapping and LMP plots.
- `pages/data_visualization/scenarios.py` -> reads `data/scenarios_data/*-scens-csv/` for scenario ensembles and computes percentiles/extremes.
- `pages/data_visualization/risk_allocation.py` -> uses `reliability_cost_index_data/` and `tuning_final_files/` for allocation visuals and tuning summaries.
- `utils/validate_lmp_data.py` -> validation helper for the LMP Parquet data under `lmps_data_visualization/`.

File format notes & quick inspection
----------------------------------
- To inspect one day of LMP data (Python):

```python
import pandas as pd
day = 'data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20-parquet/2018-01-02'
bus = pd.read_parquet(f'{day}/bus_detail.parquet')
bus.head()

# For CSVs:
import pandas as pd
df = pd.read_csv('data/scenarios_data/t7k-scens-csv/somefile.csv')
df.head()
```

Provenance guidance / assumptions
--------------------------------
- The folder names reflect two main modeling datasets: **Texas-7k** (t7k) and **RTS-GMLC** (rts). These are synthetic grids in power-systems research. 
- Scenario CSVs and LMP data are generated by the Princeton PERFORM Team's upstream simulation pipeline. 
