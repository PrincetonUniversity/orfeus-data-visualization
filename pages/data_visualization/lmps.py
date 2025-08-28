import os
import io
import bz2
import gzip
from datetime import date, timedelta, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pickle
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import n_colors

from utils.ui import html, dcc, Input, Output, State, ctx, dbc, dash
from utils.accessibility import figure_to_table_html
from utils.config import SETTINGS
from inputs.inputs import date_values_t7k, bus, branch, dbx, HAS_DROPBOX
from utils.md import load_markdown, extract_first_h1
markdown_text_lmps_overview = load_markdown('markdown', 'lmps_overview.md')
markdown_text_lmps_plot = load_markdown('markdown', 'lmps_plot.md')
LMPS_TITLE = extract_first_h1(markdown_text_lmps_overview, fallback='LMPs')
dash.register_page(__name__, path='/lmpplot', name='LMPs', order=3, title=LMPS_TITLE)

# Mapbox token/style via environment, fallback to OpenStreetMap if missing
PLOT_TOKEN = SETTINGS.mapbox_token
PLOT_STYLE = SETTINGS.mapbox_style or ('light' if PLOT_TOKEN else 'open-street-map')
LMP_DEBUG = os.getenv('LMP_DEBUG', '0').strip() in ('1', 'true', 'True', 'yes', 'on')


def _prepare_pandas_compat():
    """Install aliases for old pandas module paths used in legacy pickles.

    Some historical pickles reference 'pandas.core.indexes.numeric' which was
    removed/reshuffled in pandas 2.x. We alias it to 'pandas.core.indexes.base'
    so unpickling succeeds. Extend as needed for other legacy paths.
    """
    try:
        import sys, types
        import pandas as pd  # noqa: F401
        try:
            import pandas as pd  # type: ignore
            import pandas.core.indexes.base as base  # type: ignore
            # Create/refresh alias module
            if 'pandas.core.indexes.numeric' not in sys.modules:
                m = types.ModuleType('pandas.core.indexes.numeric')
                sys.modules['pandas.core.indexes.numeric'] = m
            else:
                m = sys.modules['pandas.core.indexes.numeric']
            # Copy base attributes
            m.__dict__.update(base.__dict__)
            # Provide legacy index class names expected by old pickles
            for legacy in ('Int64Index', 'UInt64Index', 'Float64Index'):
                try:
                    setattr(base, legacy, pd.Index)
                except Exception:
                    pass
                try:
                    setattr(m, legacy, pd.Index)
                except Exception:
                    pass
            if LMP_DEBUG:
                print('[LMP] Installed pandas compat aliases for legacy index classes')
        except Exception as e:
            if LMP_DEBUG:
                print(f'[LMP] pandas compat alias failed: {e}')
    except Exception:
        pass

html_div_lmps_overview =  html.Section(children=[
                html.Div([
                    dcc.Markdown(children= markdown_text_lmps_overview, className='markdown', id='lmps-markdown-overview'),
                ], className='section', id='lmps-overview-section')
            ], className='app-content')



