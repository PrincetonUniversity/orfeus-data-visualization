import io
import os
import glob
import numpy as np
import pandas as pd
from datetime import timedelta, datetime
from utils.ui import html, dcc, Input, Output, State, dbc, dash
from utils.accessibility import figure_to_table_html
import plotly.express as px
import plotly.graph_objects as go

from inputs.inputs import date_values_rts, date_values_t7k, energy_types, energy_types_asset_ids_rts_csv, energy_types_asset_ids_t7k_csv, ROOT_DIR, dbx, HAS_DROPBOX
from utils.config import SETTINGS
from utils.md import load_markdown, extract_first_h1
markdown_text_scenario = load_markdown('markdown', 'scenarios.md')
SCENARIOS_TITLE = extract_first_h1(markdown_text_scenario, fallback='Scenarios')
dash.register_page(__name__, path='/scenariovisualize', name='Scenarios', order=1)

# Optional local PGScen scenarios directory (from another repo)
PGSCEN_DIR = str(SETTINGS.pgscen_dir)

def _try_build_fig_from_pgscen(version: str, day: str, energy_type: str):
    """Try to build a scenarios figure from local PGScen CSV.GZ files.
    Returns a plotly figure or None on failure.
    """
    year = 2018 if version.lower() in ('t7k', 'texast7k', 'texas7k') else 2020
    # Prefer notuning folder
    preferred = [
        os.path.join(PGSCEN_DIR, 'notuning', f"varios_{energy_type}_{year}_.csv.gz"),
        os.path.join(PGSCEN_DIR, 'notuning', f"escores_{energy_type}_{year}_.csv.gz"),
    ]
    path = next((p for p in preferred if os.path.exists(p)), None)
    if path is None:
        # Fallback: any matching
        matches = glob.glob(os.path.join(PGSCEN_DIR, '**', f"*{energy_type}_{year}_*.csv.gz"), recursive=True)
        if matches:
            path = matches[0]
    if path is None:
        return None
    try:
        df = pd.read_csv(path, compression='infer')
    except Exception:
        return None

    # Identify time column
    time_col = next((c for c in df.columns if str(c).lower() in ('time','timestamp','datetime','date')), None)
    if not time_col:
        return None
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    try:
        day_dt = datetime.strptime(day, '%Y-%m-%d')
    except Exception:
        return None
    day_end = day_dt + timedelta(days=1)
    df_day = df[(df[time_col] >= day_dt) & (df[time_col] < day_end)].copy()
    if df_day.empty:
        return None

    # Scenario-like numeric columns
    num_cols = [c for c in df_day.columns if c != time_col and pd.api.types.is_numeric_dtype(df_day[c])]
    if not num_cols:
        return None

    # Build summary similar to remote flow
    df_summary = pd.DataFrame({'date': df_day[time_col]})
    scen_vals = df_day[num_cols]
    df_summary['scen_avg'] = scen_vals.mean(axis=1)
    actl_col = next((c for c in df_day.columns if str(c).lower().startswith('actual')), None)
    fcst_col = next((c for c in df_day.columns if str(c).lower().startswith('forecast')), None)
    df_summary['actual'] = df_day[actl_col] if actl_col is not None else df_summary['scen_avg']
    df_summary['forecast'] = df_day[fcst_col] if fcst_col is not None else df_summary['scen_avg']
    df_summary['5%'] = scen_vals.quantile(0.05, axis=1)
    df_summary['95%'] = scen_vals.quantile(0.95, axis=1)

    fig_summary = px.line(df_summary, x='date', y=['scen_avg', 'actual', 'forecast'])
    fig_summary.data[2].line.dash = 'dash'
    fig_summary.data[0].name = f'Scen Avg-{version}'
    fig_summary.data[1].name = f'Actual-{version}'
    fig_summary.data[2].name = f'Forecast-{version}'

    fig_5per = px.line(df_summary, x='date', y=['5%'])
    fig_95per = px.line(df_summary, x='date', y=['95%'])
    for tr in fig_summary.data:
        fig_5per.add_trace(tr)
    for tr in fig_95per.data:
        fig_5per.add_trace(tr)

    date_verbal = datetime.strftime(day_dt, "%b %d, %Y")
    fig_5per.update_layout(
        title=f'Hourly Time Series for Asset (PGScen {energy_type}) on {date_verbal} in Local Time Zone',
        yaxis_title='MWh',
        xaxis_title='Time',
        legend_title='')
    fig_5per.update_xaxes(dtick=3600000, tickformat='%I%p')
    return fig_5per

