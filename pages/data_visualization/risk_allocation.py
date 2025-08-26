import pandas as pd
from typing import List
from datetime import date, timedelta, datetime
from utils.ui import html, dcc, Input, Output, State, ctx, dash, COLORBLIND_PALETTE, PATTERN_SHAPES
import plotly.express as px
from utils.accessibility import figure_to_table_html

import dash
import dash_bootstrap_components as dbc
from inputs.inputs import type_allocs_rts, asset_allocs_rts, type_allocs_t7k, asset_allocs_t7k
from utils.md import load_markdown, extract_first_h1
markdown_text_riskalloc = load_markdown('markdown', 'allocation.md')
RISKALLOC_TITLE = extract_first_h1(markdown_text_riskalloc, fallback='Risk Allocation')
dash.register_page(__name__, path='/riskallocplot', name='Risk Allocation', order=2, title=RISKALLOC_TITLE)

today = date.today()
yesterdate_verbal = (today - timedelta(1)).strftime("%b %d")
yesterdate = (today - timedelta(1)).strftime("%y-%m-%d")[3:]

todaydate_verbal = today.strftime("%b %d")
todaydate = today.strftime("%y-%m-%d")[3:]

# Risk Alloc Asset IDs
asset_ids_risk_alloc_rts = asset_allocs_rts.columns[1:]
asset_ids_risk_alloc_t7k = asset_allocs_t7k.columns[1:]

# Calculate daily index by taking the avg of hourly index
start_date = datetime.strptime('2020-' + yesterdate, "%Y-%m-%d")
end_date = start_date + timedelta(hours=23)
daterange_rts = pd.date_range(start_date, end_date, freq='h')

start_date = datetime.strptime('2018-' + yesterdate, "%Y-%m-%d")
end_date = start_date + timedelta(hours=23)
daterange_t7k = pd.date_range(start_date, end_date, freq='h')


def _safe_daily_mean(df: pd.DataFrame, daterange: pd.DatetimeIndex, expected_cols: List[str]) -> pd.Series:
    """Compute mean over daterange safely, returning zeros for missing cols."""
    try:
        if 'time' in df.columns:
            mask = df['time'].isin(daterange)
            filtered = df.loc[mask]
            if not filtered.empty:
                s = filtered.set_index('time').mean(numeric_only=True)
                # Ensure ordering/coverage of expected columns
                return s.reindex(expected_cols).fillna(0.0)
    except Exception:
        pass
    return pd.Series({c: 0.0 for c in expected_cols})


# Precompute daily means with defensive fallbacks
type_allocs_rts_day = _safe_daily_mean(type_allocs_rts, daterange_rts, ['WIND', 'PV', 'RTPV'])
asset_cols_rts = [c for c in asset_allocs_rts.columns if c != 'time']
asset_allocs_rts_day = _safe_daily_mean(asset_allocs_rts, daterange_rts, asset_cols_rts)

type_allocs_t7k_day = _safe_daily_mean(type_allocs_t7k, daterange_t7k, ['WIND', 'PV'])
asset_cols_t7k = [c for c in asset_allocs_t7k.columns if c != 'time']
asset_allocs_t7k_day = _safe_daily_mean(asset_allocs_t7k, daterange_t7k, asset_cols_t7k)

html_div_risk_allocation_overview =  html.Div(children=[
                html.Div([
                    dcc.Markdown(children=markdown_text_riskalloc, className='markdown', id='riskalloc-markdown')
                ],
                    className='section')
            ],
                className='app-content')

