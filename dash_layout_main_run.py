import dash_bootstrap_components as dbc

from dash import dcc, html, Input, Output

from app import app
from styles.styles import colors, CONTENT_STYLE, DASH_STYLE
from pages.data_visualization.scenarios import html_div_scenariooverview, html_div_scenariovisualize
from pages.data_visualization.risk_allocation import html_div_risk_allocation_overview, html_div_risk_allocation
from pages.data_visualization.lmps import html_div_lmps_overview, html_div_lmps
from pages.data_download.data_download import html_div_datadownload
from pages.next_steps import html_div_next_steps
from pages.people import html_div_pi, html_div_staff, html_div_advisors
from pages.home import html_div_home
from pages.perform import html_div_perform

projecturl = 'https://orfeus.princeton.edu/'

navbar = dbc.NavbarSimple(
    children=[
        # dbc.Button("Sidebar", outline=True, color="secondary",
        #            className="mr-1", id="btn_sidebar"),
        dbc.NavItem(dbc.NavLink("Home", href="/")),

        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("People", header=True),
                dbc.DropdownMenuItem("Principal Investigators",
                                     href="/principalinvestigators"),
                dbc.DropdownMenuItem("Research Staff",
                                     href="/researchstaff"),
                dbc.DropdownMenuItem("Advisors",
                                     href="/advisors")
            ],
            nav=True,
            in_navbar=True,
            label='People',
        ),

        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Data Visualization", header=True),
                dbc.DropdownMenuItem("Scenarios Visualization", href="/scenariovisualize"),
                dbc.DropdownMenuItem("Risk Allocation Plot", href="riskallocplot"),
                dbc.DropdownMenuItem("LMP Geographical Visualization", href="lmpplot")
            ],
            nav=True,
            in_navbar=True,
            label="Data Visualization",
        ),

        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Data Download", header=True),
                dbc.DropdownMenuItem("Data Download", href="/datadownload"),
            ],
            nav=True,
            in_navbar=True,
            label="Data Download",
        ),
        dbc.NavItem(dbc.NavLink("Next Steps", href="/nextsteps")),
        dbc.NavItem(dbc.NavLink("PERFORM", href="/perform")),
    ],
    brand=" Operational Risk Financialization of Electricity Under Stochasticity",
    brand_href="#",
    color=colors['heavybackground'],
    dark=True,
    # fixed='top',
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


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def render_page_content(pathname):
    if pathname == '/':
        return [
            html_div_home
        ]
    elif pathname == '/scenariooverview':
        return [
                html_div_scenariooverview
        ]

    elif pathname == '/scenariovisualize':
        return [
                html_div_scenariovisualize
        ]
    elif pathname == '/riskallocoverview':
        return [
            html_div_risk_allocation_overview
        ]
    elif pathname == '/riskallocplot':
        return [
            html_div_risk_allocation
        ]
    elif pathname == '/lmpoverview':
        return[
                html_div_lmps_overview
        ]

    elif pathname == '/lmpplot':
        return [
            html_div_lmps
        ]

    elif pathname == '/datadownload':
        return [
            html_div_datadownload
        ]
    elif pathname == '/nextsteps':
        return [
            html_div_next_steps
        ]
    elif pathname == '/principalinvestigators':
        return [
            html_div_pi
        ]
    elif pathname == '/researchstaff':
        return[
            html_div_staff
        ]
    elif pathname == '/advisors':
        return[
            html_div_advisors
        ]
    elif pathname == '/perform':
        return [
            html_div_perform
        ]

# Add this to make all errors disappear on the right corner: dev_tools_ui=False,dev_tools_props_check=False
if __name__ == '__main__':
    app.run_server(debug=True, port=8055, dev_tools_ui=False,
                   dev_tools_props_check=False)
    # app.run_server(debug=True, port = 8055)
# click red square botton to stop server

