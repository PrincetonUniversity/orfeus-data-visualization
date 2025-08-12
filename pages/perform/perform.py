from dash import dcc, html, Input, Output, State, dash_table, ctx

from styles.styles import MARKDOWN_STYLE_PEOPLE, CONTENT_STYLE

from markdown.perform import markdown_text_perform

html_div_perform = html.Div(children = [
    html.Div([
        html.H1(
            children='PERFORM'),
    ], style={'textAlign': 'center'}),

    dcc.Markdown(
        children=markdown_text_perform,
        style=MARKDOWN_STYLE_PEOPLE),

], style = CONTENT_STYLE)