def dcc_tab_risk_allocation(label = 'RTS', yesterdate_verbal = yesterdate_verbal,
                        type_allocs_rtpv_day = type_allocs_rts_day['RTPV'],
                        type_allocs_pv_day = type_allocs_rts_day['PV'],
                        type_allocs_wind_day = type_allocs_rts_day['WIND'],
                        asset_ids = asset_ids_risk_alloc_rts,
                        asset_ids_id = 'asset_ids_risk_alloc_rts',
                        daily_index_asset_id = 'daily_index_asset_id_rts',
                        button_id_day_type_alloc= 'rts-type-allocs-1day',
                        button_id_week_type_alloc= 'rts-type-allocs-1week',
                        button_id_hist_type_alloc= 'rts-type-allocs-hist',
                        fig_id_type_alloc = 'fig_mean_asset_type_risk_alloc_rts',
                        button_id_day_asset_alloc = 'rts-asset-allocs-1day',
                        button_id_week_asset_alloc = 'rts-asset-allocs-1week',
                        button_id_hist_asset_alloc = 'rts-asset-allocs-hist',
                        asset_id_in_plot_title = 'asset_id_in_plot_title_rts',
                        fig_id_asset_alloc = 'fig_asset_risk_alloc_rts'):

    dbc_asset_type_title = dbc.Row(
        dbc.Col([
            html.Br(),
        html.H3(children='Asset Type Reliability Cost Index on {}'.format(yesterdate_verbal),
            className='index-title'),
        ])
        , justify='start', align='start')

    dbc_solar_index = dbc.Row(
        dbc.Col([
        html.H3(children='{}: {:.2f}'.format('Solar', type_allocs_pv_day),
            className='index-num')
        ]),
        justify='start', align='start')

    dbc_wind_index = dbc.Row(
        dbc.Col([
        html.H3(children='{}: {:.2f}'.format('Wind', type_allocs_wind_day),
            className='index-num')
        ]),
        justify='start', align='start')

    # change b/w asset id
    if label == 'RTS':
        dbc_rtpv_index = dbc.Row(
            dbc.Col([
            html.H3(children='{}: {:.2f}'.format('Rooftop Solar', type_allocs_rtpv_day),
                className='index-num')
            ])
            , justify='start', align='start')


    asset_level_index_title = 'Asset Level Reliability Cost Index on {}'.format(yesterdate_verbal)

    html_asset_level_index = html.Div(children = [
        dbc.Row(
            dbc.Col([
                html.Br(),
                html.H3(children=asset_level_index_title, className='index-title')
            ]),
            justify='start', align='start'),

        dbc.Row([
            dbc.Col([
                html.Div(
                    className="four columns pretty_container",
                    children=[
                        html.Label('Select Asset Id'),
                        dcc.Dropdown(asset_ids, placeholder='Asset ID', id=asset_ids_id,
                                     value=asset_ids[0], className='dropdown-long')
                    ])
            ])]),

        dbc.Row(
            dbc.Col([
                html.Br(),
                html.Div(id=daily_index_asset_id, className='index-num'),
                html.Br()
            ])
            , justify='start', align='start')

    ])

    html_asset_level_plot = html.Div(children = [
        dbc.Row(
            dbc.Col([
                html.Br(),
                html.H3(children=[
                        'Hourly Time Series of Asset Level Reliability Cost Index for ',
                        html.Div(id=asset_id_in_plot_title, className='inline')
                    ], className='index-title')
            ]),
            justify='start', align='start'),

        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Button('1 day', id=button_id_day_asset_alloc,
                                n_clicks=0, className='btn-white'),

                    html.Button('1 week', id=button_id_week_asset_alloc,
                                n_clicks=0, className='btn-white'),

                    html.Button('historical', id=button_id_hist_asset_alloc,
                                n_clicks=0, className='btn-white'),
                    html.Div(
                        id='container-button-timestamp')
                ])
            )
        ]),

        dbc.Row([
            dbc.Col([
                html.Figure([
                    dcc.Graph(
                        id=fig_id_asset_alloc,
                        className='graph-pad',
                        style={"height": "65vh", "width": "100%"},
                        config={"responsive": True},
                    ),
                    html.Figcaption(id=f"{fig_id_asset_alloc}-caption", className='vis-caption', tabIndex=0)
                ], className='graph-figure', role='group', **{"aria-labelledby": f"{fig_id_asset_alloc}-caption"}),
                html.Details([
                    html.Summary("Data table (asset)", **{"aria-controls": f"{fig_id_asset_alloc}-table"}),
                    html.Div(id=f"{fig_id_asset_alloc}-table", className='vis-table-wrapper')
                ], open=False)
            ])
        ], justify='start', align='start')

    ])

    html_asset_type_plot = html.Div(
    children = [
        dbc.Row(
            dbc.Col([
                html.Br(),
        html.H3(children='Hourly Time Series of Asset Type Reliability Cost Index',
            className='index-title')
            ]),
            justify='start', align='start'),

        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Button('1 day', id=button_id_day_type_alloc,
                                n_clicks=0, className='btn-white'),

                    html.Button('1 week', id=button_id_week_type_alloc,
                                n_clicks=0, className='btn-white'),

                    html.Button('historical', id=button_id_hist_type_alloc,
                                n_clicks=0, className='btn-white'),
                    html.Div(
                        id='container-button-timestamp')
                ])
            )
        ]),

        dbc.Row([
            dbc.Col([
                html.Figure([
                    dcc.Graph(
                        id=fig_id_type_alloc,
                        className='graph-pad',
                        style={"height": "65vh", "width": "100%"},
                        config={"responsive": True},
                    ),
                    html.Figcaption(id=f"{fig_id_type_alloc}-caption", className='vis-caption', tabIndex=0)
                ], className='graph-figure', role='group', **{"aria-labelledby": f"{fig_id_type_alloc}-caption"}),
                html.Details([
                    html.Summary("Data table (types)", **{"aria-controls": f"{fig_id_type_alloc}-table"}),
                    html.Div(id=f"{fig_id_type_alloc}-table", className='vis-table-wrapper')
                ], open=False)
            ])
        ], justify='start'),

        html.Div(className='section-divider')
    ])

    if label == 'RTS':
        tab_children = [dbc_asset_type_title, dbc_rtpv_index, dbc_solar_index, dbc_wind_index,
                        html_asset_level_index, html_asset_level_plot, html_asset_type_plot]
    else:
        tab_children = [dbc_asset_type_title, dbc_solar_index, dbc_wind_index,
                        html_asset_level_index, html_asset_level_plot, html_asset_type_plot]

    dcc_tab = dcc.Tab(label= label, children=tab_children,
                                    className='tab',
                                    selected_className='tab--selected')
    return dcc_tab