html_div_lmps = html.Section(children=[
                  dbc.Row(
                                            dbc.Col(html.H1(children='LMP Geographic Plots', className='title', id='lmps-title'))
                      , justify='start', align='start', id='lmps-title-row'),

                    html.Div([
                        dcc.Markdown(children=markdown_text_lmps_plot, className='markdown', id='lmps-markdown-plot'),
                    ], className='section', id='lmps-plot-section'),


                    dbc.Row([
                        dbc.Col([
                            html.Label([
                                'Select Day',
                                dcc.Dropdown(
                                    date_values_t7k[:-2],
                                    id='date_values_t7k_lmps',
                                    value=date_values_t7k[0],
                                    className='dropdown-short'
                                )
                            ]),
                            html.Div(id='live-date_values_t7k_lmps', className='visually-hidden', **{'aria-live':'polite', 'role': 'status'})
                        ], xs=12, md=6, lg=4),
                        dbc.Col([
                            html.Label([
                                'Select Hr',
                                dcc.Dropdown(
                                    list(range(24)),
                                    id='hr_values_t7k_lmps',
                                    value=15,
                                    className='dropdown-short'
                                )
                            ]),
                            html.Div(id='live-hr_values_t7k_lmps', className='visually-hidden', **{'aria-live':'polite', 'role': 'status'})
                        ], xs=12, md=6, lg=3),
                    ], className='controls-row'),

                    html.Br(),

                    dbc.Row([
                        dbc.Col([
                            html.Figure([
                                dcc.Graph(id='fig_lmp_geo', className='graph-pad graph-map', config={"responsive": True}),
                                html.Figcaption(id='fig_lmp_geo-caption', className='vis-caption', tabIndex=0)
                            ], className='graph-figure', role='group', **{"aria-labelledby": 'fig_lmp_geo-caption'}),
                            html.Details([
                                html.Summary("Data table", **{"aria-controls": "fig_lmp_geo-table"}),
                                html.Div(id='fig_lmp_geo-table', className='vis-table-wrapper')
                            ], open=False)
                        ])
                    ], justify='start')

                ], className='app-content')

# Dash Pages expects a module-level variable named 'layout'
layout = html.Section([
    html_div_lmps_overview,
    html_div_lmps,
    dcc.Location(id='url-lmps', refresh=False),
])


# Live region announcers for screen readers (polite updates on selection changes)
@dash.callback(
    Output('live-date_values_t7k_lmps', 'children'),
    Input('date_values_t7k_lmps', 'value')
)
def _announce_lmp_day(val):  # noqa: D401
    if not val:
        return ''
    return f"Day selected {val}"  # Short phrase for SR


@dash.callback(
    Output('live-hr_values_t7k_lmps', 'children'),
    Input('hr_values_t7k_lmps', 'value')
)
def _announce_lmp_hour(val):  # noqa: D401
    if val is None:
        return ''
    return f"Hour selected {val}"  # Short phrase for SR


