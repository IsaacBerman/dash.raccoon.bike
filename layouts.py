import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import json
import datetime as dt
import pytz
import requests

import bikeraccoon as br
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from credentials import MAPBOX_TOKEN

BLUE='#3286AD'
PURPLE='#190933'
NAVY='#001B2E'
PEACH='#FF715B'
GREEN='#7CA982'
ORANGE='#F49D37'
RED='#6F1A07'

colors = [BLUE, PURPLE, NAVY, PEACH, GREEN, ORANGE, RED]

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

def make_live_home_page():
    
    def linkagg(x):
        if x.empty:
            return None
        return '<br>'.join(x)
    
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
    
    
    
    return jumbo
    

def system_page(sys_name):

    api = br.LiveAPI(sys_name, echo=True)

    sys_info = api.info
    
    api.now = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    api.now = pytz.timezone('UTC').localize(api.now).astimezone(pytz.timezone(sys_info['tz']))
    sdf = api.get_system_trips(t1=api.now-dt.timedelta(hours=24),t2=api.now,freq='d')

    bdf = api.get_free_bike_trips(t1=api.now-dt.timedelta(hours=24),t2=api.now,freq='d')


    st_tab_disabled = True if sdf is None else False
    fb_tab_disabled = True if bdf is None else False
    
    st_tab_text = "No station data available" if st_tab_disabled else ""
    fb_tab_text = "No free bike data available" if fb_tab_disabled else ""
    
    active_tab = 'st-tab' if not st_tab_disabled else 'fb-tab'
    
    map_fig = make_station_map(api)

    
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



    layout = dbc.Row([
        dbc.Col([
            html.H1(f"{sys_info['brand']}", style={'color':BLUE}),
            html.H3(f"{sys_info['city']}, {sys_info['country']}", style={'color':'#696969'}),
            html.Hr(),
            ], width=12),

        dbc.Col(map_fig, width=12),
        dbc.Col([tabs] + tooltips, width=12)


    ])

    return layout



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
    
    fig.update_traces(customdata=[x.strftime('%a %B %-d %Y %X') for x in df['datetime']],hovertemplate='%{y} trips<br>' + 
                                   '<b>%{customdata}</b><extra></extra>')
    fig.update_traces(marker_color=PURPLE, marker_line_color=PURPLE,
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
    fig.update_traces(marker_color=PEACH, marker_line_color=PEACH,
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
                                          'size':[0.1 if x==0 else x for x in sdf['trips']],
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

    # remove facet/subplot labels
    # annotations = []
    #
    # for i in range(5):
    #     annotations.append(dict(xref='paper', x=0.1, y=i*2000 ,
    #                                   xanchor='right', yanchor='middle',
    #                                   text='Test 99%',
    #                                   font=dict(family='Arial',
    #                                             size=16),
    #                                   showarrow=False))
    # fig.update_layout(annotations=annotations, overwrite=True)
    #fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
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
    
    #fig.update_traces(customdata=df.index.strftime('%a %B %-d %Y %X'),hovertemplate='%{y} trips<br>' + 
    #                                '<b>%{customdata}</b><extra></extra>')
    
    print("End make top station", dt.datetime.now())

    return dcc.Graph(
        id='stations-graph',
        figure=fig
        )
