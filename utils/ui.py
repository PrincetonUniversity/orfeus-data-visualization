"""UI shim to centralize common Dash/DBC imports.

Usage in pages/modules:
    from utils.ui import dash, dcc, html, Input, Output, State, ctx, page_registry, page_container, dbc
"""

import dash
from dash import dcc, html, Input, Output, State, ctx, page_registry, page_container
import dash_bootstrap_components as dbc

__all__ = [
    "dash",
    "dcc",
    "html",
    "Input",
    "Output",
    "State",
    "ctx",
    "page_registry",
    "page_container",
    "dbc",
]
