import dash_bootstrap_components as dbc
from dash import dcc, html
from styles.styles import NAME_STYLE, SMALL_TITLE_STYLE, MARKDOWN_STYLE_PEOPLE,\
CONTENT_STYLE

from markdown.people import markdown_text_carmona, \
    markdown_text_sircar, markdown_text_ludkovski, markdown_text_swindle

def people_component(img_link, name, title, markdown_text):
    comp = dbc.Row(
        [
            dbc.Col([
                html.Img(src=img_link,
                         style={'height': '90%', 'width': '90%'})
            ], width=3),

            dbc.Col([
                html.H3(name, style=NAME_STYLE),
                html.H4(
                    title,
                    style=SMALL_TITLE_STYLE),
                dcc.Markdown(
                    children=markdown_text,
                    style=MARKDOWN_STYLE_PEOPLE),
            ]),
        ],
        justify='start', align='start')
    return comp

html_div_pi =  html.Div(
                children = [
                    html.H1(
                        children='Principal Investigators',
                        style={'title_y': 0, 'title_x': 0,
                               'font-size': '40px', 'margin-top': '0px',
                               'color': 'black'}),

                    html.Wbr(),

                    people_component(img_link='assets/carmona.jpeg',
                                     name='Rene Carmona',
                                     title="PAUL M. WYTHES ’55 PROFESSOR OF ENGINEERING AND SCIENCE",
                                     markdown_text = markdown_text_carmona),

                    html.Wbr(),

                    people_component(img_link='assets/sircar.jpeg',
                                     name='Ronnie Sircar',
                                     title="EUGENE HIGGINS PROFESSOR OF \
                                           OPERATIONS RESEARCH AND FINANCIAL ENGINEERING \
                                           AT PRINCETON UNIVERSITY",
                                     markdown_text=markdown_text_sircar),

                    html.Wbr(),

                    people_component(img_link='assets/ludkovski.jpeg',
                                     name='Michael Ludkovski',
                                     title="PROFESSOR OF STATISTICS AND APPLIED PROBABILITY DEPARTMENT AT UC SANTA BARBARA",
                                     markdown_text=markdown_text_ludkovski),

                    html.Wbr(),

                    people_component(img_link='assets/swindle.jpeg',
                                     name='Glen Swindle',
                                     title="SCOVILLE RISK PARTNERS",
                                     markdown_text=markdown_text_swindle),
                ], style = CONTENT_STYLE
            )