def plot_particular_hour(hr, bus_detail, line_detail):
    # Manually Set up Discrete Color Scale
    # Filter to hour and work on copies to avoid SettingWithCopy warnings
    bus_detail_hr = bus_detail.loc[bus_detail['Hour'] == hr].copy()
    line_detail_hr = line_detail.loc[line_detail['Hour'] == hr].copy()

    line_detail_hr['Flow'] = line_detail_hr['Flow'].apply(
        lambda x: round(x, 2))
    line_detail_hr['UID_Flow'] = line_detail_hr['UID'].astype(str) + ': ' + \
                                 line_detail_hr['Flow'].astype(str)

    # Ensure numeric and valid coordinates to avoid Mapbox extent warnings
    bus_detail_hr['lat'] = pd.to_numeric(bus_detail_hr['lat'], errors='coerce')
    bus_detail_hr['lng'] = pd.to_numeric(bus_detail_hr['lng'], errors='coerce')
    bus_detail_hr = bus_detail_hr.dropna(subset=['lat', 'lng'])
    bus_detail_hr = bus_detail_hr[(bus_detail_hr['lat'].between(-90, 90)) &
                                   (bus_detail_hr['lng'].between(-180, 180))]

    # If no bus data for this hour, return an empty map with a helpful title
    if bus_detail_hr.empty:
        fig_empty = go.Figure()
        fig_empty.update_layout(
            hovermode='closest',
            mapbox=dict(
                accesstoken=PLOT_TOKEN,
                style=PLOT_STYLE,
                bearing=0,
                center=go.layout.mapbox.Center(lat=31, lon=-99.9018),
                pitch=0,
                zoom=4.5,
            ),
            title=f"No data available for Hr {hr}",
            legend=dict(orientation='h', x=0, y=-0.1),
            margin=dict(l=10, r=10, t=40, b=40),
            height=None, width=None
        )
        return fig_empty, line_detail_hr.iloc[0:0]

    bus_detail_hr['ABS LMP'] = bus_detail_hr['LMP'].apply(lambda x: abs(x))
    # The size would vary with LMP
    bus_detail_hr['size'] = bus_detail_hr['ABS LMP']

    size_max_ = bus_detail_hr['size'].max()
    # Emphasize the extreme case in the plot by increasing size where prices <= -1e4
    bus_detail_hr.loc[bus_detail_hr['LMP'] < 0, 'size'] = size_max_
    #     bus_detail_hr.loc[bus_detail_hr['LMP'] >= 1000, 'size'] = size_max_

    #     max_lmp_hr = bus_detail_hr['ABS LMP'].max()
    #     min_lmp_hr = bus_detail_hr['ABS LMP'].min()

    #     if (max_lmp_hr-min_lmp_hr) != 0:
    #          bus_detail_hr['size'] = 5+(bus_detail_hr['ABS LMP']-min_lmp_hr)/(max_lmp_hr-min_lmp_hr)
    #         print(bus_detail_hr['size'])
    #     else:
    #         print('LMP Prices are Same across all Busses')
    #         bus_detail_hr['size'] = 5

    bus_detail_mismatch = bus_detail_hr.loc[bus_detail_hr['Mismatch'] != 0]

    # separate high congest from low congest
    line_detail_hr_highcongest = line_detail_hr[
        line_detail_hr['CongestionRatio'] >= 0.98] \
        .reset_index().sort_values(by=['CongestionRatio'])
    # Filter invalid coordinates for line endpoints
    for col in ['From Bus Lat', 'From Bus Lng', 'To Bus Lat', 'To Bus Lng']:
        line_detail_hr_highcongest[col] = pd.to_numeric(line_detail_hr_highcongest[col], errors='coerce')
    line_detail_hr_highcongest = line_detail_hr_highcongest.dropna(subset=['From Bus Lat', 'From Bus Lng', 'To Bus Lat', 'To Bus Lng'])
    line_detail_hr_highcongest = line_detail_hr_highcongest[
        line_detail_hr_highcongest['From Bus Lat'].between(-90, 90) &
        line_detail_hr_highcongest['To Bus Lat'].between(-90, 90) &
        line_detail_hr_highcongest['From Bus Lng'].between(-180, 180) &
        line_detail_hr_highcongest['To Bus Lng'].between(-180, 180)
    ]

    # Cap the number of rendered congested lines to reduce geometry load
    try:
        max_lines = int(os.getenv('LMP_MAX_LINE_TRACES', '500'))
    except Exception:
        max_lines = 500
    if line_detail_hr_highcongest.shape[0] > max_lines:
        # Keep the most congested lines (highest ratio)
        line_detail_hr_highcongest = line_detail_hr_highcongest.tail(max_lines)

    bus_highcongest = set(line_detail_hr_highcongest['To Bus'].unique()).union(
        set(line_detail_hr_highcongest['From Bus'].unique()))
    bus_detail_hr_highcongest = bus_detail_hr[
        bus_detail_hr['Bus ID'].isin(bus_highcongest)]
    bus_detail_hr_lowcongest = bus_detail_hr[
        ~bus_detail_hr['Bus ID'].isin(bus_highcongest)]

    #     print('Maximum Congestion Ratio')
    #     print(line_detail_hr_highcongest['CongestionRatio'][0])
    # plot highcongest before lowcongest so we could hover to see highcongest info even if these buses are in the same location
    fig = px.scatter_mapbox(bus_detail_hr_lowcongest, lat="lat",
                                       lon="lng", color="LMP", opacity=0.7,
                                       size='size',
                                       hover_name='Bus Name',
                                       hover_data=['Bus ID', 'LMP',
                                                   'Demand',
                                                   'GEN UID'],
                                       size_max=3, zoom=1)

    if bus_detail_hr_highcongest.shape[0] != 0:
        fig_highcongest = px.scatter_mapbox(bus_detail_hr_highcongest, lat="lat",
                                lon="lng",
                                color="LMP", opacity=0.7, size='size',
                                hover_name='Bus Name',
                                hover_data=['Bus ID', 'LMP', 'Demand',
                                            'GEN UID'],
                                size_max=3, zoom=1)
        fig.add_trace(fig_highcongest.data[0])

    if bus_detail_mismatch.shape[0] != 0:
        busids_mismatch = list(bus_detail_mismatch['Bus ID'].unique())
        line_detail_hr_mismatch = line_detail_hr[
            line_detail_hr['From Bus'].isin(busids_mismatch) |
            line_detail_hr['To Bus'].isin(busids_mismatch)]
    if not bus_detail_mismatch.empty:
        fig_mismatch = px.scatter_mapbox(bus_detail_mismatch, lat="lat",
                         lon="lng", color="LMP", opacity=1.0,
                         size='size',
                         hover_name='Bus Name',
                         hover_data=['Bus ID', 'LMP',
                                 'Mismatch', 'Demand',
                                 'GEN UID'],
                         size_max=3, zoom=1)
        if len(fig_mismatch.data) > 0:
            fig.add_trace(fig_mismatch.data[0])

    fig.update_layout(
        hovermode='closest',
        mapbox=dict(
            accesstoken=PLOT_TOKEN,
            style=PLOT_STYLE,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=31,
                lon=-99.9018
            ),
            pitch=0,
            zoom=4.5,
     )
    )

    # need to consider direction:the bus line is starting point
    fig1 = go.Figure(fig)

    # plot high congestion bus so we could hover them even if they overlap with other buses in same location
    # Plot Transmission Lines Related to Mismatch Buses

    # Build a colorscale for congested lines; avoid n_colors for 0 or 1 (division by zero)
    num_lines = int(line_detail_hr_highcongest.shape[0])
    if num_lines >= 2:
        bluepurplered = n_colors('rgb(0, 0, 255)', 'rgb(255, 0, 0)', num_lines, colortype='rgb')
        # Fix decimal point imprecision at the ends
        bluepurplered[0] = 'rgb(0, 0, 255)'
        bluepurplered[-1] = 'rgb(255, 0, 0)'
    elif num_lines == 1:
        bluepurplered = ['rgb(255, 0, 0)']
    else:
        bluepurplered = []

    # Plot line details
    if line_detail_hr_highcongest.shape[0] != 0:
        for idx, line_detail_hr_row in line_detail_hr_highcongest.iterrows():
            fromlmp = bus_detail_hr[
                bus_detail_hr['Bus ID'] == line_detail_hr_row['From Bus']][
                'LMP'].values[0]
            tolmp = \
                bus_detail_hr[
                    bus_detail_hr['Bus ID'] == line_detail_hr_row['To Bus']][
                    'LMP'].values[0]

            fig1.add_trace(go.Scattermapbox(
                mode="lines",
                lat=line_detail_hr_row[['From Bus Lat', 'To Bus Lat']].values,
                lon=line_detail_hr_row[['From Bus Lng', 'To Bus Lng']].values,
                hovertemplate=line_detail_hr_row[
                                  'UID_Flow'] + ' <br>From: ' + str(
                    line_detail_hr_row['From Bus']) +
                              '<br>To:' + str(line_detail_hr_row['To Bus']) +
                              '<extra>CongesRatio={CongesRatio:.2f}</extra>'.format(
                                  CongesRatio=line_detail_hr_row[
                                      'CongestionRatio']) +
                              '<extra><br>FromLMP={FromLMP:.2f}</extra>'.format(
                                  FromLMP=fromlmp) +
                              '<extra><br>ToLMP={ToLMP:.2f}</extra>'.format(
                                  ToLMP=tolmp),
                line=dict(
                    width=5 + float(line_detail_hr_row['CongestionRatio']) * 10,
                    color=bluepurplered[-1]), opacity=1,
                name='Congested Lines', legendgroup='Congested Lines'
            ))

    date_label = None
    try:
        date_label = bus_detail_hr['Date'].iloc[0]
    except Exception:
        date_label = ''
    fig1.update_layout(
        title='LMPs Distribution at Hr {}, {} under Texas 7k Grid'.format(hr, date_label),
        legend=dict(orientation='h', x=0, y=-0.1),
        coloraxis_colorbar=dict(orientation="h"),
        margin=dict(l=10, r=10, t=40, b=40),
        height=None, width=None
    )

    # Subtle note when there are no congested lines to plot
    if int(line_detail_hr_highcongest.shape[0]) == 0:
        fig1.add_annotation(
            text="No congested lines for this hour",
            xref="paper",
            yref="paper",
            x=1,
            y=0,
            xanchor="right",
            yanchor="bottom",
            font=dict(size=11, color="#666"),
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor="rgba(0,0,0,0)",
            showarrow=False,
        )

    for i in range(line_detail_hr_highcongest.shape[0]):
        fig1.data[-(1 + i)].showlegend = False

    if bus_detail_hr_highcongest.shape[0] != 0:
        fig1.data[0].name = 'Buses with No Congested Lines Connected to'
        fig1.data[1].name = 'Buses with Congested Lines Connected to'
        fig1.data[0].showlegend = True
        fig1.data[1].showlegend = True
        if bus_detail_mismatch.shape[0] != 0:
            fig1.data[2].name = 'Buses with Mismatch in Demand and Supply'
            fig1.data[2].showlegend = True
    else:
        fig1.data[0].name = 'Buses'
        fig1.data[0].showlegend = True
        if bus_detail_mismatch.shape[0] != 0:
            fig1.data[1].name = 'Buses with Mismatch in Demand and Supply'
            fig1.data[1].showlegend = True
    fig1.data[-1].showlegend = True
    return fig1, line_detail_hr_highcongest


