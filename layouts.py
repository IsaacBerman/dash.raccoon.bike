import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import json
import datetime as dt
import pytz
import requests
import os

import bikeraccoon as br
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

MAPBOX_TOKEN = os.environ['MAPBOX_TOKEN']


BLUE='#3286AD'
PURPLE='#8357B2'
RED='#FF5B71'
GREEN='#77ACA2'



colors = [BLUE, PURPLE, GREEN, RED]

TEMPLATE='plotly_white'

margin=go.layout.Margin(
    l=5,
    r=5,
    b=5,
    t=5,
    pad=0)


def get_city_coords(city,country):
    r = requests.get(f"https://nominatim.openstreetmap.org/search?city={city}&country={country}&format=json")
    r = r.json()[0]
    lat = float(r['lat'])
    lon = float(r['lon'])
    
    return lat,lon


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




def make_live_home_page():
    
    def linkagg(x):
        if x.empty:
            return None
        return '<br>----<br>'.join(x)
    
    cdf = br.get_systems()
    cdf['coords'] = cdf.apply(lambda x: get_city_coords(x['city'],x['country']), axis=1)
    cdf['link'] = cdf.apply(lambda x: f"<a target='_self' style='color:white;' href='/live/{x['name']}'>{x['brand']}</a>",axis=1)
    
    cdf = cdf.groupby('city').agg({'link':linkagg, 'coords':'first'})
    
                                              

#     sdf = pd.concat([br.LiveAPI(sys_name).get_stations() for sys_name in br.get_systems()['name']])
    
    maplayout = go.Layout(mapbox_style="light",
                      mapbox=go.layout.Mapbox(
                        accesstoken=MAPBOX_TOKEN,
                        bearing=0,
                        center=go.layout.mapbox.Center(
                        lat=49,
                        lon=-100,
                        ),
                        zoom=3
                        ),
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)',
                      margin=margin,
                      showlegend = False,
                     )


    mapdata = go.Scattermapbox(lat=cdf['coords'].apply(lambda x: x[0]),
                               lon=cdf['coords'].apply(lambda x: x[1]),
#                                lat=sdf['lat'],
#                                lon=sdf['lon'],
                               text=cdf['link'],
                               hoverinfo='text',
                              
                               marker={'color':BLUE,
                                        'size':20,
                            #           'symbol':'bicycle'
                            #           'size':trips_df['trips'],
                            #           'sizemode':'area',
                            #           'sizeref':2.*max(trips_df['trips'])/(40.**2),
                            #           'sizemin':4
                                })

                              
    fig = go.Figure(data=mapdata,layout=maplayout)

    
    jumbo = dbc.Jumbotron(fluid=False, children=
        [
            html.H1("Live Bikeshare Tracking"),
            html.Hr(),
            html.P(f"Select a bikeshare system to view live trip activity"),
            dbc.Col(width=12, children=[
                dcc.Graph(
                    id='cities-graph',
                    figure=fig
                    )
            ])
        ]
    )
    
    
    
    return html.Div([sidebar,jumbo])
    
    
def make_tabs(api):
    sdf = api.get_system_trips(t1=api.now-dt.timedelta(hours=24),t2=api.now,freq='d')

    bdf = api.get_free_bike_trips(t1=api.now-dt.timedelta(hours=24),t2=api.now,freq='d')


    st_tab_disabled = True if sdf is None else False
    fb_tab_disabled = True if bdf is None else False
    
    st_tab_text = "No station data available" if st_tab_disabled else ""
    fb_tab_text = "No free bike data available" if fb_tab_disabled else ""
    
    active_tab = 'st-tab' if not st_tab_disabled else 'fb-tab'
    

    
    
    station_tab = dbc.Tab(label='Stations', tab_id='st-tab', disabled=st_tab_disabled ,children=[

            dbc.Row([
                #dbc.Col(width=3, children=html.Span(json.dumps(sys_info, indent=4))),


                dbc.Col(width=12, md=8, children=[
                    dbc.Row([
                        dbc.Col(width=12, children=[
                            make_hourly_graph(api)
                            ]),
                        dbc.Col(width=12, children=[
                            make_daily_graph(api)
                            ]),
                    ]),
                ]),


                dbc.Col(width=12, md=4, children=[
                    #html.H3("Most active stations"),
                    make_top_stations(api)
                ])
            ])
        ] if not st_tab_disabled else [])

    free_bike_tab = dbc.Tab(label="Free bikes", tab_id="fb-tab", disabled=fb_tab_disabled, children=[
        dbc.Row([
                #dbc.Col(width=3, children=html.Span(json.dumps(sys_info, indent=4))),


                dbc.Col(width=8, children=[
                    dbc.Row([
                        dbc.Col(width=12, children=[
                            make_hourly_graph(api,kind='free_bikes')
                            ]),
                        dbc.Col(width=12, children=[
                            make_daily_graph(api,kind='free_bikes')
                            ]),
                    ]),
                ]),

            ])
            
        ] if not fb_tab_disabled else []  )

    tabs = dbc.Tabs(active_tab=active_tab, children=
        [
            station_tab,
            free_bike_tab
        ]
    )
    
    # Tooltips aren't working properly with DBC tabs for some reason.