html_div_risk_allocation = html.Div(children=[
                dbc.Row(
                    dbc.Col(html.H1(children='Reliability Cost Index', className='title', id='riskalloc-title'))
                    , justify='start', align='start', id='riskalloc-title-row'),

                dbc.Row(dcc.Tabs(
                    children=[
                        dcc_tab_risk_allocation(label='RTS',
                                                yesterdate_verbal=yesterdate_verbal,
                                                type_allocs_rtpv_day=
                                                type_allocs_rts_day['RTPV'],
                                                type_allocs_pv_day=
                                                type_allocs_rts_day['PV'],
                                                type_allocs_wind_day=
                                                type_allocs_rts_day['WIND'],
                                                asset_ids=asset_ids_risk_alloc_rts,
                                                asset_ids_id='asset_ids_risk_alloc_rts',
                                                daily_index_asset_id='daily_index_asset_id_rts',
                                                button_id_day_type_alloc='rts-type-allocs-1day',
                                                button_id_week_type_alloc='rts-type-allocs-1week',
                                                button_id_hist_type_alloc='rts-type-allocs-hist',
                                                fig_id_type_alloc='fig_mean_asset_type_risk_alloc_rts',
                                                asset_id_in_plot_title='asset_id_in_plot_title_rts',
                                                button_id_day_asset_alloc='rts-asset-allocs-1day',
                                                button_id_week_asset_alloc='rts-asset-allocs-1week',
                                                button_id_hist_asset_alloc='rts-asset-allocs-hist',
                                                fig_id_asset_alloc='fig_asset_risk_alloc_rts'),

                        dcc_tab_risk_allocation(label='T7K',
                                                yesterdate_verbal=yesterdate_verbal,
                                                type_allocs_pv_day=
                                                type_allocs_t7k_day['PV'],
                                                type_allocs_wind_day=
                                                type_allocs_t7k_day['WIND'],
                                                asset_ids=asset_ids_risk_alloc_t7k,
                                                asset_ids_id='asset_ids_risk_alloc_t7k',
                                                daily_index_asset_id='daily_index_asset_id_t7k',
                                                button_id_day_type_alloc='t7k-type-allocs-1day',
                                                button_id_week_type_alloc='t7k-type-allocs-1week',
                                                button_id_hist_type_alloc='t7k-type-allocs-hist',
                                                fig_id_type_alloc='fig_mean_asset_type_risk_alloc_t7k',
                                                asset_id_in_plot_title='asset_id_in_plot_title_t7k',
                                                button_id_day_asset_alloc='t7k-asset-allocs-1day',
                                                button_id_week_asset_alloc='t7k-asset-allocs-1week',
                                                button_id_hist_asset_alloc='t7k-asset-allocs-hist',
                                                fig_id_asset_alloc='fig_asset_risk_alloc_t7k'),

                    ], className='tabs'
                ),
                    justify='between')
            ], className='app-content')

