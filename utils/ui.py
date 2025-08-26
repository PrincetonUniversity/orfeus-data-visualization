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
    "COLORBLIND_PALETTE",
    "PATTERN_SHAPES",
]

# Colorblind-friendly palette (Okabe-Ito)
COLORBLIND_PALETTE = [
    '#000000',  # black
    '#E69F00',  # orange
    '#56B4E9',  # sky blue
    '#009E73',  # bluish green
    '#F0E442',  # yellow
    '#0072B2',  # blue
    '#D55E00',  # vermillion
    '#CC79A7',  # reddish purple
]

# Fallback pattern shapes list (Plotly marker symbols for differentiation)
PATTERN_SHAPES = [
    'circle', 'square', 'diamond', 'cross', 'x', 'triangle-up', 'triangle-down',
]