def dcc_tab_scenariovisualize(label= 'RTS',
                              date_values = date_values_rts, date_values_id = 'date_values_rts',
                              energy_types = energy_types, energy_types_id = 'energy_types_rts',
                              asset_id = 'asset_ids_rts',
                              scenario_plot_id = 'rts_scenario_plot_notuning'):
    dcc_tab = dcc.Tab(label=label,
            children=[

                # dbc.Row(
                #     dbc.Col([
                #         html.Br(),
                #         html.Label('Select Version'),
                #         dcc.RadioItems(
                #             options={'tuning': 'Tuning', 'notuning': 'No Tuning'},
                #             id='version_t7k',
                #             value='tuning',
                #             style=RADIOITEMS_STYLE)
                #     ])
                # ),

                dbc.Row([
                    dbc.Col([
                        html.Label('Select Day'),
                        dcc.Dropdown(date_values,
                                     id=date_values_id,
                                     value=date_values[0],
                                     className='dropdown-short')
                    ], xs=12, md=6, lg=4),
                    dbc.Col([
                        html.Label('Select Asset Type'),
                        dcc.RadioItems(
                            list(energy_types),
                            'load',
                            id=energy_types_id,
                            className='radioitems')
                    ], xs=12, md=6, lg=4),
                    dbc.Col([
                        html.Label('Select Asset ID'),
                        dcc.Dropdown(id=asset_id,
                                     className='dropdown-long'),
                    ], xs=12, md=12, lg=4),
                ], className='controls-row'),

                # plot
                html.Wbr(),
                dbc.Row(dbc.Col([
                    html.Figure([
                        dcc.Graph(
                            id=scenario_plot_id,
                            style={"height": "70vh", "width": "100%"},
                            config={"responsive": True}),
                        html.Figcaption(id=f"{scenario_plot_id}-caption", className='vis-caption', tabIndex=0)
                    ], className='graph-figure', role='group', **{"aria-labelledby": f"{scenario_plot_id}-caption"}),
                    html.Details([
                        html.Summary("Data table", **{"aria-controls": f"{scenario_plot_id}-table"}),
                        html.Div(id=f"{scenario_plot_id}-table", className='vis-table-wrapper')
                    ], open=False)
                ]))
            ],
            className='tab',
            selected_className='tab--selected')
    return dcc_tab


html_div_scenariooverview = html.Section(children=[
    html.Div([
        dcc.Markdown(children=markdown_text_scenario,
                 className='markdown', id='scenarios-markdown')
    ], className='section', id='scenarios-markdown-section')
], className='app-content')

html_div_scenariovisualize = html.Section(children=[

                dbc.Row(
                    dbc.Col(html.H1(children='Scenarios Visualization',
                                    className='title', id='scenarios-title'))
                    , justify='start', align='start', id='scenarios-title-row'),

                dbc.Row(dcc.Tabs(
                    children=[
                        dcc_tab_scenariovisualize(label='RTS',
                                                  date_values=date_values_rts,
                                                  date_values_id='date_values_rts',
                                                  energy_types=energy_types,
                                                  energy_types_id='energy_types_rts',
                                                  asset_id='asset_ids_rts',
                                                  scenario_plot_id='rts_scenario_plot_notuning'),

                        dcc_tab_scenariovisualize(label='Texast7k',
                                                  date_values=date_values_t7k,
                                                  date_values_id='date_values_t7k',
                                                  energy_types=energy_types,
                                                  energy_types_id='energy_types_t7k',
                                                  asset_id='asset_ids_t7k',
                                                  scenario_plot_id='t7k_scenario_plot_notuning')
                    ], className='tabs'
                ),
                    justify='between')
            ], className='app-content')

# Dash Pages expects a module-level variable named 'layout'
layout = html.Div([
    html_div_scenariooverview,
    html_div_scenariovisualize,
    dcc.Location(id='url-scenarios', refresh=False),
])