#     tooltips = [
#         dbc.Tooltip(st_tab_text, target="st-tab"),
#         dbc.Tooltip(fb_tab_text, target="fb-tab")
#     ]
    tooltips = []
    
    
    return [tabs] + tooltips
    
    
def system_page(sys_name):

    """
    Make base system page. Elements will be generated with callbacks
    """
    
    api = br.LiveAPI(sys_name, echo=True)

    sys_info = api.info

    layout = dbc.Row([
        dbc.Col([
            html.H1(f"{sys_info['brand']}", style={'color':BLUE}),
            html.H3(f"{sys_info['city']}, {sys_info['country']}", style={'color':'#696969'}),
            html.Hr(),
            ], width=12),


        dbc.Col(width=12, id='top_row'),
        dbc.Col(width=12, id='map_fig'),
        dbc.Spinner(dbc.Col(width=12, id='tabs'))  #This is slowest so only tabs needs the spinner

    ])

    return html.Div([sidebar,layout])


def make_top_row(api):
    
    bikes = api.get_station_trips(dt.datetime.now().replace(hour=4),freq='h')['num_bikes_available'].sum()
    
    try:
        bikes = bikes + api.get_free_bike_trips(dt.datetime.now().replace(hour=4), freq='h')['num_bikes_available'].sum()
    except TypeError:
        pass
    
    card_content_bikes = [
    #dbc.CardHeader("Card header"),
    dbc.CardBody(
        [
            html.H5("Total bikes", className="card-title"),
            html.H3(
                f"{bikes:,}",
                className="card-text display-3",
            ),
        ]
    ),
]
    
    sdf = api.get_stations()
    stations = len(sdf[sdf['active']])
    card_content_stations = [
    #dbc.CardHeader("Active Stations"),
    dbc.CardBody(
        [
            html.H5("Active Stations", className="card-title"),
            html.H3(
                f"{stations:,}",
                className="card-text display-3",
            ),
        ]
    ),
]
        
    # This combines station and free bike trips
    trips = api.get_system_trips(dt.datetime.now(),freq='y').sum(1)[0]  
    card_content_trips = [
    #dbc.CardHeader("Card header"),
    dbc.CardBody(
        [
            html.H5("Trips this year", className="card-title"),
            html.H3(
                f"{trips:,}",
                className="card-text display-3",
            ),
        ]
    ),
]
    
    
    cards = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(dbc.Card(card_content_bikes, color=RED, inverse=True)),
                dbc.Col(
                    dbc.Card(card_content_stations, color=GREEN, inverse=True)
                ),
                dbc.Col(dbc.Card(card_content_trips, color=PURPLE, inverse=True)),
            ],
            className="mb-4",
        ),

    ]
)
    return cards


def make_daily_graph(api,kind='station'):

    t1 = api.now.replace(minute=0, second=0, microsecond=0)
    t2 = t1 - dt.timedelta(days=31)


    
    df = api.get_system_trips(t1,t2,freq='d').reset_index()

    if kind=='station': 
        y='station trips'
    elif kind=='free_bikes':
        y='free bike trips'
    fig  = px.bar(df.reset_index(), x='datetime', y=y, height=300, template=TEMPLATE)
    fig.update_layout(
        title="Daily Trips",
        xaxis_title="",
        yaxis_title="trips",
    )
    
    fig.update_traces(customdata=[x.strftime('%a %B %-d %Y') for x in df['datetime']],hovertemplate='%{y} trips<br>' + 
                                   '<b>%{customdata}</b><extra></extra>')
    fig.update_traces(marker_color=RED, marker_line_color=RED,
                  marker_line_width=1.5, opacity=1, width=1000 * 3600 * 20 )
    
    return dcc.Graph(
        id='daily-graph',
        figure=fig
    )

def make_hourly_graph(api,kind='station'):

    t1 = api.now.replace(minute=0, second=0, microsecond=0)
    t2 = t1 - dt.timedelta(days=7)
    df = api.get_system_trips(t1,t2,freq='h').reset_index()
    if kind=='station':
        y='station trips'
    elif kind=='free_bikes':
        y='free bike trips'
    fig  = px.bar(df.reset_index(), x='datetime', y=y,
                  height=300,template=TEMPLATE)
    fig.update_layout(
        title="Hourly Trips",
        xaxis_title="",
        yaxis_title="trips",
    )

    fig.update_traces(customdata=[x.strftime('%a %B %-d %Y %X') for x in df['datetime']],hovertemplate='%{y} trips<br>' + 
                                    '<b>%{customdata}</b><extra></extra>')
    fig.update_traces(marker_color=PURPLE, marker_line_color=PURPLE,
                  marker_line_width=1.5, opacity=1)
    return dcc.Graph(
        id='hourly-graph',
        figure=fig
    )


    


