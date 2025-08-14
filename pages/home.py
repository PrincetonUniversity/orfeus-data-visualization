import dash
from dash import html, dcc

dash.register_page(__name__, path='/', name='Home', order=0)

layout = html.Div([
    html.H1('Data Visualizations', className='title'),
    html.Div([
        dcc.Markdown(
            'Explore scenarios, risk allocation, and geographic LMPs using the pages in the navigation bar.',
            className='markdown'
        ),
        html.Hr(),
        html.Ul([
            html.Li(html.A('Scenarios Visualization', href='/scenariovisualize')),
            html.Li(html.A('Risk Allocation Plot', href='/riskallocplot')),
            html.Li(html.A('LMP Geographical Visualization', href='/lmpplot')),
        ]),
    ], className='section')
], className='app-content')
