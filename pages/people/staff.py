from dash import html
from styles.styles import CONTENT_STYLE

from markdown.people import markdown_text_xinshuo, markdown_text_michal, \
    markdown_text_junying, markdown_text_guillermo
from .principals import people_component

html_div_staff =  html.Div(
                children = [
                    html.H1(
                        children='Research Staff',
                        style={'title_y': 0, 'title_x': 0,
                               'font-size': '40px', 'margin-top': '0px',
                               'color': 'black'}),

                    html.Wbr(),

                    people_component(img_link='assets/xinshuo.png',
                                     name='Xinshuo Yang',
                                     title="POSTDOCTORAL RESEARCH ASSOCIATE",
                                     markdown_text = markdown_text_xinshuo),

                    html.Wbr(),

                    people_component(img_link='assets/michal.png',
                                     name='Michal Grazdkowski',
                                     title="SENIOR RESEARCH SOFTWARE ENGINEER",
                                     markdown_text=markdown_text_michal),

                    html.Wbr(),

                    people_component(img_link='assets/junying.jpeg',
                                     name='Junying (Alice) Fang',
                                     title="RESEARCH SOFTWARE ENGINEER",
                                     markdown_text=markdown_text_junying),

                    html.Wbr(),

                    people_component(img_link='assets/guillermo.jpeg',
                                     name='Guillermo Terrén-Serrano',
                                     title="POSTDOCTORAL RESEARCH ASSOCIATE",
                                     markdown_text=markdown_text_guillermo),
                ], style = CONTENT_STYLE
            )