import os
import dash
from dash import dcc, html, Input, Output, State, page_registry, page_container
import dash_bootstrap_components as dbc
try:
    import dropbox  # type: ignore
except Exception:  # dropbox lib may be missing in some envs
    dropbox = None

# Optional Dropbox config via environment variables; fall back to no Dropbox
# Define these BEFORE creating the Dash app so pages can import them during init
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

app = dash.Dash(__name__, use_pages=True,
                external_stylesheets=[dbc.themes.CERULEAN],
                suppress_callback_exceptions=True)
app.title = 'ORFEUS Data Website'

# Simple health endpoint for container orchestrators
@app.server.get("/healthz")
def _healthz():
    return {"status": "ok"}


# -------- App Shell (Navbar + Page Container) --------

def _nav_links():
    """Build nav links from Dash Pages registry, honoring 'order' and optional meta.hide_from_nav."""
    pages = [p for p in page_registry.values() if not p.get('meta', {}).get('hide_from_nav')]
    pages = sorted(pages, key=lambda p: p.get('order', 0))
    return [dbc.NavItem(dbc.NavLink(p.get('name', p['path'].strip('/').title()) or 'Home', href=p['path'], active="exact")) for p in pages]


navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand("ORFEUS Data Visualization", href="/"),
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        dbc.Collapse(dbc.Nav(_nav_links(), className="ms-auto", navbar=True),
                     id="navbar-collapse", is_open=False, navbar=True),
    ], fluid=True),
    dark=False,
    className="dbc-navbar"
)


app.layout = html.Div([
    dcc.Store(id='side_click'),
    navbar,
    html.Div(page_container, className='app-content')
])


@dash.callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"),
)
def _toggle_navbar_collapse(n, is_open):
    if n:
        return not (is_open or False)
    return is_open

