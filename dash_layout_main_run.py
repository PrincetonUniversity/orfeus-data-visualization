import dash_bootstrap_components as dbc

from dash import dcc, html, Input, Output

from app import app
from styles.styles import colors, CONTENT_STYLE, DASH_STYLE, TITLE_STYLE, MARKDOWN_STYLE
from pages.data_visualization.scenarios import html_div_scenariovisualize
from pages.data_visualization.risk_allocation import html_div_risk_allocation
from pages.data_visualization.lmps import html_div_lmps

projecturl = 'https://orfeus.princeton.edu/'

navbar = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Data Visualization", href="/"),
                dbc.DropdownMenuItem("Scenarios Visualization", href="/scenariovisualize"),
                dbc.DropdownMenuItem("Risk Allocation Plot", href="/riskallocplot"),
                dbc.DropdownMenuItem("LMP Geographical Visualization", href="/lmpplot")
            ],
            nav=True,
            in_navbar=True,
            label="Data Visualization",
        ),
    ],
    brand="ORFEUS Data Visualization",
    brand_href="/",
    color=colors['background_navgbar'],
    dark=False,
    fluid=True
)


content = html.Div(id='page-content', children=[], style=CONTENT_STYLE)

app.layout = html.Div(style=DASH_STYLE,
                      children=[
                          dcc.Store(id='side_click'),
                          dcc.Location(id='url'),
                          navbar,
                          # sidebar,
                          content
                      ])


# Landing page for Data Visualization
html_div_datavis_landing = html.Div(children=[
    html.H1("Data Visualization", style=TITLE_STYLE),
    html.Div([
        dcc.Markdown(
            children=(
                "Our data visualization suite includes Scenarios Visualization with options for day, "
                "asset type, and asset ID, Risk Allocation Plot, and LMP Geographic Plots to explore "
                "how LMPs distribute geographically."
            ),
            style=MARKDOWN_STYLE,
        ),
        html.Hr(),
        html.Ul([
            html.Li(html.A("Scenarios Visualization", href="/scenariovisualize")),
            html.Li(html.A("Risk Allocation Plot", href="/riskallocplot")),
            html.Li(html.A("LMP Geographical Visualization", href="/lmpplot")),
        ]),
    ], style={'padding': '20px'})
], style=CONTENT_STYLE)


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def render_page_content(pathname):
    if pathname == '/' or pathname is None:
        return [html_div_datavis_landing]
    elif pathname == '/scenariovisualize':
        return [
                html_div_scenariovisualize
        ]
    elif pathname == '/riskallocplot':
        return [
            html_div_risk_allocation
        ]
    elif pathname == '/lmpplot':
        return [
            html_div_lmps
        ]
    # default fallback to landing
    return [html_div_datavis_landing]

# Add this to make all errors disappear on the right corner: dev_tools_ui=False,dev_tools_props_check=False
if __name__ == '__main__':
    app.run_server(debug=True, port=8055, dev_tools_ui=False,
                   dev_tools_props_check=False)
    # app.run_server(debug=True, port = 8055)
# click red square botton to stop server

