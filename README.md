# ORFEUS Data Visualization 

ORFEUS Data Visualization is an application for visualizing energy demand scenarios, risk allocation, and LMPs. The app provides data visualization for [Operational Risk Financialization of Electricity Under Stochasticity](https://orfeus.princeton.edu) (ORFEUS), Princeton University’s PERFORM team. 

## Data Requirements 

The application will run without a `data` directory but will default to "Stub Mode" with placeholders and a warning that data is missing.

The `data` directory need contain tuning files, grid topology files, and datasets.  They are **not** provided here.

The canonical copy of the data is stored in Princeton's [TigerData](https://tigerdata.princeton.edu) service. It is currently mounted on della at `/tigerdata/PERFORM/orfeus-data-visualization/data`. Copy or mount that directory as `data/` in the repository root (or at `/app/data` in the container).

* The tuning files are expected in `data/tuning_final_files`.  These are used to build asset lists and dates.
* Three grid topology files (`bus.csv`, `branch.csv`, `gen.csv`) are expected in `data/Vatic_Grids/Texas-7k/TX_Data/SourceData`.
* Time series per-day and per-asset CSVs are expected in `data/scenarios_data` for Scenarios.
* Four CSVs are expected in `data/reliability_cost_index_data` for Reliability Cost Index (Risk Allocation).
* Per-day Parquet data is expected in `data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20-parquet/<YYYY-MM-DD>/` for LMP Geographic Plots. See `scripts/lmp_migration/` to convert the legacy `.p.gz` pickles.

## Runtime Environments 

The app defaults to running at [http://127.0.0.1:8055](http://127.0.0.1:8055).  Select a custom port with `PORT=`.

### venv

```
python -m venv dashenv
. dashenv/bin/activate
pip install -r requirements.txt
unset HOST HOSTNAME FLASK_RUN_HOST DASH_HOST ; PORT=8055 BIND_HOST=127.0.0.1 python app.py
```

### Conda

```
conda env create -f environment.yml
conda activate dashenv
python app.py
```

### uv

```
uv venv dashenv 
source dashenv/bin/activate
uv pip sync requirements.txt
uv run app.py
```

### Docker

```
docker build -t orfeus-app .
docker run --rm -p 8055:8055 \
  -e PORT=8055 \
  -v "$PWD/data:/app/data" \
  orfeus-app
```

## Editing Pages & Styles

Page copy lives in plain Markdown files under `markdown/`.

- `markdown/scenarios.md` → Scenarios overview text on the Scenarios page
- `markdown/lmps_overview.md` → Overview text on the LMP page
- `markdown/lmps_plot.md` → Instructions for the LMP interactive plot
- `markdown/allocation.md` → Overview text on the Risk Allocation page

These are read at runtime via `utils/md.py:load_markdown(...)`. Update the `.md` files and refresh the app to see changes.

All custom styling is centralized in `assets/style.css`. 

## Data Validation & Application Health

Validate data integrity by running:

```
if [ -z "$(sha256sum -c data-checksums.sha256 | grep -v 'OK$')" ]; then echo "All Valid"; fi
```

Validate the LMP Parquet data with `utils/validate_lmp_data.py` (one day, or `--all`).

```
python utils/validate_lmp_data.py 2018-01-02
python utils/validate_lmp_data.py --all
```

## Tests

Run lint, type checks and tests in Docker (also run in CI):

```
docker-compose -f docker-compose.test.yml run --rm --build tests
```

## Migrating the LMP data (issue #1)

The legacy LMP files are dill pickles that need pandas 1.x classes to load. Convert them once, on della, with `scripts/lmp_migration/run_on_della.sh`. It creates its own virtualenv in `$HOME`, never modifies the source files, verifies every table, writes `SHA256SUMS`, and is safe to re-run:

```
export SRC=/tigerdata/PERFORM/orfeus-data-visualization/data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20
export DST=/tigerdata/PERFORM/orfeus-data-visualization/data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20-parquet
scripts/lmp_migration/run_on_della.sh --dry-run          # reads every file, writes nothing
scripts/lmp_migration/run_on_della.sh --limit 3          # trial run
scripts/lmp_migration/run_on_della.sh                    # full run (about 1 GB; stops at --max-output-gb 1.5)
```

Check the overall health of the app by running a GET of `/healthz`.
