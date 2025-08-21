from utils.ui import dash, html, dcc
from utils.md import load_markdown

dash.register_page(__name__, path='/', name='Home', order=0)

markdown_text_home = load_markdown('markdown', 'home.md')

layout = html.Section([
    html.Div([
    dcc.Markdown(markdown_text_home, className='markdown'),
    ], className='section')
], className='app-content')
