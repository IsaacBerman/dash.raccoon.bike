"""
This app creates a simple sidebar layout using inline style arguments and the
dbc.Nav component.

dcc.Location is used to track the current location, and a callback uses the
current location to render the appropriate page content. The active prop of
each NavLink is set automatically according to the current pathname. To use
this feature you must install dash-bootstrap-components >= 0.11.0.

For more details on building multi-page Dash applications, check out the Dash
documentation: https://dash.plot.ly/urls
"""
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from whitenoise import WhiteNoise


import base64

import bikeraccoon as br

from layouts import *

base_url = 'https://dash.mikejarrett.ca'

#encoded_logo = base64.b64encode(open('static/logo.png', 'rb').read())
app = dash.Dash(__name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        meta_tags=[
            {'name':"twitter:card", 'content':"summary_large_image"},
             {'name':"twitter:site", 'content':"@VanBikeShareBot"},
             {'name':"twitter:creator", 'content':"@mikejarrett_"},
             {'name':"twitter:title", 'content':"raccoon.bike"},
             {'name':"twitter:description", 'content':"Live tracking of public bikeshare systems"},
             {'name':"twitter:image" , 'content':f'{base_url}/assets/logo.png'},
             {'property':"og:url", 'content':"https://dash.raccoon.bike"},
             {'property':"og:title", 'content':"raccoon.bike"},
             {'property':"og:description", 'content':"Live tracking of public bikeshare systems"},
             {'property':"og:image" , 'content':f'{base_url}/assets/logo.png'},
             {'property':"og:type" , 'content':"website"},
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ],
    )


app.title = 'raccoon.bike'
server = app.server

# This is to serve files from /static/ as if it's root
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/')


MAIN_COLOUR='#3286AD'
# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}



sidebar = html.Div(
    [
#         dcc.Link(href="/", children=html.H2("bikeraccoon", className="display-5", style={'font-family':'Courier New'})),
        html.H2(dcc.Link(href="/", children="raccoon.bike",style={"color": "black", "text-decoration": "none"}), className="display-5", style={'font-family':'Courier New'}),
        #html.Img(src='data:image/png;base64,{}'.format(encoded_logo.decode()), style={'width': '100%'}),
        #html.Img(src=app.get_asset_url('logo.png'), style={'width':'100%'}),
        html.Img(src='/logo.png', style={'width':'100%'}),
        html.Hr(),
        html.P(
            "Real-time monitoring of bike share systems", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink(f"{system['brand']} ({system['city']})", href=f"/live/{system['name']}", style={'color':BLUE}) for system in br.get_systems().to_dict('records')

            ],
            vertical=True,
            pills=True,
        ),
        
        html.Hr(),
        dcc.Link(href='/about/', children='About',style={"color": BLUE}), 
        
        
    ],
    
    
#    style=SIDEBAR_STYLE,
    id='sidebar'
)

content = dbc.Spinner(html.Div(id="page-content"), fullscreen=True)

footer = html.Div([
                html.Hr(),
                html.Span("© Mike Jarrett 2021", style={'float': 'right','margin':10})
                ])

app.layout = html.Div([dcc.Location(id="url"), sidebar, content, footer])

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ['/','/live/']:
        return make_live_home_page()

    if pathname in ['/about','/about/']:
        return html.Div(about_text)
    
    
    try:
        sys_name = pathname.strip('/').split('/')
        print(sys_name)
        print(sys_name[1])
        return system_page(sys_name[1])
    except Exception as e:
        print(e)
        pass

    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("No Data", className="text-danger"),
            html.Hr(),
            html.P(f"This system has no recent activity in the bikeraccoon database"),
        ]
    )


if __name__ == "__main__":
    app.run_server(port=8050, host='0.0.0.0', debug=True)