# Dash Pages module-level layout (add a Location component for query param parsing)
layout = html.Div([
    html_div_risk_allocation,
    dcc.Location(id='url-riskalloc', refresh=False),
])


@dash.callback(
    Output('riskalloc-markdown', 'style'),
    Input('embed-store', 'data')
)
def _riskalloc_toggle_embed(embed: bool):
    return {'display': 'none'} if embed else {}

# Hide the main page title when embed=true & showtitle=false
@dash.callback(
    Output('riskalloc-title', 'style'),
    Output('riskalloc-title-row', 'style'),
    Input('url-riskalloc', 'search'),
)
def _riskalloc_toggle_title(search: str | None):
    try:
        from urllib.parse import parse_qs
        q = parse_qs((search or '').lstrip('?'))
        embed = (q.get('embed', [''])[0] or '').strip().lower() in ('1', 'true', 'yes', 'on')
        sval = (q.get('showtitle', [None])[0] or '').strip().lower()
        showtitle = not (sval in ('0', 'false', 'no', 'off'))
    except Exception:
        embed, showtitle = False, True
    title_style = {} if (not embed or showtitle) else {'display': 'none'}
    return title_style, title_style

def plot_mean_asset_type_risk_alloc(type_allocs, version='RTS', period='1day',
                                    level='asset_type', asset_id=None):
    # Empty-state helper
    def _empty_fig(title: str = 'No data available'):
        fig = px.line(pd.DataFrame({'time': [], 'value': []}), x='time', y='value')
        fig.update_layout(title=title, xaxis_title='Date', yaxis_title='Reliability Cost Index ($)')
        return fig
    if version == 'RTS':
        startyear_ = '2020-'
        if level == 'asset_type':
            y_ = ['WIND', 'PV', 'RTPV']
        else:
            y_ = asset_id
    else:
        startyear_ = '2018-'
        if level == 'asset_type':
            y_ = ['WIND', 'PV']
        else:
            y_ = asset_id

    # Validate y selection
    if level != 'asset_type':
        if not y_:
            return _empty_fig('Select an asset to view the time series')
        # Coerce to list for existence checks
        y_cols = [y_]
    else:
        y_cols = y_

    missing = [c for c in y_cols if c not in type_allocs.columns]
    if missing:
        return _empty_fig(f"Missing columns: {', '.join(missing)}")

    if period == 'hist':
        if 'time' not in type_allocs.columns or type_allocs.empty:
            return _empty_fig()
        fig_type_allocs = px.line(type_allocs, x='time', y=y_,
                                  hover_data={"time": "|%H, %b %d"})
        fig_type_allocs.update_xaxes(tickformat='%H \n %b %d, %Y',
                                     title_font_size=25)

    else:
        end_date = datetime.strptime(startyear_ + todaydate, "%Y-%m-%d")
        if period == '1day':
            if 'time' not in type_allocs.columns or type_allocs.empty:
                return _empty_fig()
            if version == 'RTS':
                delta = timedelta(days=1)
                daterange = pd.date_range(end_date - delta, end_date, freq='h')
                type_allocs_day = type_allocs[type_allocs['time'].isin(daterange)]
            else:
                type_allocs_day = type_allocs.iloc[-24:, ]
            if type_allocs_day.empty:
                return _empty_fig()
            fig_type_allocs = px.line(type_allocs_day, x='time', y=y_,
                                      hover_data={"time": "|%H, %b %d"})
            fig_type_allocs.update_xaxes(tickformat='%H \n %b %d',
                                         title_font_size=25)

        elif period == '1week':
            if 'time' not in type_allocs.columns or type_allocs.empty:
                return _empty_fig()
            if version == 'RTS':
                delta = timedelta(weeks=1)
                daterange = pd.date_range(end_date - delta, end_date, freq='h')
                type_allocs_day = type_allocs[type_allocs['time'].isin(daterange)]
            else:
                type_allocs_day = type_allocs.iloc[-24*7:, ]
            if type_allocs_day.empty:
                return _empty_fig()
            fig_type_allocs = px.line(type_allocs_day, x='time', y=y_,
                                      hover_data={"time": "|%H, %b %d"})
            fig_type_allocs.update_xaxes(tickformat='%H \n %b %d',
                                         title_font_size=25)

    # Label traces defensively
    if len(fig_type_allocs.data) >= 1:
        fig_type_allocs.data[0].name = 'Wind'
    if level == 'asset_type' and len(fig_type_allocs.data) >= 2:
        fig_type_allocs.data[1].name = 'Solar'
        if version == 'RTS' and len(fig_type_allocs.data) >= 3:
            fig_type_allocs.data[2].name = 'Rooftop Solar'

    fig_type_allocs.update_layout(
        xaxis_title='Date',
        yaxis_title='Reliability Cost Index ($)',
        legend_title='Asset Type')

    # fig_type_allocs.update_xaxes(
    #     rangeselector=dict(
    #         buttons=list([
    #             dict(count=1, label="1d", step="day", stepmode="todate"),
    #             dict(count=7, label="1w", step="day", stepmode="todate"),
    #             dict(step="all")
    #         ])
    #     ),
    #     title_font_size = 25
    # )

    fig_type_allocs.update_yaxes(title_font_size=25)
    # Apply accessible color palette & line dash patterns
    try:
        for i, tr in enumerate(fig_type_allocs.data):
            if i < len(COLORBLIND_PALETTE):
                tr.line.color = COLORBLIND_PALETTE[i]
            if i % 3 == 1:
                tr.line.dash = 'dash'
            elif i % 3 == 2:
                tr.line.dash = 'dot'
    except Exception:
        pass
    return fig_type_allocs


