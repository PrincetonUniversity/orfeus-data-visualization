# ORFEUS Data Visualization 

ORFEUS Data Visualization is an application for visualizing energy demand scenarios, risk allocation, and LMPs. The app provides data visualization for [Operational Risk Financialization of Electricity Under Stochasticity](https://orfeus.princeton.edu) (ORFEUS), Princeton University’s PERFORM team. 

## Data Requirements 

The application will run without a `data` directory but will default to "Stub Mode" with placeholders and a warning that data is missing.

The `data` directory need contain tuning files, grid topology files, and datasets.

* The tuning files are expected in `data/tuning_final_files`.  These are used to build asset lists and dates.
* Three grid topology files (`bus.csv`, `branch.csv`, `gen.csv`) are expected in `data/Vatic_Grids/Texas-7k/TX_Data/SourceData`.
* Time series per-day and per-asset CSVs are expected in `data/scenarios_data` for Scenarios.
* Four CSVs are expected in `data/reliability_cost_index_data` for Reliability Cost Index (Risk Allocation).
* Per-day pickled data is expected in `data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20` for LMP Geographic Plots.

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

Validate LMP `.p.gz` files (pickles) with `utils/validate_lmp_pickle.py`.

```
python utils/validate_lmp_pickle.py data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20/2018-01-02.p.gz
```

Check the overall health of the app by running a GET of `/healthz`.