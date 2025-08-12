from dash import html, dcc
import dash_bootstrap_components as dbc

from styles.styles import TITLE_STYLE, CONTENT_STYLE, MARKDOWN_STYLE
from markdown.next_steps import markdown_text_next_steps

html_div_next_steps = html.Div(children=[

                html.H1(
                    children='Next Steps of the ORFEUS Project',
                    style=TITLE_STYLE
                ),

                dbc.Row(
                    dbc.Col([
                        html.Br(),
                        dcc.Markdown(
                            children=markdown_text_next_steps,
                            style=MARKDOWN_STYLE),
                    ]), justify='start', align='start'),

            ], style=CONTENT_STYLE)