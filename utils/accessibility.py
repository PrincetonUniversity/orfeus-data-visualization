"""Accessibility utilities (tables, alt representations) for visualizations.

Provides helpers to convert Plotly figures to simple HTML tables to give
screen-reader and keyboard users an alternative, sortable baseline structure.
"""
from __future__ import annotations

from typing import Any, Sequence

try:
    import plotly.graph_objects as go  # type: ignore
except Exception:  # pragma: no cover - plotly optional at import time
    go = None  # type: ignore

from dash import html  # dash.html components


def figure_to_table_html(fig: Any, max_rows: int = 50):
    """Return an HTML table (first ``max_rows`` rows per trace) for a Plotly figure.

    Supports two broad trace families used in the app:
    1. Cartesian traces (x/y)
    2. Mapbox / geo traces (lat/lon) — e.g. LMP scatter_mapbox

    For mapbox traces we also attempt to surface an associated numeric value
    (marker.color sequence, z, or customdata first column) as 'Value'. Headers
    are adapted automatically depending on whether (x,y) or (lat,lon) data are
    encountered. Mixed figures (both cartesian and geo) will union the headers.
    """
    try:
        if fig is None:
            return html.Em('No data')
        # Dash supplies dict; reconstruct Figure when plotly is available.
        if isinstance(fig, dict) and go is not None:
            try:
                fig = go.Figure(fig)  # type: ignore
            except Exception:
                # Fall back to raw dict processing later
                pass

        data_seq: Sequence = getattr(fig, 'data', []) if not isinstance(fig, dict) else fig.get('data', [])  # type: ignore
        if not data_seq:
            return html.Em('No data')

        saw_xy = False
        saw_latlon = False
        rows_xy: list[list[Any]] = []  # [Trace, Index, X, Y]
        rows_latlon: list[list[Any]] = []  # [Trace, Index, Lat, Lon, Value]

        for ti, tr in enumerate(data_seq):
            if isinstance(tr, dict):
                xs = tr.get('x') or []
                ys = tr.get('y') or []
                lats = tr.get('lat') or []
                lons = tr.get('lon') or []
                marker = tr.get('marker') or {}
                name = tr.get('name') or f'Trace {ti+1}'
                customdata = tr.get('customdata') or []
                zvals = tr.get('z') or []
            else:  # graph objects trace
                xs = getattr(tr, 'x', []) or []
                ys = getattr(tr, 'y', []) or []
                lats = getattr(tr, 'lat', []) or []
                lons = getattr(tr, 'lon', []) or []
                marker = getattr(tr, 'marker', None)
                name = getattr(tr, 'name', None) or f'Trace {ti+1}'
                customdata = getattr(tr, 'customdata', []) or []
                zvals = getattr(tr, 'z', []) or []
            # Prefer cartesian if both provided.
            if xs and ys:
                saw_xy = True
                limit = min(len(xs), len(ys), max_rows)
                for i in range(limit):
                    rows_xy.append([name, i, xs[i], ys[i]])
            elif lats and lons:
                saw_latlon = True
                limit = min(len(lats), len(lons), max_rows)
                # Derive value column
                values = []
                try:
                    # marker.color may be scalar or sequence
                    colors = marker.get('color') if isinstance(marker, dict) else getattr(marker, 'color', None)
                    if isinstance(colors, (list, tuple)) and len(colors) == len(lats):
                        values = list(colors)
                    elif isinstance(zvals, (list, tuple)) and len(zvals) == len(lats):
                        values = list(zvals)
                    elif isinstance(customdata, (list, tuple)) and customdata and isinstance(customdata[0], (list, tuple)):
                        # Take first column
                        values = [cd[0] if cd else '' for cd in customdata[:len(lats)]]
                except Exception:
                    values = []
                for i in range(limit):
                    val = values[i] if i < len(values) else ''
                    rows_latlon.append([name, i, lats[i], lons[i], val])

        if not rows_xy and not rows_latlon:
            return html.Em('No data')

        # Compose headers / rows based on what we saw.
        # If both families present, we'll output XY rows then LAT/LON rows with a blank separator row.
        table_sections = []
        total_rows = 0
        if rows_xy:
            table_sections.append([
                html.Thead(html.Tr([html.Th(h) for h in ['Trace', 'Index', 'X', 'Y']])),
                html.Tbody([html.Tr([html.Td(c) for c in r]) for r in rows_xy])
            ])
            total_rows += len(rows_xy)
        if rows_latlon:
            # Add a separator row if both present for clarity (visually minimal, assistive tech will just see another row).
            if rows_xy:
                sep = html.Tbody([html.Tr([html.Td(html.Em('—')) for _ in range(5)])])
            else:
                sep = None
            section = [
                html.Thead(html.Tr([html.Th(h) for h in ['Trace', 'Index', 'Lat', 'Lon', 'Value']])),
                html.Tbody([html.Tr([html.Td(c) for c in r]) for r in rows_latlon])
            ]
            if sep:
                table_sections.append([sep])
            table_sections.append(section)
            total_rows += len(rows_latlon)

        # Flatten sections
        children = []
        for sec in table_sections:
            children.extend(sec)

        return html.Table(children, className='vis-table', **{"aria-rowcount": total_rows})
    except Exception:
        return html.Em('Table error')

__all__ = ["figure_to_table_html"]
