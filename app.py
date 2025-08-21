from pathlib import Path
import os
from urllib.parse import parse_qs

from utils.ui import dash, dcc, html, Input, Output, State, page_registry, page_container, dbc
from utils.config import SETTINGS
from utils.dropbox_client import get_dropbox

# Dropbox client (lazy-verified). Expose on the module for other modules if needed.
dbx, HAS_DROPBOX = get_dropbox()

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


banner = None
if getattr(SETTINGS, "stub_mode", False):
    banner = dbc.Alert(
        "Stub Mode: Data shown may be placeholders for CI/testing and/or missing data directory.",
        color="warning",
        className="m-0 py-1 px-2 w-100 text-center",
        style={"borderRadius": 0}
    )

navbar_children = [
    dbc.NavbarBrand("ORFEUS Data Visualization", href="/"),
    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
    dbc.Collapse(dbc.Nav(_nav_links(), className="ms-auto", navbar=True),
                 id="navbar-collapse", is_open=False, navbar=True),
]
# Wrap navbar so we can hide it in embed mode
navbar = dbc.Navbar(
    dbc.Container(navbar_children, fluid=True),
    dark=False,
    className="dbc-navbar",
)


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id='side_click'),
    dcc.Store(id='embed-store', data=False),
    html.Div(navbar, id="navbar-wrapper"),
    banner if banner else html.Div(),
    html.Section(page_container, className='app-content')
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


@dash.callback(
    Output('embed-store', 'data'),
    Input('url', 'search'),
)
def _parse_embed_flag(search: str | None):
    # Extract embed query parameter; accept 1|true|yes|on (case-insensitive)
    try:
        q = parse_qs((search or '').lstrip('?'))
        val = (q.get('embed', [None])[0] or '').strip().lower()
        return val in ('1', 'true', 'yes', 'on')
    except Exception:
        return False


@dash.callback(
    Output('navbar-wrapper', 'style'),
    Input('embed-store', 'data'),
)
def _toggle_navbar_visibility(embed: bool):
    return {'display': 'none'} if embed else {}


if __name__ == "__main__":
    # Local development entrypoint
    app.run_server(debug=True, port=SETTINGS.port)

