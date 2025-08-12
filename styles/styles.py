colors = {
    'background': 'white',
    'heavybackground': '#119DFF',
    'lightbackground': '#F9f9f9',
    'background_navgbar': '#f8f9fa',
    'title': '#3f3f3f',
    'plottitle': 'black',
    'text_1': '#606060',  # main text
    'text_2': '#7FDBFF',  # sub text
    'grid': '#d4dfee',
    'marker': 'rgb(55, 126, 184)',
    'line': ' LightBlue'
}
# background rgb(204, 204, 204)
# F2F2F2

colors_scenario = {
    'actual_tuning': 'rgba(0, 0, 0, 0.7)',
    'forecast_tuning': 'rgba(0, 0, 0, 0.7)',
    'scen_tuning': 'rgba(27,158,119,1)',
    '5per_tuning': 'rgba(27,158,119,0.5)',

    'actual_notuning': 'rgba(0, 0, 255, 0.7)',
    'forecast_notuning': 'rgba(0, 0, 255, 0.7)',
    'scen_notuning': 'rgba(247,129,91,1)',
    '5per_notuning': 'rgba(247,129,91,0.5)',

    'actual_v2': 'black',
    'forecast_v2': 'black',
    'scen_v2': 'rgba(255,127,0,1)',
    '5per_v2': 'rgba(255,127,0,5)',

    'fill': 'rgba(128,128,128,0.8)',
    'vline': 'grey'
}

colors_type = {'Wind': 'rgba(55, 126, 184, 0.5)',
               'Solar': 'rgba(255, 127, 0, 0.5)',
               'Rooftop Solar': 'rgba(166, 86, 40, 0.5)'}

colors_cost = {'nocost': 'rgba(0, 0, 0, 0.8)',
               'withcost': 'rgba(0, 100, 0, 0.8)'}

DASH_STYLE = {'backgroundColor': colors['background'],
              'Color': colors['text_1'],
              'paper_bgcolor': colors['background'], 'margin': 0,
              'margin-top': 0, 'padding': 0, 'height': '100%',
              'font_size': '14px'}

TABS_STYLES = {
    'height': '44px'
}

TAB_STYLE = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px'
}

TAB_SELECTED_STYLE = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': colors['heavybackground'],
    'color': colors['lightbackground'],
    'padding': '6px'
}

TITLE_STYLE = {
    'textAlign': 'center',
    # 'font-weight': 'bold',
    # 'color': '#2FA4EB',
    'title_y': 0,
    'title_x': 0.5,
    'font-size': '40px',
    'margin-top': '0px'}



# navigation sidebar style
MARKDOWN_STYLE = {'text-align': 'left', 'font-size': '20px',
                  "padding": ": '15px"}

MARKDOWN_STYLE_PEOPLE = {'text-align': 'left', 'font-size': '16px',
                  "padding": ": '15px"}

MARKDOWN_STYLE_DOWNLOAD = {'text-align': 'left', 'font-size': '20px',
                           "padding": ": '0px"}

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 62.5,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0.5rem 1rem",
    "background-color": colors['background_navgbar'],
}

SIDEBAR_HIDEN = {
    "position": "fixed",
    "top": 62.5,
    "left": "-16rem",
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0rem 0rem",
    "background-color": colors['background_navgbar'],
}

RADIOITEMS_STYLE = {
    'display': 'Grid',
    'grid-template-columns': 'repeat(2, 3fr)',
    'grid-auto-flow': 'column dense',
    'line-height': '1.1',
    'width': '400px',
    'height': '40px',
    'paddingTop': '0px',
    'paddingLeft': '0px',
    'paddingRight': '10px',
    'gap': '10px',
    'paddingBottom': '0px',
    'border-radius': '50 %',
    'boarder': '0px',
    'color': colors['text_1'],
    'cursor': 'pointer'}

DROPDOWN_STYLE = {
    'background': 'transparent',
    'color': colors['text_1'],
    'width': '200px',
    'paddingLeft': '0px',
    'paddingRight': '0px',
    'paddingBottom': '0px',
    'paddingTop': '0px',
    'marginRight': '0px',
    'position': 'relative'
}

DROPDOWN_STYLE_SIDEBAR = {
    'background': 'transparent',
    'color': colors['background_navgbar'],
    'width': '200px',
    'paddingLeft': '0px',
    'paddingRight': '0px',
    'paddingBottom': '0px',
    'paddingTop': '0px',
    'marginRight': '0px',
    'position': 'relative',
    'boarder': colors['background_navgbar'],
    'borderStyle': 'dashed',
    'font-size': '20px'
}

DROPDOWN_STYLE_LONG = {
    'background': 'transparent',
    'color': colors['text_1'],
    'width': '400px',
    'paddingLeft': '0px',
    'paddingRight': '0px',
    'paddingBottom': '0px',
    'paddingTop': '0px',
    'marginRight': '0px',
    'position': 'relative'
}

WHITE_BUTTON_STYLE = {'background-color': colors['lightbackground'],
                      'color': colors['text_1'],
                      'height': '30px',
                      'width': '80px',
                      'margin-top': '0px',
                      'margin-right': '10px',
                      'border': '0px'}

CONTENT_STYLE = {
    "top": 62.5,
    "transition": "margin-left .5s",
    'margin-left': '3rem',
    'margin-right': '3rem',
    'margin-top': '0rem',
    'padding': '0.5rem 0rem 0rem 0rem',
    'textAlign': 'left',
    'color': colors['text_1'],
    'background': colors['background']
}

CONTENT_STYLE1 = {
    "transition": "margin-left .5s",
    'margin-left': '2rem',
    'margin-right': '0rem',
    'margin-top': '0rem',
    'padding': '0.5rem 0rem 0rem 0rem',
    'textAlign': 'left',
    'color': colors['text_1'],
    'background': colors['background']
}

CONTENT_STYLE_IMAG = {
    "top": 62.5,
    "transition": "margin-left .5s",
    'margin-left': '3rem',
    'margin-right': '3rem',
    'margin-top': '0rem',
    'padding': '0.5rem 0rem 0rem 0rem',
    'textAlign': 'left',
    'color': colors['text_1'],
    'background': colors['background'],
    'background-image': 'url(windmills_background.png)'
}

SMALL_TITLE_STYLE = {'font-size': 16, 'font-weight': 'bold', 'color': 'black',
                  'padding-left': '0px'}

INDEX_TITLE_STYLE = {'color': 'black', 'font-size': '30px',
                     'padding-left': '0px'}

DOWNLOAD_TITLE_STYLE = {'color': colors['text_1'], 'font-size': '30px',
                        'padding-left': '0px'}

INDEX_NUM_STYLE = {'font-size': '20px', 'color': colors['text_1'],
                   'padding-left': '20px'}

CITATION_STYLE = {'font-size': 12, 'font-weight': 'bold', 'color': 'black',
                  'padding-left': '20px'}

NAME_STYLE = {'font-size': 26,  'color': 'black',
                  'padding-left': '0px'}

FONT16_COLORBLACK_STYLE = {'font-size': 16, 'color': 'black',
                  'padding-left': '0px'}
