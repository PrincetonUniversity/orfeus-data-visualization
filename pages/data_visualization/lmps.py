import io
import os
import bz2
import gzip
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime
import dill as pickle
from dash import html, dcc, Input, Output, ctx
import plotly.express as px
from plotly.colors import n_colors
import plotly.graph_objects as go

import dash
import dash_bootstrap_components as dbc
from inputs.inputs import date_values_t7k, bus, branch, dbx, HAS_DROPBOX
from utils.md import load_markdown
markdown_text_lmps_overview = load_markdown('markdown', 'lmps_overview.md')
markdown_text_lmps_plot = load_markdown('markdown', 'lmps_plot.md')
dash.register_page(__name__, path='/lmpplot', name='LMPs', order=3)

# Mapbox token/style via environment, fallback to OpenStreetMap if missing
PLOT_TOKEN = os.getenv('MAPBOX_TOKEN') or os.getenv('DASH_MAPBOX_TOKEN') or None
PLOT_STYLE = os.getenv('MAPBOX_STYLE') or ('light' if PLOT_TOKEN else 'open-street-map')

html_div_lmps_overview =  html.Div(children=[

                html.H1(children='Locational Marginal Prices', className='title'),

                html.Div([
                    dcc.Markdown(children= markdown_text_lmps_overview, className='markdown'),
                ])
            ], className='app-content')



html_div_lmps = html.Div(children=[
                  dbc.Row(
                                            dbc.Col(html.H3(children='LMP Geographic Plots', className='title'))
                      , justify='start', align='start'),

                    html.Div([
                                                dcc.Markdown(children=markdown_text_lmps_plot, className='markdown'),
                    ],
                                                className='section'),

                    html.Hr(),

                    dbc.Row(
                        dbc.Col([
                            html.Label('Select Day'),
                            dcc.Dropdown(date_values_t7k[:-2], id='date_values_t7k_lmps',
                                         value=date_values_t7k[0], className='dropdown-short'),
                            html.Br()
                        ])
                    ),

                    dbc.Row(
                        dbc.Col([
                            html.Label('Select Hr'),
                            dcc.Dropdown(list(range(24)), id='hr_values_t7k_lmps',
                                         value=15, className='dropdown-short')
                        ])
                    ),

                    html.Br(),

                    dbc.Row([
                        dbc.Col(
                            dcc.Graph(id='fig_lmp_geo', className='graph-pad'))
                    ]
                        , justify='start')

                ], className='app-content')

# Dash Pages expects a module-level variable named 'layout'
layout = html.Div([
    html_div_lmps_overview,
    html_div_lmps,
])


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
                                       size_max=15, zoom=1)

    if bus_detail_hr_highcongest.shape[0] != 0:
        fig_highcongest = px.scatter_mapbox(bus_detail_hr_highcongest, lat="lat",
                                lon="lng",
                                color="LMP", opacity=0.7, size='size',
                                hover_name='Bus Name',
                                hover_data=['Bus ID', 'LMP', 'Demand',
                                            'GEN UID'],
                                size_max=15, zoom=1)
        fig.add_trace(fig_highcongest.data[0])

    if bus_detail_mismatch.shape[0] != 0:
        busids_mismatch = list(bus_detail_mismatch['Bus ID'].unique())
        line_detail_hr_mismatch = line_detail_hr[
            line_detail_hr['From Bus'].isin(busids_mismatch) |
            line_detail_hr['To Bus'].isin(busids_mismatch)]
    fig_mismatch = px.scatter_mapbox(bus_detail_mismatch, lat="lat",
                     lon="lng", color="LMP", opacity=1.0,
                     size='size',
                     hover_name='Bus Name',
                     hover_data=['Bus ID', 'LMP',
                             'Mismatch', 'Demand',
                             'GEN UID'],
                     size_max=15, zoom=1)
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

    bluepurplered = n_colors('rgb(0, 0, 255)', 'rgb(255, 0, 0)',
                             line_detail_hr_highcongest.shape[0],
                             colortype='rgb')
    # Fix decimal point imprecision
    bluepurplered[0] = 'rgb(0, 0, 255)'
    bluepurplered[-1] = 'rgb(255, 0, 0)'

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

    fig1.update_layout(title='LMPs Distribution at Hr {}, {} under Texas 7k Grid'.format(hr,
                                                                     bus_detail_hr[
                                                                         'Date'].unique()[
                                                                         0]),
                       legend=dict(x=1, y=1),
                       coloraxis_colorbar=dict(orientation="h"),
                       height=600, width=1000)

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

def build_lmp_plot_file(file_name, bus, branch):
    file_path = '/ORFEUS-Alice/data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20/{}'.format(file_name)
    df_pickle = None
    if HAS_DROPBOX and dbx is not None:
        try:
            _, res = dbx.files_download(file_path)
            byts = res.content
            # Try bz2 first, then gzip
            try:
                with io.BytesIO(byts) as stream:
                    with bz2.BZ2File(stream, 'r') as f:
                        df_pickle = pickle.load(f)
            except Exception:
                try:
                    with io.BytesIO(byts) as stream:
                        with gzip.GzipFile(fileobj=stream, mode='r') as f:
                            df_pickle = pickle.load(f)
                except Exception:
                    df_pickle = None
        except Exception:
            df_pickle = None
    if df_pickle is None:
        import os
        cwd = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(cwd, '../../'))
        local_path = os.path.join(root, 'data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20', file_name)
        if os.path.exists(local_path):
            # Try bz2 then gzip
            try:
                with bz2.BZ2File(local_path, 'r') as f:
                    df_pickle = pickle.load(f)
            except Exception:
                try:
                    with gzip.open(local_path, 'rb') as f:
                        df_pickle = pickle.load(f)
                except Exception:
                    df_pickle = None
    if df_pickle is None:
        # minimal stub
        bus_name = bus['Bus Name'].iloc[0]
        day = date_values_t7k[0] if len(date_values_t7k) > 0 else '2018-01-02'
        bus_detail = pd.DataFrame({
            'Bus': [bus_name]*24,
            'Hour': list(range(24)),
            'LMP': [0.0]*24,
            'Demand': [0.0]*24,
            'Date': [day]*24,
            'Mismatch': [0.0]*24,
        })
        uid = branch['UID'].iloc[0]
        line_detail = pd.DataFrame({
            'Line': [uid]*24,
            'Hour': list(range(24)),
            'Flow': [0.0]*24,
        })
    else:
        # Support multiple pickle schemas
        bus_detail, line_detail = _extract_bus_line(df_pickle)

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
    return bus_detail, line_detail

@dash.callback(
    Output('fig_lmp_geo', 'figure'),
    Input('date_values_t7k_lmps', 'value'),
    Input('hr_values_t7k_lmps', 'value'))
def hourly_cost_dist_rts(date, hr):
    bus_detail, line_detail = build_lmp_plot_file(file_name=date + '.p.gz',
                                                  bus=bus, branch=branch)
    fig, _ = plot_particular_hour(hr, bus_detail, line_detail)
    return fig
