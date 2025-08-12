import dash_bootstrap_components as dbc
from dash import dcc, html

from styles.styles import CONTENT_STYLE, MARKDOWN_STYLE_PEOPLE
from markdown.home import markdown_text_project, \
        markdown_text_scenarios, markdown_text_simulation,\
        markdown_text_risk, markdown_text_commercial

html_div_end = html.Div(
    children = [
        dbc.Row(
            [
                dbc.Col([
                    html.H1(
                        children='ORFEUS',
                        style={'font-size': '20px', 'font-weight': 'bold',
                               'color': 'black'}),

                    html.H4(children = 'ORFEUS — Operational Risk Financialization of \
                        Electricity Under Stochasticity — is the Princeton University perform team.',
                    style = {'font-size': '16px', 'color': '#606060'})
                ]),

                dbc.Col([
                    html.H1(
                        children='Contact',
                        style={'font-size': '20px', 'font-weight': 'bold',
                               'color': 'black'}),

                    html.H4(children = 'Please contact us via jf3375@princeton.edu',
                            style = {'font-size': '16px', 'color': '#606060'}
                            )
                ]),
            ]
            , justify='start'),

        html.Wbr(),

        dbc.Row(
            [
                dbc.Col([
                    html.Img(src='assets/pu.png',
                             style={'height': '80%', 'width': '100%'}),
                ]),

                dbc.Col([
                    html.Img(src='assets/ucsb.png',
                             style={'height': '80%', 'width': '100%'}),
                ]),

                dbc.Col([
                    html.Img(src='assets/scoville.jpg',
                             style={'height': '80%', 'width': '100%'}),
                ]),

                dbc.Col([
                    html.Img(src='assets/arpa.jpg',
                             style={'height': '80%', 'width': '100%'}),
                ]),
            ]
            , justify='evenly'),

    ], style = CONTENT_STYLE
)


html_div_home = html.Div(
    children = [
        html.Div([
        html.Img(src='assets/orfeus-logo.png',
                         style={'height': '50%', 'width': '50%'}),
        ], style={'textAlign': 'center'}),

        html.Wbr(),

        html.Div([
        html.H1(
            children='About the Project',
            style={'font-size': '40px', 'font-weight': 'bold',
                   'margin-top': '0px', 'color': 'black'}),
        ], style={'textAlign': 'center'}),

        dbc.Row(
            [
                dbc.Col([
                    html.Img(src='assets/aboutproject.jpg',
                             style={'height': '100%', 'width': '100%'})
                ], width=4),

                dbc.Col([
                    dcc.Markdown(
                        children=markdown_text_project,
                        style=MARKDOWN_STYLE_PEOPLE),
                ]),
            ],
            justify='start', align='start'),

        html.H3(children = 'A Stochastic Model Capturing Correlations',
                style = {'color': 'black'}),

        dcc.Markdown(
            children=markdown_text_scenarios,
            style=MARKDOWN_STYLE_PEOPLE),

        dbc.Row(
            [
                dbc.Col([
                    html.Img(src='assets/load.png',
                             style={'height': '100%', 'width': '100%'})
                ]),

                dbc.Col([
                    html.Img(src='assets/wind.png',
                             style={'height': '100%', 'width': '100%'})
                ]),

                dbc.Col([
                    html.Img(src='assets/solar.png',
                             style={'height': '100%', 'width': '100%'})
                ]),
            ]
        , justify = 'evenly'),

        html.Wbr(),
        html.Wbr(),

        html.H3(children='A Monte Carlo Simulation Platform',
                style={'color': 'black'}),

        dcc.Markdown(
            children=markdown_text_simulation,
            style=MARKDOWN_STYLE_PEOPLE),

        html.Img(src='assets/montecarlo.jpg',style={'height': '100%', 'width': '100%'}),

        html.Wbr(),
        html.Wbr(),

        html.H3(children='Financial Risk Measures Reliability Indices',
                style={'color': 'black'}),

        dcc.Markdown(
            children=markdown_text_risk,
            style=MARKDOWN_STYLE_PEOPLE),

        html.Img(src='assets/risk.png',
                 style={'height': '30%', 'width': '30%'}),

        html.Wbr(),
        html.Wbr(),

        html.H3(children='Transition to Market and Pilot',
                style={'color': 'black'}),

        dcc.Markdown(
            children=markdown_text_commercial,
            style=MARKDOWN_STYLE_PEOPLE),

        html.Img(src='assets/transitiontomkt.jpg',
                 style={'height': '80%', 'width': '80%'}),

        html.Hr(),

        html_div_end

    ], style = CONTENT_STYLE)