def _extract_bus_line(obj):
    """Return (bus_detail_df, line_detail_df) from a pickle object with varying keys.

    Accepts common variants: 'bus_detail'|'bus'|'bus_df'|'buses' and
    'line_detail'|'line'|'line_df'|'lines'. Avoids DataFrame truthiness.
    """
    bus_df = None
    for k in ("bus_detail", "bus", "bus_df", "buses"):
        val = obj.get(k)
        if isinstance(val, pd.DataFrame):
            bus_df = val.reset_index()
            break
    line_df = None
    for k in ("line_detail", "line", "line_df", "lines"):
        val = obj.get(k)
        if isinstance(val, pd.DataFrame):
            line_df = val.reset_index()
            break
    if bus_df is None or line_df is None:
        raise ValueError("Pickle missing required bus/line DataFrames")
    return bus_df, line_df

def _resolve_case_insensitive(p: str) -> str | None:
    path = Path(p)
    if path.exists():
        if LMP_DEBUG:
            print(f"[LMP] Found path: {path}")
        return str(path)
    parent = path.parent
    try:
        target = path.name.lower()
        for name in os.listdir(parent):
            if name.lower() == target:
                cand = parent / name
                if cand.exists():
                    if LMP_DEBUG:
                        print(f"[LMP] Case-insensitive resolved: {cand}")
                    return str(cand)
    except Exception:
        pass
    return None


