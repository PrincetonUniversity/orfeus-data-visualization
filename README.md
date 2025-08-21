# ORFEUS Dash App

This repository contains a Dash application for visualizing scenarios, risk allocation, and LMPs. Tested on Python 3.13.

## Running locally (Python 3.13)
```
python3.13 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Always mount your local `data/` directory; enable stub mode to run without full datasets.

1. Build the image
2. Run the container with a volume mount and stub mode (safe without data present):

```sh
docker build -t orfeus-app .
docker run --name orfeus-app --rm -p 8055:8055 -e PORT=8055 -e STUB_MODE=1 -v "$PWD/data:/app/data" orfeus-app
```

If you have full data available, you can drop STUB_MODE=1 to use real datasets.

## Running locally (Conda, Python 3.13)
- Create and activate the environment from `environment.yml`:
```
conda env create -f environment.yml
conda activate dashenv
```
- Optional: set environment variables (Dropbox and local PGScen directory):
```
export DROPBOX_APP_KEY="<your_key>"
export DROPBOX_APP_SECRET="<your_secret>"
export DROPBOX_REFRESH_TOKEN="<your_refresh_token>"
# If you have PGScen CSVs locally (outside Docker), point the app to them
export ORFEUS_PGSCEN_DIR="$PWD/data/PGscen_Scenarios"
```
- Run the app:
```
python app.py
```
- Optional: run on a custom port:
```
PORT=8056 python app.py
```

Tips
- If the env already exists, update it: `conda env update -f environment.yml --prune`
- If you use mamba: `mamba env create -f environment.yml`
- macOS/zsh: export variables in the same shell session before running `python app.py`.

## Running locally (uv)
uv is a fast Python package manager from Astral. You can use it instead of pip/venv.

- Create and activate a virtual environment:
```
uv venv .venv
source .venv/bin/activate
```
- Install dependencies from `requirements.txt` (sync keeps the env exactly in sync):
```
uv pip sync requirements.txt
```
- Optional: set environment variables (Dropbox and local PGScen directory):
```
export DROPBOX_APP_KEY="<your_key>"
export DROPBOX_APP_SECRET="<your_secret>"
export DROPBOX_REFRESH_TOKEN="<your_refresh_token>"
export ORFEUS_PGSCEN_DIR="$PWD/data/PGscen_Scenarios"
```
- Run the app (either works):
```
uv run app.py
# or
python app.py
```
- Optional: choose a port:
```
PORT=8056 uv run app.py
```

Notes
- Install uv: https://docs.astral.sh/uv/getting-started/installation/
- You can also use `uv pip install -r requirements.txt` if you don’t need syncing behavior.

## Container build and run
Build the image:
```
docker build -t orfeus-app .
```
Run the container (maps port 8055):
```
docker run --rm -p 8055:8055 \
  -e PORT=8055 \
  -e DROPBOX_APP_KEY="$DROPBOX_APP_KEY" \
  -e DROPBOX_APP_SECRET="$DROPBOX_APP_SECRET" \
  -e DROPBOX_REFRESH_TOKEN="$DROPBOX_REFRESH_TOKEN" \
  -e ORFEUS_PGSCEN_DIR="/app/data/PGscen_Scenarios" \
  -v "$PWD/data:/app/data" \
  orfeus-app