@dash.callback(
    Output("fig_mean_asset_type_risk_alloc_rts", "figure"),
    Output("fig_mean_asset_type_risk_alloc_rts-caption", "children"),
    Input('rts-type-allocs-1day', 'n_clicks'),
    Input('rts-type-allocs-1week', 'n_clicks'),
    Input('rts-type-allocs-hist', 'n_clicks'),
    State('embed-store', 'data')
)
def plot_mean_asset_type_risk_alloc_daterange_rts(btn1, btn2, btn3, embed):
    if "rts-type-allocs-1day" == ctx.triggered_id:
        fig = plot_mean_asset_type_risk_alloc(type_allocs_rts, version='RTS',
                                              period='1day')
    elif "rts-type-allocs-1week" == ctx.triggered_id:
        fig = plot_mean_asset_type_risk_alloc(type_allocs_rts, version='RTS',
                                              period='1week')
    elif "rts-type-allocs-hist" == ctx.triggered_id:
        fig = plot_mean_asset_type_risk_alloc(type_allocs_rts, version='RTS',
                                              period='hist')
    else:
        fig = plot_mean_asset_type_risk_alloc(type_allocs_rts, version='RTS',
                                              period='1day')
    try:
        if embed:
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), width=None, height=None)
    except Exception:
        pass
    # Build accessible caption summary
    cap = []
    try:
        if fig and fig.data:
            cap.append("Series: " + ", ".join([tr.name or f"Series {i+1}" for i, tr in enumerate(fig.data)]))
            # Summaries per trace (first 3 traces typical)
            for tr in fig.data[:3]:
                yvals = [v for v in tr.y if isinstance(v, (int, float))]
                if yvals:
                    cap.append(f"{tr.name}: min {min(yvals):.2f}, max {max(yvals):.2f}, mean {sum(yvals)/len(yvals):.2f}")
    except Exception:
        pass
    caption = " | ".join(cap) if cap else "Reliability Cost Index time series chart"
    return fig, caption


@dash.callback(
    Output('fig_mean_asset_type_risk_alloc_rts-table', 'children'),
    Input('fig_mean_asset_type_risk_alloc_rts', 'figure')
)
def _update_rts_type_table(fig_json):
    try:
        return figure_to_table_html(fig_json)
    except Exception:
        return html.Em('Unavailable')