def _load_pickle_from_bytes(byts: bytes):
    _prepare_pandas_compat()
    # Try bz2, then gzip, with standard pickle; fallback to dill if installed.
    # Return None if all attempts fail.
    try:
        with io.BytesIO(byts) as stream:
            with bz2.BZ2File(stream, 'r') as f:
                return pickle.load(f)
    except Exception as e:
        if LMP_DEBUG:
            print(f"[LMP] bz2 std pickle load failed: {e}")
        pass
    try:
        with io.BytesIO(byts) as stream:
            with gzip.GzipFile(fileobj=stream, mode='r') as f:
                return pickle.load(f)
    except Exception as e:
        if LMP_DEBUG:
            print(f"[LMP] gzip std pickle load failed: {e}")
        pass
    # dill with gzip
    try:
        import dill as dill_pickle  # optional fallback
        with io.BytesIO(byts) as stream:
            with gzip.GzipFile(fileobj=stream, mode='r') as f:
                return dill_pickle.load(f)
    except Exception as e:
        if LMP_DEBUG:
            print(f"[LMP] gzip dill load failed: {e}")
        pass
    # dill with bz2
    try:
        import dill as dill_pickle
        with io.BytesIO(byts) as stream:
            with bz2.BZ2File(stream, 'r') as f:
                return dill_pickle.load(f)
    except Exception as e:
        if LMP_DEBUG:
            print(f"[LMP] bz2 dill load failed: {e}")
        return None