```
- Health check endpoint: `GET /healthz`

## Notes
- The app reads local data from `data/` under the project root. In Docker, mount your data directory to `/app/data` so the app can find it.
- Dropbox credentials are optional; when set via env the app will read from Dropbox as well.

Expected local data layout under `data/` (used when available):

- Scenarios (CSV per-day/per-asset):
  - `data/scenarios_data/rts-scens-csv/<YYYYMMDD>/{load|wind|solar}/<ASSET_ID>.csv`
  - `data/scenarios_data/t7k-scens-csv/<YYYYMMDD>/{load|wind|solar}/<ASSET_ID>.csv`
  - The app will also look in `.../{notuning|tuning}/<YYYYMMDD>/{load|wind|solar}/<ASSET_ID>.csv` if present.
- LMPs (compressed pickles used by the LMP page):
  - `data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20/<YYYY-MM-DD>.p.gz`
- Grid topology for Texas-7k (used to plot buses/branches):
  - `data/Vatic_Grids/Texas-7k/TX_Data/SourceData/bus.csv`
  - `data/Vatic_Grids/Texas-7k/TX_Data/SourceData/branch.csv`
  - `data/Vatic_Grids/Texas-7k/TX_Data/SourceData/gen.csv`
- Tuning summary CSVs (used to populate asset lists and defaults):
  - `data/tuning_final_files/*.csv`
  - `data/tuning_final_files/texas7k/*.csv`
  - `data/tuning_final_files/texas7k/pca/*.csv`
- Optional PGScen scenarios (if you set `ORFEUS_PGSCEN_DIR` for local use outside Docker):
  - `data/PGscen_Scenarios/**` containing files like `varios_<type>_<year>_.csv.gz` or `escores_<type>_<year>_.csv.gz`.

Risk Allocation data:
- The Risk Allocation page now reads daily aggregates from local CSVs under `data/reliability_cost_index_data/`.
  - RTS (2020):
    - `data/reliability_cost_index_data/rts/daily_type-allocs_rts_type_allocs.csv`
    - `data/reliability_cost_index_data/rts/daily_type-allocs_rts_asset_allocs.csv`
  - Texas-7k (2018):
    - `data/reliability_cost_index_data/t7k/daily_type-allocs_t7k_type_allocs.csv`
    - `data/reliability_cost_index_data/t7k/daily_type-allocs_t7k_asset_allocs.csv`
  - If these files are missing, the app will display zero-filled stub series for the expected date ranges.

## Styling

All custom styling is centralized in `assets/style.css`. We avoid inline Python style dicts.

Key classes in use:

- Container/layout: `app-content`, `section`
- Typography: `title`, `markdown`, `index-title`, `index-num`
- Controls: `dropdown-short`, `dropdown-long`, `radioitems`, `btn-white`
- Tabs: `tabs`, `tab`, `tab--selected`
- Graph helpers: `graph-pad`
- Misc: `inline`

Navbar styling uses the `dbc-navbar` class; active menu highlight is light gray via CSS overrides. Plotly charts use default templates/colorways—no custom color scales are set in code.

To add new styles, define classes in `assets/style.css` and reference them via `className` in Dash components.

## Editing page content (Markdown)

Static page copy lives in plain Markdown files under `markdown/` so non-programmers can edit text without touching Python:

- `markdown/scenarios.md` → Scenarios overview text on the Scenarios page
- `markdown/lmps_overview.md` → Overview text on the LMP page
- `markdown/lmps_plot.md` → Instructions for the LMP interactive plot
- `markdown/allocation.md` → Overview text on the Risk Allocation page

These are read at runtime via `utils/md.py:load_markdown(...)`. Update the `.md` files and refresh the app to see changes.

## Validate LMP pickle files (CLI)

A helper script validates LMP `.p.gz` files for the LMP page.

- Script: `utils/validate_lmp_pickle.py`
- Run from the project root:
```
python utils/validate_lmp_pickle.py data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20/2018-01-02.p.gz
```
- With custom grid CSVs (optional; improves join checks):
```
python utils/validate_lmp_pickle.py /abs/path/2018-01-02.p.gz \
  --bus-csv /abs/path/bus.csv \
  --branch-csv /abs/path/branch.csv
```

What it checks
- Pickle loads (bz2 first, gzip as fallback) and is a dict with `bus_detail` and `line_detail` DataFrames
- Required columns: bus_detail {Bus, Hour, LMP, Demand, Date, Mismatch}, line_detail {Line, Hour, Flow}
- Hour values within 0..23; numeric types for LMP/Demand/Flow
- Best-effort check that filename date (YYYY-MM-DD) appears in `bus_detail['Date']`
- Optional join coverage to grid CSVs (Bus Name→Bus ID, Line→UID)

Exit codes
- 0 = PASS, non-zero = validation error

## Deploy to Azure Container Apps (HTTPS with Azure Files at /app/data)

This repo includes a sanitized `app.yaml` template (no secrets). Use it to mount an Azure Files share at `/app/data`.

High-level
- Build the image in ACR, create a Storage Account + Files share, create a Log Analytics workspace and Container Apps environment, deploy the app with HTTPS-only ingress to port 8055, then apply `app.yaml` to add the read-only volume mount.

Prereqs
- Azure CLI with the Container Apps extension: `az extension add -n containerapp --upgrade`
- Resource providers registered: `Microsoft.ContainerRegistry`, `Microsoft.App`, `Microsoft.OperationalInsights`, `Microsoft.Insights`, `Microsoft.Storage`

Suggested steps (bash/zsh)
```
# Subscription
SUB_ID="<your-subscription-guid>"
az account set --subscription "$SUB_ID"

# Register providers (re-run until all show Registered)
for ns in Microsoft.ContainerRegistry Microsoft.App Microsoft.OperationalInsights Microsoft.Insights Microsoft.Storage; do
  az provider register --namespace "$ns"
done
for ns in Microsoft.ContainerRegistry Microsoft.App Microsoft.OperationalInsights Microsoft.Insights Microsoft.Storage; do
  echo -n "$ns: "; az provider show -n "$ns" --query registrationState -o tsv
done

# Variables
location="eastus"; rg="orfeus-rg"; acr="orfeusacr$RANDOM"; sa="orfeusdata$RANDOM"; share="data"
workspace="orfeus-law"; envname="orfeus-env"; appname="orfeus-app"; image="orfeus-app:latest"; port=8055

# Group + ACR + build
az group create -n "$rg" -l "$location"
az acr create -g "$rg" -n "$acr" --sku Basic
az acr build --registry "$acr" --image "$image" .

# Storage + Files (ReadOnly mount planned)
az storage account create -n "$sa" -g "$rg" -l "$location" --sku Standard_LRS --kind StorageV2
az storage share create --name "$share" --account-name "$sa"
sa_key=$(az storage account keys list -g "$rg" -n "$sa" --query "[0].value" -o tsv)

# Log Analytics + Container Apps env
law_cid=$(az monitor log-analytics workspace show -g "$rg" -n "$workspace" --query customerId -o tsv)
law_key=$(az monitor log-analytics workspace get-shared-keys -g "$rg" -n "$workspace" --query primarySharedKey -o tsv)
az containerapp env create -n "$envname" -g "$rg" \
  --location "$location" \
  --logs-workspace-id "$law_cid" \
  --logs-workspace-key "$law_key"

# Environment storage (Azure Files, ReadOnly)
az containerapp env storage set \
  --name "$envname" -g "$rg" \
  --storage-name "$share" \
  --access-mode ReadOnly \
  --account-name "$sa" \
  --azure-file-account-key "$sa_key" \
  --azure-file-share-name "$share"

# App (HTTPS-only, target-port 8055)
az containerapp create -n "$appname" -g "$rg" \
  --environment "$envname" \
  --image "$acr.azurecr.io/$image" \
  --registry-server "$acr.azurecr.io" \
  --registry-identity system \
  --target-port $port \
  --ingress external \
  --env-vars PORT=$port
az containerapp ingress enable --name "$appname" -g "$rg" --target-port $port --type external --allow-insecure false

# Mount Azure Files using app.yaml (edit placeholders first)
az containerapp update -n "$appname" -g "$rg" --yaml app.yaml

# Grant AcrPull to the app identity
app_principal=$(az containerapp show -n "$appname" -g "$rg" --query "identity.principalId" -o tsv)
acr_id=$(az acr show -n "$acr" -g "$rg" --query id -o tsv)
az role assignment create --assignee "$app_principal" --role AcrPull --scope "$acr_id"

# Public URL & logs
az containerapp show -n "$appname" -g "$rg" --query properties.configuration.ingress.fqdn -o tsv
az containerapp logs show -n "$appname" -g "$rg" --follow --tail 100
```

app.yaml template
- `app.yaml` is sanitized. Replace placeholders: `<APP_NAME>`, `<LOCATION>`, `<ENV_RESOURCE_ID>`, `<ACR_SERVER>`, `<IMAGE_NAME>`, `<TAG>`, `<SHARE_NAME>`.
- Apply with: `az containerapp update -n "$appname" -g "$rg" --yaml app.yaml`
- Do not commit live resource IDs/secrets.