def build_timeseries(version, day, asset_type, asset_id):
    day = day.replace('-', '')
    file_path = '/ORFEUS-Alice/data/scenarios_data/{}-scens-csv/{}/{}/{}.csv'.format(
        version, day, asset_type, asset_id)
    df = None
    if HAS_DROPBOX and dbx is not None:
        try:
            _, res = dbx.files_download(file_path)
            with io.BytesIO(res.content) as stream:
                df = pd.read_csv(stream, index_col=0).reset_index()
        except Exception:
            df = None
    if df is None:
        # Try local per-asset files (with and without 'notuning'),
        # and with asset_id space/underscore variants.
        # Build possible filename variants for the asset id
        asset_variants = []
        # Always consider the original string form
        try:
            asset_str = str(asset_id)
        except Exception:
            asset_str = f"{asset_id}"
        asset_variants.append(asset_str)
        # If numeric like 1.0, also try integer string '1'
        try:
            if isinstance(asset_id, (int, np.integer)):
                asset_variants.append(str(int(asset_id)))
            elif isinstance(asset_id, (float, np.floating)):
                if float(asset_id).is_integer():
                    asset_variants.append(str(int(asset_id)))
                # Also try stripping a trailing .0 if present in string form
                if asset_str.endswith('.0'):
                    asset_variants.append(asset_str[:-2])
        except Exception:
            pass
        # Try underscore variant for names with spaces
        if isinstance(asset_str, str) and ' ' in asset_str:
            asset_variants.append(asset_str.replace(' ', '_'))
        # De-duplicate while preserving order
        seen = set()
        asset_variants = [x for x in asset_variants if not (x in seen or seen.add(x))]
        found = False
        for aid in asset_variants:
            candidates = [
                f"data/scenarios_data/{version}-scens-csv/{day}/{asset_type}/{aid}.csv",
                f"data/scenarios_data/{version}-scens-csv/notuning/{day}/{asset_type}/{aid}.csv",
                f"data/scenarios_data/{version}-scens-csv/tuning/{day}/{asset_type}/{aid}.csv",
            ]
            for rel in candidates:
                local_path = os.path.join(ROOT_DIR, rel)
                if os.path.exists(local_path):
                    try:
                        df = pd.read_csv(local_path, index_col=0).reset_index()
                        found = True
                        break
                    except Exception:
                        df = None
            if found:
                break
        if df is None:
            # Try PGScen directory (expects YYYY-MM-DD)
            day_iso = f"{day[:4]}-{day[4:6]}-{day[6:8]}"
            fig_pg = _try_build_fig_from_pgscen(version, day_iso, asset_type)
            if fig_pg is not None:
                return fig_pg
            # No data available: return an annotated empty figure
            msg = f"No data found for {asset_type}:{asset_id} on {day_iso}"
            fig = go.Figure()
            fig.add_annotation(text=msg, xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False,
                               font=dict(size=18))
            fig.update_layout(title=f"{asset_id} — {day_iso}")
            return fig

    # build the list of date values
    # start from 00:00 to 23:00 on the day in local time
    start_date = datetime.strptime(
        '{}-{}-{}-00-00'.format(day[2:4], day[4:6], day[6:8]),
        "%y-%m-%d-%H-%M")
    end_date = start_date + timedelta(hours=23)
    date_values_7k = pd.date_range(start=start_date, end=end_date, freq='h')

    # find 5 percentile extreme scenarios
    df_5per = pd.DataFrame()
    df_95per = pd.DataFrame()
    num_largest = max(1, int((df.shape[0] - 2) * 0.05))

    for time in df.columns[2:]:
        df_5per[time] = df[time][2:].nlargest(num_largest).values
        df_95per[time] = df[time][2:].nsmallest(num_largest).values

    df_5per = df_5per.T
    df_5per.index = date_values_7k
    df_5per.name = 'date'
    df_5per.columns = np.arange(1, num_largest + 1)

    df_95per = df_95per.T
    df_95per.index = date_values_7k
    df_95per.name = 'date'
    df_95per.columns = np.arange(1, num_largest + 1)

    scen_summary = df.iloc[2:, 2:].describe()
    df_summary = pd.DataFrame({'date': date_values_7k,
                               'actual': df.loc[df['Type'] == 'Actual'].iloc[:,
                                         2:].values.flatten(),
                               'forecast': df.loc[
                                               df['Type'] == 'Forecast'].iloc[
                                           :, 2:].values.flatten(),
                               'scen_avg': scen_summary.loc['mean', :].values,
                               '5%': df.iloc[2:, 2:].quantile(0.05).values,
                               '95%': df.iloc[2:, 2:].quantile(0.95).values,
                               '25%': scen_summary.loc['25%', :].values,
                               '75%': scen_summary.loc['75%', :].values,
                               'max': scen_summary.loc['max', :].values,
                               'min': scen_summary.loc['min', :].values})

    # summary plot
    fig_summary = px.line(df_summary, x='date',
                          y=['scen_avg', 'actual', 'forecast'])

    fig_summary.data[2].line.dash = 'dash'

    fig_summary.data[0].name = 'Scen Avg-{}'.format(version)

    fig_summary.data[1].name = 'Actual-{}'.format(version)

    fig_summary.data[2].name = 'Forecast-{}'.format(version)

    fig_summary.data[0].legendgroup = 'Scen Avg-{}'.format(version)

    fig_summary.data[1].legendgroup = 'Actual-{}'.format(version)

    fig_summary.data[2].legendgroup = 'Forecast-{}'.format(version)

    # add 5 percentile scenarios to plot
    fig_5per = px.line(df_5per, x=date_values_7k, y=df_5per.columns)
    fig_5per.for_each_trace(
        lambda t: t.update(name='Top 5 Percentile-{}'.format(version),
                           legendgroup='Top 5 Percentile-{}'.format(version)))

    fig_95per = px.line(df_95per, x=date_values_7k, y=df_95per.columns)
    fig_95per.for_each_trace(
        lambda t: t.update(name='Bottom 5 Percentile-{}'.format(version),
                           legendgroup='Bottom 5 Percentile-{}'.format(
                               version)))

    # fig_5per.data[0].name = 'top 5 percentile'
    for i in range(1, len(fig_5per.data)):
        fig_5per.data[i].showlegend = False

    for i in range(1, len(fig_95per.data)):
        fig_95per.data[i].showlegend = False

    # add percentiles to summary plot
    for i in range(len(fig_summary.data)):
        fig_5per.add_trace(fig_summary.data[i])

    for i in range(len(fig_95per.data)):
        fig_5per.add_trace(fig_95per.data[i])

    fig = fig_5per

    date = datetime.strptime(day, "%Y%m%d").strftime("%b %d, %Y")
    fig.update_layout(
        title='Hourly Time Series for Asset {} on {} in Local Time Zone'.format(
            asset_id, date),
        yaxis_title='MWh',
        xaxis_title='Time',
        legend_title='')
    fig.update_xaxes(dtick=3600000, tickformat='%I%p')

    return fig