def make_station_map(api):

    sdf = api.get_stations()
    bdf = api.query_free_bikes()
    
    tdf = api.get_station_trips(t1=api.now,freq='d',station='all')

    sdf = pd.merge(sdf,tdf,on='station_id')
        
    # Get city location from OSM API
    city = api.info['city']
    country = api.info['country']
    r = requests.get(f"https://nominatim.openstreetmap.org/search?city={city}&country={country}&format=json")
    r = r.json()[0]
    lat = float(r['lat'])
    lon = float(r['lon'])
    maplayout = go.Layout(mapbox_style="light",
                          mapbox=go.layout.Mapbox(
                            accesstoken=MAPBOX_TOKEN,
                            bearing=0,
                            center=go.layout.mapbox.Center(
                            lat=lat,
                            lon=lon
                            ),
                            zoom=11.5
                            ),
                          paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)',
                          margin=margin,
                          showlegend = False,
                         )


    mapdata = [go.Scattermapbox()]
    

    
    if sdf is not None:

        
        stationdata = go.Scattermapbox(lat=sdf['lat'],
                                   lon=sdf['lon'],
                                   text=sdf['name'],
                                   customdata=sdf['trips'],
                                   hoverinfo='text',
                                   hovertemplate =
                                    '<i>Trips today</i>: %{customdata}<br>' + 
                                    '<b>%{text}</b><extra></extra>',
                                   #name='Trips Today',
                                   marker={'color':GREEN,
                                          'sizemin':1,
                                          'size':[1 if x==0 else x for x in sdf['trips']],
                                          'sizemode':'area',
                                          'sizeref':2.*max(sdf['trips'])/(40.**2),
                                          
                                          
                                    })
        mapdata.append(stationdata)
        

        
        

    if bdf is not None:
        bikedata = go.Scattermapbox(lat=bdf['lat'],
                                   lon=bdf['lon'],
                                   text=bdf['bike_id'],
                                   hoverinfo='text',
                                   name='Free Bikes',
                                   marker={'color':GREEN,
                                            'size':6,
                                            'symbol':'bicycle'
                                            })
        mapdata.append(bikedata)
        
        
    
    fig = go.Figure(data=mapdata,layout=maplayout)
    


    return dcc.Graph(
        id='station-graph',
        figure=fig
    )



def make_top_stations(api):

    print("Start make top station", dt.datetime.now())

    n_stations = 10
    
    t1 = api.now.replace(minute=0, second=0, microsecond=0)
    t2 = t1 - dt.timedelta(hours=24)
    
    
    thdf = api.get_station_trips(t1,t2,freq='h',station='all')


    top_stations = list(thdf.groupby('station').sum().sort_values('trips',ascending=False).index[:n_stations])


    thdf = thdf[thdf['station'].isin(top_stations)].pivot(values='trips',columns='station')

    fig = px.line(thdf[top_stations],facet_row="station",facet_row_spacing=0.05,color_discrete_sequence=colors)

    # hide and lock down axes
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False)#, fixedrange=True)


    fig.for_each_annotation(lambda a: a.update(textangle=0,x=0.05,y=a.y+0.05,
                                                text=a.text.split("=")[-1],
                                                ))
    # strip down the rest of the plot
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        margin=dict(t=40,l=10,b=10,r=10),
        title="Most active stations (last 24 hours)"
    )
    

    fig.update_traces(customdata=[x.strftime('%a %B %-d %Y %X') for x in thdf.index],hovertemplate='%{y} trips<br>' + 
                                    '<b>%{customdata}</b><extra></extra>')
    print("End make top station", dt.datetime.now())

    return dcc.Graph(
        id='stations-graph',
        figure=fig,
        config={
        'displayModeBar': False
        }
        )



about_text = dcc.Markdown('''
# About this website

`dash.raccoon.bike` is a website that shares live stats for Canadian public bikeshare systems. Data is updated every ~20 minutes.

Data is generated by tracking the [GBFS](https://github.com/NABSA/gbfs) feeds of available bikeshare systems. [The tracking software](https://github.com/mjarrett/bikeraccoonAPI) records a trip occuring when a bike is removed from a station or a free floating bike becomes unavailable. For more information about how this works and how well the tracking matches the actual usage statistics, see [this blog post](https://notes.mikejarrett.ca/tracking-bikeshare-use-using-gbfs-feeds/). 

I've also written a [Python package](https://github.com/mjarrett/bikeraccoon) called `bikeraccoon` that wraps the tracking API so you can query the tracker with a single line of Python. This website is built on the tracker->API->`bikeraccoon` stack.

If a system isn't showing live data, it's probably because the feed from the bikeshare provider is down. When the feed returns, the page for that system should start working again.

This website was created by Mike Jarrett. Please feel free to contact me at [@mikejarrett_](https://twitter.com/mikejarrett_) on Twitter or by email at mike/@/mikejarrett.ca. Questions, requests, and contributions to this project are welcome.

To receive daily bikeshare updates in your twitter feed, please follow:
* [@vanbikesharebot](https://twitter.com/vanbikesharebot)
* [@tobikesharebot](https://twitter.com/tobikesharebot)
* [@mtlbikesharebot](https://twitter.com/mtlbikesharebot)
''')

