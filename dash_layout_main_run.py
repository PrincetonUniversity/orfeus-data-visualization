import dash_bootstrap_components as dbc

from dash import dcc, html, Input, Output, State

from app import app
from pages.data_visualization.scenarios import html_div_scenariovisualize
from pages.data_visualization.risk_allocation import html_div_risk_allocation
from pages.data_visualization.lmps import html_div_lmps

projecturl = 'https://orfeus.princeton.edu/'

navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand("ORFEUS Data Visualization", href="/"),
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        dbc.Collapse(
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Scenarios Visualization", href="/scenariovisualize", active="exact")),
                dbc.NavItem(dbc.NavLink("Risk Allocation Plot", href="/riskallocplot", active="exact")),
                dbc.NavItem(dbc.NavLink("LMP Geographical Visualization", href="/lmpplot", active="exact")),
            ], className="ms-auto", navbar=True),
            id="navbar-collapse",
            is_open=False,
            navbar=True,
        ),
    ], fluid=True),
    dark=False,
    className="dbc-navbar"
)


content = html.Div(id='page-content', children=[], className='app-content')

app.layout = html.Div(
                      children=[
                          dcc.Store(id='side_click'),
                          dcc.Location(id='url'),
                          navbar,
                          # sidebar,
                          content
                      ])


# Landing page for Data Visualization
html_div_datavis_landing = html.Div(children=[
    html.H1("Data Visualization", className='title'),
    html.Div([
        dcc.Markdown(
            children=(
                "Our data visualization suite includes Scenarios Visualization with options for day, "
                "asset type, and asset ID, Risk Allocation Plot, and LMP Geographic Plots to explore "
                "how LMPs distribute geographically."
            ),
            className='markdown',
        ),
        html.Hr(),
        html.Ul([
            html.Li(html.A("Scenarios Visualization", href="/scenariovisualize")),
            html.Li(html.A("Risk Allocation Plot", href="/riskallocplot")),
            html.Li(html.A("LMP Geographical Visualization", href="/lmpplot")),
        ]),
    ], className='section')
], className='app-content')


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

# Toggle the navbar collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"),
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not (is_open or False)
    return is_open

# Add this to make all errors disappear on the right corner: dev_tools_ui=False,dev_tools_props_check=False
if __name__ == '__main__':
    app.run_server(debug=True, port=8055, dev_tools_ui=False,
                   dev_tools_props_check=False)
    # app.run_server(debug=True, port = 8055)
# click red square botton to stop server