@dash.callback(
    Output('fig_asset_risk_alloc_rts', 'figure'),
    Output('fig_asset_risk_alloc_rts-caption', 'children'),
    Input('asset_ids_risk_alloc_rts', 'value'),
    Input('rts-asset-allocs-1day', 'n_clicks'),
    Input('rts-asset-allocs-1week', 'n_clicks'),
    Input('rts-asset-allocs-hist', 'n_clicks'),
    State('embed-store', 'data')
)
def asset_ids_risk_alloc_rts(asset_id, button1, button2, button3, embed):
    if asset_id is None:
        return plot_mean_asset_type_risk_alloc(asset_allocs_rts, version='RTS', period='1day', level='asset_id', asset_id=None)
    if "rts-asset-allocs-1day" == ctx.triggered_id:
        fig_asset_allocs = plot_mean_asset_type_risk_alloc(asset_allocs_rts,
                                                           version='RTS',
                                                           period='1day',
                                                           level='asset_id',
                                                           asset_id=asset_id)
    elif "rts-asset-allocs-1week" == ctx.triggered_id:
        fig_asset_allocs = plot_mean_asset_type_risk_alloc(asset_allocs_rts,
                                                           version='RTS',
                                                           period='1week',
                                                           level='asset_id',
                                                           asset_id=asset_id)
    elif "rts-asset-allocs-hist" == ctx.triggered_id:
        fig_asset_allocs = plot_mean_asset_type_risk_alloc(asset_allocs_rts,
                                                           version='RTS',
                                                           period='hist',
                                                           level='asset_id',
                                                           asset_id=asset_id)
    else:
        fig_asset_allocs = plot_mean_asset_type_risk_alloc(asset_allocs_rts,
                                                           version='RTS',
                                                           period='1day',
                                                           level='asset_id',
                                                           asset_id=asset_id)
    try:
        if embed:
            fig_asset_allocs.update_layout(margin=dict(l=10, r=10, t=30, b=10), width=None, height=None)
    except Exception:
        pass
    # Caption summarizing asset series
    caption = f"Asset {asset_id} Reliability Cost Index time series"
    try:
        if fig_asset_allocs and fig_asset_allocs.data and fig_asset_allocs.data[0].y is not None:
            yvals = [v for v in fig_asset_allocs.data[0].y if isinstance(v, (int, float))]
            if yvals:
                caption += f"; min {min(yvals):.2f}, max {max(yvals):.2f}, mean {sum(yvals)/len(yvals):.2f}"
    except Exception:
        pass
    return fig_asset_allocs, caption

@dash.callback(
    Output('fig_asset_risk_alloc_rts-table', 'children'),
    Input('fig_asset_risk_alloc_rts', 'figure')
)
def _update_rts_asset_table(fig_json):
    try:
        return figure_to_table_html(fig_json)
    except Exception:
        return html.Em('Unavailable')


@dash.callback(
    Output('daily_index_asset_id_rts', 'children'),
    Input('asset_ids_risk_alloc_rts', 'value'))
def find_daily_index_asset_id_rts(asset_id):
    index = asset_allocs_rts_day[asset_id]
    return f'{asset_id}: {index:.2f}'

@dash.callback(
    Output('asset_id_in_plot_title_rts', 'children'),
    Input('asset_ids_risk_alloc_rts', 'value'))
def find_daily_index_asset_id(asset_id):
    return f'{asset_id}'



@dash.callback(
    Output("fig_mean_asset_type_risk_alloc_t7k", "figure"),
    Output("fig_mean_asset_type_risk_alloc_t7k-caption", "children"),
    Input('t7k-type-allocs-1day', 'n_clicks'),
    Input('t7k-type-allocs-1week', 'n_clicks'),
    Input('t7k-type-allocs-hist', 'n_clicks'),
    State('embed-store', 'data')
)
def plot_mean_asset_type_risk_alloc_daterange_t7k(btn1, btn2, btn3, embed):
    if "t7k-type-allocs-1day" == ctx.triggered_id:
        fig = plot_mean_asset_type_risk_alloc(type_allocs_t7k, version='T7K',
                                              period='1day')
    elif "t7k-type-allocs-1week" == ctx.triggered_id:
        fig = plot_mean_asset_type_risk_alloc(type_allocs_t7k, version='T7K',
                                              period='1week')
    elif "t7k-type-allocs-hist" == ctx.triggered_id:
        fig = plot_mean_asset_type_risk_alloc(type_allocs_t7k, version='T7K',
                                              period='hist')
    else:
        fig = plot_mean_asset_type_risk_alloc(type_allocs_t7k, version='T7K',
                                              period='1day')
    try:
        if embed:
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), width=None, height=None)
    except Exception:
        pass
    cap = []
    try:
        if fig and fig.data:
            cap.append("Series: " + ", ".join([tr.name or f"Series {i+1}" for i, tr in enumerate(fig.data)]))
            for tr in fig.data[:3]:
                yvals = [v for v in tr.y if isinstance(v, (int, float))]
                if yvals:
                    cap.append(f"{tr.name}: min {min(yvals):.2f}, max {max(yvals):.2f}, mean {sum(yvals)/len(yvals):.2f}")
    except Exception:
        pass
    caption = " | ".join(cap) if cap else "Reliability Cost Index time series chart"
    return fig, caption

