import pandas as pd
from datetime import date, timedelta, datetime
from dash import html, dcc, Input, Output, ctx
import plotly.express as px

import dash_bootstrap_components as dbc

from styles.styles import TITLE_STYLE, INDEX_TITLE_STYLE, INDEX_NUM_STYLE, WHITE_BUTTON_STYLE, CONTENT_STYLE, \
    DROPDOWN_STYLE_LONG,  TAB_STYLE, TABS_STYLES, TAB_SELECTED_STYLE, MARKDOWN_STYLE, \
    colors, colors_type
from inputs.inputs import type_allocs_rts, asset_allocs_rts, type_allocs_t7k, asset_allocs_t7k
from markdown.allocation import markdown_text_riskalloc
from app import app

today = date.today()
yesterdate_verbal = (today - timedelta(1)).strftime("%b %d, %Y").split(',')[0]
yesterdate = (today - timedelta(1)).strftime("%y-%m-%d")[3:]

todaydate_verbal = today.strftime("%b %d, %Y").split(',')[0]
todaydate = today.strftime("%y-%m-%d")[3:]

# Risk Alloc Asset IDs
asset_ids_risk_alloc_rts = asset_allocs_rts.columns[1:]
asset_ids_risk_alloc_t7k = asset_allocs_t7k.columns[1:]

# Calculate daily index by taking the avg of hourly index
start_date = datetime.strptime('2020-' + yesterdate, "%Y-%m-%d")
end_date = start_date + timedelta(hours=23)
daterange_rts = pd.date_range(start_date, end_date, freq='H')

start_date = datetime.strptime('2018-' + yesterdate, "%Y-%m-%d")
end_date = start_date + timedelta(hours=23)
daterange_t7k = pd.date_range(start_date, end_date, freq='H')

type_allocs_rts_day = type_allocs_rts[
    type_allocs_rts['time'].isin(daterange_rts)].set_index(['time']).mean()
asset_allocs_rts_day = asset_allocs_rts[
    asset_allocs_rts['time'].isin(daterange_rts)].set_index(['time']).mean()
type_allocs_t7k_day = type_allocs_t7k[
    type_allocs_t7k['time'].isin(daterange_t7k)].set_index(['time']).mean()
asset_allocs_t7k_day = asset_allocs_t7k[
    asset_allocs_t7k['time'].isin(daterange_t7k)].set_index(['time']).mean()