def build_lmp_plot_file(file_name, bus, branch):
    file_path = '/ORFEUS-Alice/data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20/{}'.format(file_name)
    df_pickle = None
    if HAS_DROPBOX and dbx is not None:
        try:
            _, res = dbx.files_download(file_path)
            byts = res.content
            df_pickle = _load_pickle_from_bytes(byts)
            if LMP_DEBUG:
                print(f"[LMP] Loaded from Dropbox: {file_path}: {df_pickle is not None}")
        except Exception as e:
            if LMP_DEBUG:
                print(f"[LMP] Dropbox load failed for {file_path}: {e}")
            df_pickle = None
    if df_pickle is None:
        root = str(SETTINGS.root_dir)
        lmp_dir = os.path.join(root, 'data', 'lmps_data_visualization', 't7k_v0.4.0-a2_rsvf-20')
        local_path = os.path.join(lmp_dir, file_name)
        # Resolve case-insensitive if needed
        resolved = _resolve_case_insensitive(local_path)
        if resolved is None:
            # Also try resolving the directory case-insensitively, then join filename again
            dir_resolved = _resolve_case_insensitive(lmp_dir)
            if dir_resolved is not None:
                resolved = _resolve_case_insensitive(os.path.join(dir_resolved, file_name))
        if LMP_DEBUG:
            print(f"[LMP] Local path candidate: {resolved}")
        if resolved is not None and os.path.exists(resolved):
            _prepare_pandas_compat()
            # Prefer pandas.read_pickle with compression=infer when reading from path
            try:
                df_pickle = pd.read_pickle(resolved, compression='infer')
                if LMP_DEBUG:
                    print(f"[LMP] Loaded via pandas.read_pickle: {resolved}")
            except Exception:
                # Fallback to manual gzip/bz2
                try:
                    with bz2.BZ2File(resolved, 'r') as f:
                        df_pickle = pickle.load(f)
                    if LMP_DEBUG:
                        print(f"[LMP] Loaded via bz2 std pickle: {resolved}")
                except Exception:
                    try:
                        with gzip.open(resolved, 'rb') as f:
                            df_pickle = pickle.load(f)
                        if LMP_DEBUG:
                            print(f"[LMP] Loaded via gzip std pickle: {resolved}")
                    except Exception:
                        # Final fallback using dill if available
                        try:
                            import dill as dill_pickle
                            with gzip.open(resolved, 'rb') as f:
                                df_pickle = dill_pickle.load(f)
                            if LMP_DEBUG:
                                print(f"[LMP] Loaded via gzip dill: {resolved}")
                        except Exception:
                            try:
                                import dill as dill_pickle
                                with bz2.BZ2File(resolved, 'r') as f:
                                    df_pickle = dill_pickle.load(f)
                                if LMP_DEBUG:
                                    print(f"[LMP] Loaded via bz2 dill: {resolved}")
                            except Exception:
                                if LMP_DEBUG:
                                    print(f"[LMP] All local load attempts failed for {resolved}")
                                df_pickle = None
    if df_pickle is None:
        # minimal stub
        day = date_values_t7k[0] if len(date_values_t7k) > 0 else '2018-01-02'
        # If grid data is missing (as in CI), synthesize a small, valid dataset
        grid_available = (
            isinstance(bus, pd.DataFrame) and not bus.empty and 'Bus Name' in bus.columns
            and isinstance(branch, pd.DataFrame) and not branch.empty and 'UID' in branch.columns
        )
        if grid_available:
            bus_name = bus['Bus Name'].iloc[0]
            uid = branch['UID'].iloc[0]
        else:
            bus_name = 'Stub Bus'
            uid = 'L-1'

        bus_detail = pd.DataFrame({
            'Bus': [bus_name]*24,
            'Hour': list(range(24)),
            'LMP': [0.0]*24,
            'Demand': [0.0]*24,
            'Date': [day]*24,
            'Mismatch': [0.0]*24,
        })
        line_detail = pd.DataFrame({
            'Line': [uid]*24,
            'Hour': list(range(24)),
            'Flow': [0.0]*24,
        })

        # If no grid, attach minimal geometry/ids so plotting works and skip merges
        if not grid_available:
            # Provide coordinates roughly centered in Texas
            lat_c, lng_c = 31.0, -99.9018
            bus_detail['Bus Name'] = bus_name
            bus_detail['Bus ID'] = 1
            bus_detail['lat'] = lat_c
            bus_detail['lng'] = lng_c
            bus_detail['GEN UID'] = 'Not Gen'

            line_detail['UID'] = uid
            line_detail['From Bus'] = 1
            line_detail['To Bus'] = 1
            line_detail['From Bus Lat'] = lat_c
            line_detail['From Bus Lng'] = lng_c
            line_detail['To Bus Lat'] = lat_c
            line_detail['To Bus Lng'] = lng_c
            line_detail['CongestionRatio'] = 0.0
            return bus_detail, line_detail
    else:
        # Support multiple pickle schemas
        bus_detail, line_detail = _extract_bus_line(df_pickle)

    # Attempt to enrich with grid metadata; gracefully fallback if not available
    try:
        line_detail = pd.merge(line_detail, branch[['UID', 'From Bus', 'To Bus',
                                                    'From Name', 'To Name',
                                                    'Cont Rating']],
                               left_on='Line', right_on='UID')
        line_detail['CongestionRatio'] = line_detail['Flow'].apply(
            lambda x: abs(x)) / line_detail['Cont Rating']

        bus_detail = pd.merge(bus_detail, bus[
            ['Bus ID', 'lat', 'lng', 'Zone', 'Sub Name', 'Bus Name', 'Area',
             'GEN UID']],
                              left_on='Bus', right_on='Bus Name')

        busid_lat = dict(zip(bus_detail['Bus ID'], bus_detail['lat']))
        busid_lng = dict(zip(bus_detail['Bus ID'], bus_detail['lng']))
        line_detail['To Bus Lat'] = line_detail['To Bus'].apply(
            lambda x: busid_lat[x])
        line_detail['To Bus Lng'] = line_detail['To Bus'].apply(
            lambda x: busid_lng[x])
        line_detail['From Bus Lat'] = line_detail['From Bus'].apply(
            lambda x: busid_lat[x])
        line_detail['From Bus Lng'] = line_detail['From Bus'].apply(
            lambda x: busid_lng[x])
    except Exception:
        # Provide minimal geometry if merging fails
        if 'UID' not in line_detail.columns and 'Line' in line_detail.columns:
            line_detail['UID'] = line_detail['Line']
        lat_c, lng_c = 31.0, -99.9018
        for col, val in [
            ('From Bus Lat', lat_c), ('From Bus Lng', lng_c),
            ('To Bus Lat', lat_c), ('To Bus Lng', lng_c)
        ]:
            if col not in line_detail.columns:
                line_detail[col] = val
        if 'CongestionRatio' not in line_detail.columns:
            line_detail['CongestionRatio'] = 0.0
        if 'lat' not in bus_detail.columns:
            bus_detail['lat'] = lat_c
        if 'lng' not in bus_detail.columns:
            bus_detail['lng'] = lng_c
    return bus_detail, line_detail

