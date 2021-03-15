import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import json
import datetime as dt

import bikeraccoon as br

import plotly.express as px
import plotly.graph_objects as go

from credentials import MAPBOX_TOKEN

margin=go.layout.Margin(
    l=5,
    r=5,
    b=5,
    t=5,
    pad=0)


def system_page(sys_name):

    api = br.LiveAPI(sys_name)

    sys_info = api.get_system_info()


    layout = dbc.Row([

        dbc.Col(width=12, children=[
            html.H1(f"{sys_info['brand']}"),
            html.H3(f"{sys_info['city']}, {sys_info['country']}"),
            html.Hr(),

            dbc.Row([
                dbc.Col(width=3, children=html.Span(json.dumps(sys_info, indent=4))),
                dbc.Col(width=9, children=[
                    make_daily_graph(api),
                    make_hourly_graph(api)
                ]),
            ]),
            dbc.Row([
                dbc.Col(width=12, children=[
                    make_station_map(api)
                ]),
            ]),
        ]),
    ])

    return layout


def make_daily_graph(api):

    t1 = dt.datetime.now()
    t2 = t1 - dt.timedelta(days=31)

    df = api.get_system_trips(t1,t2,freq='d').reset_index()
    fig  = px.bar(df.reset_index(), x='datetime', y='station trips')
    return dcc.Graph(
        id='daily-graph',
        figure=fig
    )

def make_hourly_graph(api):

    t1 = dt.datetime.now()
    t2 = t1 - dt.timedelta(days=7)

    df = api.get_system_trips(t1,t2,freq='h').reset_index()
    fig  = px.bar(df.reset_index(), x='datetime', y='station trips')
    return dcc.Graph(
        id='hourly-graph',
        figure=fig
    )


def make_station_map(api):

    sdf = api.get_stations()

    maplayout = go.Layout(mapbox_style="light",
                          mapbox=go.layout.Mapbox(
                            accesstoken=MAPBOX_TOKEN,
                            bearing=0,
                            center=go.layout.mapbox.Center(
                            lat=sdf.lat.mean(),
                            lon=sdf.lon.mean()
                            ),
                            zoom=11.5
                            ),
                          paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)',
                          margin=margin,
                          showlegend = False,
                         )



    mapdata = go.Scattermapbox(lat=sdf['lat'],
                               lon=sdf['lon'],
                               text=sdf['name'],
                               hoverinfo='text',
                                   marker={'color':'#0f0f0f',
                                            'size':6,
                                            'symbol':'bicycle'
                                #           'size':trips_df['trips'],
                                #           'sizemode':'area',
                                #           'sizeref':2.*max(trips_df['trips'])/(40.**2),
                                #           'sizemin':4
                                })

    fig = go.Figure(data=mapdata,layout=maplayout)
    return dcc.Graph(
        id='station-graph',
        figure=fig
    )
