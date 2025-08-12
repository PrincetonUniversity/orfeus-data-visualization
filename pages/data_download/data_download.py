from dash import html, dcc
import dash_bootstrap_components as dbc

from styles.styles import TITLE_STYLE, CONTENT_STYLE, DOWNLOAD_TITLE_STYLE, MARKDOWN_STYLE
from markdown.data_download import markdown_text_datadownload_scenarios, markdown_text_datadownload_costindex, \
        markdown_text_datadownload_lmp, markdown_text_datadownload_globus, \
        markdown_link_datadownload_scenarios, markdown_link_datadownload_costindex, \
        markdown_link_datadownload_lmp, markdown_link_datadownload_globus

def dbc_download(title = 'Data Transfer with Globus', markdown_text = markdown_text_datadownload_globus,
                 markdown_link = markdown_link_datadownload_globus):
    dbc_download = dbc.Row(
        dbc.Col([
            html.Br(),
            html.H4(children=title,
                    style=DOWNLOAD_TITLE_STYLE),
            dcc.Markdown(
                children=markdown_text,
                style=MARKDOWN_STYLE),
            dcc.Markdown(markdown_link,
                         link_target="_blank"),
        ])
        , justify='start', align='start')
    return dbc_download

html_div_datadownload =  html.Div(children=[

                html.H1(
                    children='Download ORFEUS Project Data',
                    style=TITLE_STYLE
                ),

                dbc_download(title = 'Scenarios Data', markdown_text = markdown_text_datadownload_scenarios,
                    markdown_link = markdown_link_datadownload_scenarios),

                dbc_download(title='Reliability Cost Index Data',
                             markdown_text=markdown_text_datadownload_costindex,
                             markdown_link=markdown_link_datadownload_costindex),

                dbc_download(title='Locational Marginal Price Data',
                             markdown_text=markdown_text_datadownload_lmp,
                             markdown_link=markdown_link_datadownload_lmp),

                dbc_download(title='Data Transfer with Globus',
                             markdown_text=markdown_text_datadownload_globus,
                             markdown_link=markdown_link_datadownload_globus),

            ], style=CONTENT_STYLE)