@dash.callback(
    Output('fig_lmp_geo', 'figure'),
    Output('fig_lmp_geo-caption', 'children'),
    Input('date_values_t7k_lmps', 'value'),
    Input('hr_values_t7k_lmps', 'value'),
    Input('url-lmps', 'search'),
    State('embed-store', 'data'))
def hourly_cost_dist_rts(date, hr, search, embed):
    bus_detail, line_detail = build_lmp_plot_file(file_name=date + '.p.gz',
                                                  bus=bus, branch=branch)
    fig, _ = plot_particular_hour(hr, bus_detail, line_detail)
    if embed:
        try:
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), width=None, height=None)
            if 'legend' in fig.layout and fig.layout.legend:
                fig.update_layout(legend=dict(orientation='h', x=0, y=-0.1))
        except Exception:
            pass
        # Optionally hide the visualization title if showtitle=false
        try:
            from urllib.parse import parse_qs
            q = parse_qs((search or '').lstrip('?'))
            sval = (q.get('showtitle', [None])[0] or '').strip().lower()
            showtitle = not (sval in ('0', 'false', 'no', 'off'))
            if not showtitle:
                fig.update_layout(title=None)
        except Exception:
            pass
    # Build accessible caption summarizing key stats
    caption = f"LMP geographic distribution for hour {hr} on {date}."
    try:
        if isinstance(bus_detail, pd.DataFrame) and not bus_detail.empty and 'LMP' in bus_detail.columns:
            lmp_vals = pd.to_numeric(bus_detail['LMP'], errors='coerce').dropna().tolist()
            if lmp_vals:
                mn = min(lmp_vals); mx = max(lmp_vals)
                caption += f" Buses: {len(bus_detail)}; LMP min {mn:.2f}, max {mx:.2f}."
        if isinstance(line_detail, pd.DataFrame) and 'CongestionRatio' in line_detail.columns:
            congested = (line_detail['CongestionRatio'] >= 0.98).sum()
            caption += f" Congested lines (>=98% rating): {congested}."
        if 'title' in fig.layout and fig.layout.title:
            caption += f" Title: {fig.layout.title.text}."
    except Exception:
        pass
    return fig, caption