@dash.callback(
    Output('asset_ids_t7k', 'options'),
    Input('energy_types_t7k', 'value'))
def set_asset_ids_options(energy_type):
    return [{'label': i, 'value': i} for i in
            energy_types_asset_ids_t7k_csv[energy_type]]


@dash.callback(
    Output('asset_ids_t7k', 'value'),
    Input('asset_ids_t7k', 'options'))
def set_asset_ids_value(energy_types_asset_ids_t7k_csv):
    try:
        # prefer a middle option if available, else first, else None
        if len(energy_types_asset_ids_t7k_csv) > 2:
            return energy_types_asset_ids_t7k_csv[2]['value']
        if len(energy_types_asset_ids_t7k_csv) > 0:
            return energy_types_asset_ids_t7k_csv[0]['value']
    except Exception:
        pass
    return None


@dash.callback(
    Output('asset_ids_rts', 'options'),
    Input('energy_types_rts', 'value'))
def set_asset_ids_options(energy_type):
    return [{'label': i, 'value': i} for i in
            energy_types_asset_ids_rts_csv[energy_type]]


@dash.callback(
    Output('asset_ids_rts', 'value'),
    Input('asset_ids_rts', 'options'))
def set_asset_ids_value(energy_types_asset_ids_rts_csv):
    try:
        if len(energy_types_asset_ids_rts_csv) > 0:
            return energy_types_asset_ids_rts_csv[0]['value']
    except Exception:
        pass
    return None

@dash.callback(
    Output('t7k_scenario_plot_notuning', 'figure'),
    Output('t7k_scenario_plot_notuning-caption', 'children'),
    # Input('version_t7k', 'value'),
    Input('date_values_t7k', 'value'),
    Input('energy_types_t7k', 'value'),
    Input('asset_ids_t7k', 'value'),
    Input('url-scenarios', 'search'),
    State('embed-store', 'data'))