@dash.callback(
    Output('fig_mean_asset_type_risk_alloc_t7k-table', 'children'),
    Input('fig_mean_asset_type_risk_alloc_t7k', 'figure')
)
def _update_t7k_type_table(fig_json):
    try:
        return figure_to_table_html(fig_json)
    except Exception:
        return html.Em('Unavailable')

@dash.callback(
    Output('fig_asset_risk_alloc_t7k', 'figure'),
    Output('fig_asset_risk_alloc_t7k-caption', 'children'),
    Input('asset_ids_risk_alloc_t7k', 'value'),
    Input('t7k-asset-allocs-1day', 'n_clicks'),
    Input('t7k-asset-allocs-1week', 'n_clicks'),
    Input('t7k-asset-allocs-hist', 'n_clicks'),
    State('embed-store', 'data')
)
def asset_ids_risk_alloc_t7k(asset_id, button1, button2, button3, embed):
    if asset_id is None:
        return plot_mean_asset_type_risk_alloc(asset_allocs_t7k, version='T7K', period='1day', level='asset_id', asset_id=None)
    if "t7k-asset-allocs-1day" == ctx.triggered_id:
        fig_asset_allocs = plot_mean_asset_type_risk_alloc(asset_allocs_t7k,
                                                           version='T7K',
                                                           period='1day',
                                                           level='asset_id',
                                                           asset_id=asset_id)
    elif "t7k-asset-allocs-1week" == ctx.triggered_id:
        fig_asset_allocs = plot_mean_asset_type_risk_alloc(asset_allocs_t7k,
                                                           version='T7K',
                                                           period='1week',
                                                           level='asset_id',
                                                           asset_id=asset_id)
    elif "t7k-asset-allocs-hist" == ctx.triggered_id:
        fig_asset_allocs = plot_mean_asset_type_risk_alloc(asset_allocs_t7k,
                                                           version='T7K',
                                                           period='hist',
                                                           level='asset_id',
                                                           asset_id=asset_id)
    else:
        fig_asset_allocs = plot_mean_asset_type_risk_alloc(asset_allocs_t7k,
                                                           version='T7K',
                                                           period='1day',
                                                           level='asset_id',
                                                           asset_id=asset_id)
    try:
        if embed:
            fig_asset_allocs.update_layout(margin=dict(l=10, r=10, t=30, b=10), width=None, height=None)
    except Exception:
        pass
    caption = f"Asset {asset_id} Reliability Cost Index time series"
    try:
        if fig_asset_allocs and fig_asset_allocs.data and fig_asset_allocs.data[0].y is not None:
            yvals = [v for v in fig_asset_allocs.data[0].y if isinstance(v, (int, float))]
            if yvals:
                caption += f"; min {min(yvals):.2f}, max {max(yvals):.2f}, mean {sum(yvals)/len(yvals):.2f}"
    except Exception:
        pass
    return fig_asset_allocs, caption

@dash.callback(
    Output('fig_asset_risk_alloc_t7k-table', 'children'),
    Input('fig_asset_risk_alloc_t7k', 'figure')
)
def _update_t7k_asset_table(fig_json):
    try:
        return figure_to_table_html(fig_json)
    except Exception:
        return html.Em('Unavailable')


@dash.callback(
    Output('daily_index_asset_id_t7k', 'children'),
    Input('asset_ids_risk_alloc_t7k', 'value'))
def find_daily_index_asset_id_t7k(asset_id_t7k):
    # Use the daily-filtered aggregation (consistent with RTS)
    index = asset_allocs_t7k_day[asset_id_t7k]
    return f'{asset_id_t7k}: {index:.2f}'

@dash.callback(
    Output('asset_id_in_plot_title_t7k', 'children'),
    Input('asset_ids_risk_alloc_t7k', 'value'))
def set_asset_id_in_plot_title_t7k(asset_id_t7k):
    return f'{asset_id_t7k}'