import os
import dash
import dash_bootstrap_components as dbc
try:
    import dropbox  # type: ignore
except Exception:  # dropbox lib may be missing in some envs
    dropbox = None

app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN],
                suppress_callback_exceptions=True)
app.title = 'ORFEUS Data Website'

# Optional Dropbox config via environment variables; fall back to no Dropbox
# Set env vars: DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN
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
        # light touch: verify credentials lazily at first call; don't ping here
        HAS_DROPBOX = True
    except Exception:
        dbx = None
        HAS_DROPBOX = False

# Simple health endpoint for container orchestrators
@app.server.get("/healthz")
def _healthz():
    return {"status": "ok"}

