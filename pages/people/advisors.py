from dash import html
from styles.styles import CONTENT_STYLE, FONT16_COLORBLACK_STYLE

html_div_advisors = html.Div(
    children = [
        html.H1(
            children='Technical Advisors',
            style={'title_y': 0, 'title_x': 0,
                   'font-size': '40px', 'margin-top': '0px',
                   'color': 'black'}),
        html.H4(
            children = 'Rana Mukerji, Senior Vice President, NYISO',
            style = FONT16_COLORBLACK_STYLE
        ),

        html.Wbr(),

        html.H1(
            children='Industry Advisory Board',
            style={'title_y': 0, 'title_x': 0,
                   'font-size': '40px', 'margin-top': '0px',
                   'color': 'black'}),
        html.H4(
            children='Dinkar Bhatia, Co-Head of North American Power, Hartree Partners, North America',
            style=FONT16_COLORBLACK_STYLE
        ),

        html.Wbr(),

        html.H4(
            children='J.C. Kneale, Vice President, ICE Markets at International Exchange',
            style=FONT16_COLORBLACK_STYLE
        ),

        html.Wbr(),

        html.H4(
            children='Oana Root, Senior Director of Origination, Brookfield Renewable',
            style=FONT16_COLORBLACK_STYLE
        ),

        html.Wbr(),

        html.H4(
            children='Mahesh Morjaria, Executive Vice President, Terabase Energy',
            style=FONT16_COLORBLACK_STYLE
        ),

        html.Wbr(),

        html.H4(
            children='Oana Root, Senior Director of Origination, Brookfield Renewable',
            style=FONT16_COLORBLACK_STYLE
        ),

        html.Wbr(),

        html.H4(
            children='Lori Simpson, Director of Wholesale Market Development, Exelon',
            style=FONT16_COLORBLACK_STYLE
        ),

    ], style = CONTENT_STYLE
)