# ORFEUS Dash App

This repository contains a Dash application for visualizing scenarios, risk allocation, and LMPs.

## Running locally (Python)
- Create a virtual environment and install requirements:
```
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

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