def update_scenario_plot(day, asset_type, asset_id, search, embed):
    fig = build_timeseries('t7k', day, asset_type, asset_id)
    try:
        if embed:
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), width=None, height=None)
            # showtitle=false hides title in embed mode
            from urllib.parse import parse_qs
            q = parse_qs((search or '').lstrip('?'))
            sval = (q.get('showtitle', [None])[0] or '').strip().lower()
            showtitle = not (sval in ('0', 'false', 'no', 'off'))
            if not showtitle:
                fig.update_layout(title=None)
    except Exception:
        pass
    # Caption summarizing ranges
    caption = f"Scenarios plot T7K {asset_type} asset {asset_id} on {day}."
    try:
        if fig and fig.data:
            # Attempt to summarize first 3 series
            stats_parts = []
            for tr in fig.data[:3]:
                yvals = [v for v in getattr(tr, 'y', []) if isinstance(v, (int, float))]
                if yvals:
                    stats_parts.append(f"{tr.name}: {min(yvals):.1f}-{max(yvals):.1f}")
            if stats_parts:
                caption += " " + "; ".join(stats_parts)
    except Exception:
        pass
    return fig, caption


@dash.callback(
    Output('rts_scenario_plot_notuning', 'figure'),
    Output('rts_scenario_plot_notuning-caption', 'children'),
    # Input('version_t7k', 'value'),
    Input('date_values_rts', 'value'),
    Input('energy_types_rts', 'value'),
    Input('asset_ids_rts', 'value'),
    Input('url-scenarios', 'search'),
    State('embed-store', 'data'))
def update_scenario_plot_rts(day, asset_type, asset_id, search, embed):
    fig = build_timeseries('rts', day, asset_type, asset_id)
    try:
        if embed:
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), width=None, height=None)
            # showtitle=false hides title in embed mode
            from urllib.parse import parse_qs
            q = parse_qs((search or '').lstrip('?'))
            sval = (q.get('showtitle', [None])[0] or '').strip().lower()
            showtitle = not (sval in ('0', 'false', 'no', 'off'))
            if not showtitle:
                fig.update_layout(title=None)
    except Exception:
        pass
    caption = f"Scenarios plot RTS {asset_type} asset {asset_id} on {day}."
    try:
        if fig and fig.data:
            stats_parts = []
            for tr in fig.data[:3]:
                yvals = [v for v in getattr(tr, 'y', []) if isinstance(v, (int, float))]
                if yvals:
                    stats_parts.append(f"{tr.name}: {min(yvals):.1f}-{max(yvals):.1f}")
            if stats_parts:
                caption += " " + "; ".join(stats_parts)
    except Exception:
        pass
    return fig, caption


@dash.callback(
    Output('scenarios-markdown-section', 'style'),
    Output('scenarios-title', 'style'),
    Output('scenarios-title-row', 'style'),
    Input('url-scenarios', 'search'),
)
def _scenarios_toggle_embed(search):
    try:
        from urllib.parse import parse_qs
        q = parse_qs((search or '').lstrip('?'))
        val = (q.get('embed', [None])[0] or '').strip().lower()
        embed = val in ('1', 'true', 'yes', 'on')
    except Exception:
        embed = False
    style_hide = {'display': 'none'} if embed else {}
    # In embed mode: hide markdown; and if showtitle=false, also hide title and its row.
    try:
        from urllib.parse import parse_qs
        q = parse_qs((search or '').lstrip('?'))
        sval = (q.get('showtitle', [None])[0] or '').strip().lower()
        showtitle = not (sval in ('0', 'false', 'no', 'off'))
    except Exception:
        showtitle = True
    title_style = {} if (not embed or showtitle) else {'display': 'none'}
    row_style = title_style
    return style_hide, title_style, row_style


# Data table population callbacks (reuse central accessibility helper)
@dash.callback(
    Output('rts_scenario_plot_notuning-table', 'children'),
    Input('rts_scenario_plot_notuning', 'figure')
)
def _update_rts_scen_table(fig_json):  # noqa: D401
    try:
        return figure_to_table_html(fig_json)
    except Exception:
        return html.Em('Unavailable')


@dash.callback(
    Output('t7k_scenario_plot_notuning-table', 'children'),
    Input('t7k_scenario_plot_notuning', 'figure')
)
def _update_t7k_scen_table(fig_json):  # noqa: D401
    try:
        return figure_to_table_html(fig_json)
    except Exception:
        return html.Em('Unavailable')