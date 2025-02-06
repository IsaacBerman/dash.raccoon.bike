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
import sys
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
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




content = html.Div(id="page-content")

app.layout = html.Div([dcc.Location(id="url"), content])

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ['/','/live/']:
        return make_live_home_page()

    if pathname in ['/about','/about/']:
        return html.Div(about_text)
    
    
    try:
        sys_name = pathname.strip('/').split('/')[1]
        return system_page(sys_name)
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


@app.callback(Output("top_row", "children"), [Input("page-content", "children")],  [State("url", "pathname")])
def render_top_row(content,pathname):
    sys_name = pathname.strip('/').split('/')[1]
    
    api = br.LiveAPI(sys_name, echo=True)

    sys_info = api.info
    
    api.now = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    api.now = pytz.timezone('UTC').localize(api.now).astimezone(pytz.timezone(sys_info['tz']))
    
    top_row = make_top_row(api)

    return top_row
   
    
    
@app.callback(Output("tabs", "children"), [Input("page-content", "children")],  [State("url", "pathname")])
def render_tabs(content,pathname):
    sys_name = pathname.strip('/').split('/')[1]
    
    api = br.LiveAPI(sys_name, echo=True)

    sys_info = api.info
    
    api.now = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    api.now = pytz.timezone('UTC').localize(api.now).astimezone(pytz.timezone(sys_info['tz']))
    
    tabs = make_tabs(api)

    return tabs    

if __name__ == "__main__":
    ip = sys.argv[1]
    app.run_server(port=8000, host=ip, debug=False)