html_div_risk_allocation_overview =  html.Div(children=[

                html.H1(
                    children='Risk Allocation',
                    style=TITLE_STYLE
                ),

                html.Div([
                    dcc.Markdown(children=markdown_text_riskalloc,
                                 style=MARKDOWN_STYLE)
                ],
                    style={'padding': '20px'})
            ],
                style=CONTENT_STYLE)

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
            html.H3(
                children='Asset Type Reliability Cost Index on {}'.format(
                    yesterdate_verbal),
                style=INDEX_TITLE_STYLE),
        ])
        , justify='start', align='start')

    dbc_solar_index = dbc.Row(
        dbc.Col([
            html.H3(
                children='{}: {:.2f}'.format('Solar',
                                             type_allocs_pv_day),
                style=INDEX_NUM_STYLE)
        ]),
        justify='start', align='start')

    dbc_wind_index = dbc.Row(
        dbc.Col([
            html.H3(
                children='{}: {:.2f}'.format('Wind',
                                             type_allocs_wind_day),
                style=INDEX_NUM_STYLE)
        ]),
        justify='start', align='start')

    # change b/w asset id
    if label == 'RTS':
        dbc_rtpv_index = dbc.Row(
            dbc.Col([
                html.H3(children='{}: {:.2f}'.format(
                    'Rooftop Solar',
                    type_allocs_rtpv_day),
                    style=INDEX_NUM_STYLE)
            ])
            , justify='start', align='start')


    if label == 'RTS':
        asset_level_index_title = 'Asset Level Reliability Cost Index on {}'.format(
                        yesterdate_verbal)
    else:
        asset_level_index_title = 'Average of Asset Level Reliability Cost Index Across Days'

    html_asset_level_index = html.Div(children = [
        dbc.Row(
            dbc.Col([
                html.Br(),
                html.H3(
                    children=asset_level_index_title,
                    style=INDEX_TITLE_STYLE)
            ]),
            justify='start', align='start'),

        dbc.Row([
            dbc.Col([
                html.Div(
                    className="four columns pretty_container",
                    children=[
                        html.Label('Select Asset Id'),
                        dcc.Dropdown(
                            asset_ids,
                            placeholder='Asset ID',
                            id=asset_ids_id,
                            value=asset_ids[0],
                            style=DROPDOWN_STYLE_LONG)
                    ])
            ])]),

        dbc.Row(
            dbc.Col([
                html.Br(),
                html.Div(id=daily_index_asset_id,
                         style=INDEX_NUM_STYLE),
                html.Br()
            ])
            , justify='start', align='start'),

        html.Hr()
    ])

    html_asset_level_plot = html.Div(children = [
        dbc.Row(
            dbc.Col([
                html.Br(),
                html.H3(
                    children=[
                        'Hourly Time Series of Asset Level Reliability Cost Index for ',

                        html.Div(
                            id=asset_id_in_plot_title,
                            style={'display': 'inline'})

                    ],
                    style=INDEX_TITLE_STYLE)
            ]),
            justify='start', align='start'),

        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Button('1 day',
                                id=button_id_day_asset_alloc,
                                n_clicks=0,
                                style=WHITE_BUTTON_STYLE),

                    html.Button('1 week',
                                id=button_id_week_asset_alloc,
                                n_clicks=0,
                                style=WHITE_BUTTON_STYLE),

                    html.Button('historical',
                                id=button_id_hist_asset_alloc,
                                n_clicks=0,
                                style=WHITE_BUTTON_STYLE),
                    html.Div(
                        id='container-button-timestamp')
                ])
            )
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id=fig_id_asset_alloc,
                    style={'padding-left': '10px'}
                )
            ]),

        ],
            justify='start',
            align='start')

    ])

    html_asset_type_plot = html.Div(
    children = [
        dbc.Row(
            dbc.Col([
                html.Br(),
                html.H3(
                    children='Hourly Time Series of Asset Type Reliability Cost Index',
                    style=INDEX_TITLE_STYLE)
            ]),
            justify='start', align='start'),

        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Button('1 day',
                                id=button_id_day_type_alloc,
                                n_clicks=0,
                                style=WHITE_BUTTON_STYLE),

                    html.Button('1 week',
                                id=button_id_week_type_alloc,
                                n_clicks=0,
                                style=WHITE_BUTTON_STYLE),

                    html.Button('historical',
                                id=button_id_hist_type_alloc,
                                n_clicks=0,
                                style=WHITE_BUTTON_STYLE),
                    html.Div(
                        id='container-button-timestamp')
                ])
            )
        ]),

        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    # figure=plot_mean_asset_type_risk_alloc(type_allocs_rts),
                    id=fig_id_type_alloc,
                    style={'padding-left': '10px'}
                ))
        ],
            justify='start'),

        html.Hr()
    ])

    if label == 'RTS':
        tab_children = [dbc_asset_type_title, dbc_rtpv_index, dbc_solar_index, dbc_wind_index,
                        html_asset_level_index, html_asset_type_plot, html_asset_level_plot]
    else:
        tab_children = [dbc_asset_type_title, dbc_solar_index, dbc_wind_index,
                        html_asset_level_index, html_asset_type_plot, html_asset_level_plot]

    dcc_tab = dcc.Tab(label= label, children=tab_children,
                                    style=TAB_STYLE,
                                    selected_style=TAB_SELECTED_STYLE)
    return dcc_tab

html_div_risk_allocation = html.Div(children=[
                dbc.Row(
                    dbc.Col(html.H3(children='Reliability Cost Index',
                                    style=TITLE_STYLE))
                    , justify='start', align='start'),

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

                    ],
                    style=TABS_STYLES
                ),
                    justify='between')
            ], style=CONTENT_STYLE)