@dash.callback(
    Output('fig_lmp_geo-table', 'children'),
    Input('fig_lmp_geo', 'figure')
)
def _update_lmp_table(fig_json):
    try:
        return figure_to_table_html(fig_json)
    except Exception:
        return html.Em('Unavailable')


@dash.callback(
    Output('lmps-overview-section', 'style'),
    Output('lmps-plot-section', 'style'),
    Output('lmps-title', 'style'),
    Output('lmps-title-row', 'style'),
    Input('url-lmps', 'search'),
)
def _lmps_toggle_embed(search):
    try:
        from urllib.parse import parse_qs
        q = parse_qs((search or '').lstrip('?'))
        val = (q.get('embed', [None])[0] or '').strip().lower()
        embed = val in ('1', 'true', 'yes', 'on')
    except Exception:
        embed = False
    style_hide = {'display': 'none'} if embed else {}
    # Determine showtitle override
    try:
        from urllib.parse import parse_qs
        q = parse_qs((search or '').lstrip('?'))
        sval = (q.get('showtitle', [None])[0] or '').strip().lower()
        showtitle = not (sval in ('0', 'false', 'no', 'off'))
    except Exception:
        showtitle = True
    title_style = {} if (not embed or showtitle) else {'display': 'none'}
    row_style = title_style
    return style_hide, style_hide, title_style, row_style