def plot_mean_asset_type_risk_alloc(type_allocs, version='RTS', period='1day',
                                    level='asset_type', asset_id=None):
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

    if period == 'hist':
        fig_type_allocs = px.line(type_allocs, x='time', y=y_,
                                  hover_data={"time": "|%H, %b %d"})
        fig_type_allocs.update_xaxes(tickformat='%H \n %b %d, %Y',
                                     title_font_size=25)

    else:
        end_date = datetime.strptime(startyear_ + todaydate, "%Y-%m-%d")
        if period == '1day':
            if version == 'RTS':
                delta = timedelta(days=1)
                daterange = pd.date_range(end_date - delta, end_date, freq='H')
                type_allocs_day = type_allocs[type_allocs['time'].isin(daterange)]
            else:
                type_allocs_day = type_allocs.iloc[-24:, ]
            fig_type_allocs = px.line(type_allocs_day, x='time', y=y_,
                                      hover_data={"time": "|%H, %b %d"})
            fig_type_allocs.update_xaxes(tickformat='%H \n %b %d',
                                         title_font_size=25)

        elif period == '1week':
            if version == 'RTS':
                delta = timedelta(weeks=1)
                daterange = pd.date_range(end_date - delta, end_date, freq='H')
                type_allocs_day = type_allocs[type_allocs['time'].isin(daterange)]
            else:
                type_allocs_day = type_allocs.iloc[-24*7:, ]
            fig_type_allocs = px.line(type_allocs_day, x='time', y=y_,
                                      hover_data={"time": "|%H, %b %d"})
            fig_type_allocs.update_xaxes(tickformat='%H \n %b %d',
                                         title_font_size=25)

    fig_type_allocs.data[0].name = 'Wind'
    fig_type_allocs.data[0].line.color = colors_type['Wind']

    if level == 'asset_type':
        fig_type_allocs.data[1].name = 'Solar'
        fig_type_allocs.data[1].line.color = colors_type['Solar']
        if version == 'RTS':
            fig_type_allocs.data[2].name = 'Rooftop Solar'
            fig_type_allocs.data[2].line.color = colors_type['Rooftop Solar']

    fig_type_allocs.update_layout(
        # title='Hourly Time Series of {} Asset Type Reliability Cost Index, updated on {}'.format(version, todaydate_verbal),
        xaxis_title='Date',
        yaxis_title='Reliability Cost Index ($)',
        legend_title='Asset Type',
        font_family='sans-serif', font_color=colors['text_1'],
        title_font_color=colors['plottitle'],
        legend=dict(x=1, y=1), legend_font_size=20, title_font_size=25,
        font_size=16,
        plot_bgcolor=colors['lightbackground'],
        paper_bgcolor=colors['background'])

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

    fig_type_allocs.update_yaxes(
        title_font_size=25)
    return fig_type_allocs


@app.callback(
    Output("fig_mean_asset_type_risk_alloc_rts", "figure"),
    Input('rts-type-allocs-1day', 'n_clicks'),
    Input('rts-type-allocs-1week', 'n_clicks'),
    Input('rts-type-allocs-hist', 'n_clicks')
)
def plot_mean_asset_type_risk_alloc_daterange(btn1, btn2, btn3):
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
    return fig


@app.callback(
    Output('fig_asset_risk_alloc_rts', 'figure'),
    Input('asset_ids_risk_alloc_rts', 'value'),
    Input('rts-asset-allocs-1day', 'n_clicks'),
    Input('rts-asset-allocs-1week', 'n_clicks'),
    Input('rts-asset-allocs-hist', 'n_clicks')
)
def asset_ids_risk_alloc(asset_id, button1, button2, button3):
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
    return fig_asset_allocs


@app.callback(
    Output('daily_index_asset_id_rts', 'children'),
    Input('asset_ids_risk_alloc_rts', 'value'))
def find_daily_index_asset_id_rts(asset_id):
    index = asset_allocs_rts_day[asset_id]
    return f'{asset_id}: {index:.2f}'

@app.callback(
    Output('asset_id_in_plot_title_rts', 'children'),
    Input('asset_ids_risk_alloc_rts', 'value'))
def find_daily_index_asset_id(asset_id):
    return f'{asset_id}'



@app.callback(
    Output("fig_mean_asset_type_risk_alloc_t7k", "figure"),
    Input('t7k-type-allocs-1day', 'n_clicks'),
    Input('t7k-type-allocs-1week', 'n_clicks'),
    Input('t7k-type-allocs-hist', 'n_clicks')
)
def plot_mean_asset_type_risk_alloc_daterange(btn1, btn2, btn3):
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
    return fig

@app.callback(
    Output('fig_asset_risk_alloc_t7k', 'figure'),
    Input('asset_ids_risk_alloc_t7k', 'value'),
    Input('t7k-asset-allocs-1day', 'n_clicks'),
    Input('t7k-asset-allocs-1week', 'n_clicks'),
    Input('t7k-asset-allocs-hist', 'n_clicks')
)
def asset_ids_risk_alloc(asset_id, button1, button2, button3):
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
    return fig_asset_allocs


@app.callback(
    Output('daily_index_asset_id_t7k', 'children'),
    Input('asset_ids_risk_alloc_t7k', 'value'))
def find_daily_index_asset_id_t7k(asset_id_t7k):
    index = asset_allocs_t7k[asset_id_t7k].mean()
    return f'{asset_id_t7k}: {index:.2f}'

@app.callback(
    Output('asset_id_in_plot_title_t7k', 'children'),
    Input('asset_ids_risk_alloc_t7k', 'value'))
def find_daily_index_asset_id_t7k(asset_id_t7k):
    return f'{asset_id_t7k}'