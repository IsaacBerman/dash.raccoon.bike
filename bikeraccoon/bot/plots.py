import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd

from bikeraccoon.bot.weather import *



c_blue =     '#3286AD' 
c_light_blue='#50AAD3'
c_indigo =   '#8357B2'
c_red =      '#FF5B71'
c_yellow =   '#E5DE50' 
c_green =    '#77ACA2'




def plot_hourly_trips(api,kind,t1,t2,ax=None, palette=None):
    sns.set(style='ticks', palette=palette)  
    color = sns.color_palette()[0]

    if ax is None:
        f,ax = plt.subplots()
        
    trips = api.get_system_trips(t1,t2)
    
    if kind == 'stations':
        trips = trips['station trips']
    elif kind == 'floating':
        trips = trips['free bike trips']
    elif kind == 'hybrid':
        trips = trips['station trips'] + trips['free bike trips'] 


    
    line = ax.plot(trips.index,trips.values,color=color)

    ax.fill_between(trips.index,0,trips.values,alpha=0.4,color=color)
    
    ax.xaxis.set_major_locator(mdates.DayLocator(tz=trips.index.tz))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%A",tz=trips.index.tz))
    #ax.xaxis.get_ticklabels()[-1].set_visible(False)
    ax.tick_params(axis='x',labelrotation=45)

    try:
        ax.xaxis.get_ticklabels()[-1].set_visible(False)
    except:
        pass
    ax.set_ylabel('Hourly trips')
    sns.despine(top=True,bottom=True,left=True,right=True)
    ax.tick_params(axis=u'both', which=u'both',length=0)
    ax.grid(which='both')
    return ax

def plot_daily_trips(api,kind,t1,t2,ax=None, palette=None):
    
    sns.set(style='ticks', palette=palette)  
    color = sns.color_palette()[0]
    

    trips = api.get_system_trips(t1,t2, freq='d')
    
    
    if ax is None:
        f,ax = plt.subplots()

        
    if kind == 'stations':
        trips = trips['station trips']
    elif kind == 'floating':
        trips = trips['free bike trips']
    elif kind == 'hybrid':
        trips = trips['station trips'] + trips['free bike trips'] 
        
    trips.index = [x - pd.Timedelta(6,'h') for x in trips.index]

    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.tick_params(axis='x',labelrotation=45)
    
    ax.bar(trips.index,trips.values,color=color)

    ax.set_ylabel('Daily trips')
    sns.despine(top=True,bottom=True,left=True,right=True)
    ax.tick_params(axis=u'both', which=u'both',length=0)
    ax.grid(which='both')
    return ax


def plot_alltime_trips(api,t1,t2,kind,ax=None, palette=None):
    sns.set(style='ticks', palette=palette)  
    color = sns.color_palette()[0]
    color = sns.color_palette()[0]

    if ax is None:
        f,ax = plt.subplots()


    trips = api.get_system_trips(t1,t2, freq='d')    
        
        
    if kind == 'stations':
        trips = trips['station trips']
    elif kind == 'floating':
        trips = trips['free bike trips']
    elif kind == 'hybrid':
        trips = trips['station trips'] + trips['free bike trips'] 



    ax.xaxis.set_major_locator(mdates.YearLocator(1,1,2,tz=trips.index.tz))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y",tz=trips.index.tz))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(tz=trips.index.tz))

    ax.tick_params(axis='x',labelrotation=45)
    ax.plot(trips.index,trips.values)
    ax.set_ylabel('Daily trips')
    sns.despine()
    ax.grid(which='both')
    return ax




 


def plot_daily_weather(api,date1,date2,ax=None):
    try:
        df = get_weather_range(api,'daily',date1,date2)
    except Exception as e:
        print(f"get_weather_range(api,'daily',{date1},{date2}) failed with the following exception")
        print(e)
        return None
    
    if ax is None:
        f,ax = plt.subplots()
        
    ax2 = ax.twinx()

    ax.set_ylabel('Daily high')
    ax2.bar(df.index,df['precipIntensity'].values*24,color=c_light_blue)
#     ax2.bar(df.index,df['precipIntensity'].values,color='#3778bf',zorder=1001,width=1/24)

    ax.plot(df.index,df['temperatureHigh'],color=c_yellow,zorder=1000)
    ax2.set_ylabel('Precipitation')
    ax.yaxis.label.set_color(c_yellow)
    ax2.yaxis.label.set_color(c_light_blue)
    ax.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.tick_params(axis='x',labelrotation=45)
    ax2.tick_params(axis='x',labelrotation=45)
    
    sns.despine(ax=ax,top=True,bottom=True,left=True,right=True)
    sns.despine(ax=ax2,top=True,bottom=True,left=True,right=True)
    ax.tick_params(axis='both', which='both',length=0)
    ax2.tick_params(axis='both', which='both',length=0)
    ax.grid(which='both')   
    
    ax.set_yticklabels([])
    ax2.set_yticklabels([])
    

    #ax.text(0,-1.4,'Powered by Dark Sky: https://darksky.net/poweredby/',transform=ax.transAxes,fontdict={'color':'grey','style':'italic','family':'serif','size':8})
    
    
    return ax,ax2


def plot_hourly_weather(api,date1,date2,ax=None):
    try:
        df = get_weather_range(api,'hourly',date1,date2)
    except:
        return None
    
    if ax is None:
        f,ax = plt.subplots()
        
    ax2 = ax.twinx()

    ax.set_ylabel('Temperature')
#     ax2.bar(df.index,df['precipIntensity'].values,color='#3778bf',zorder=1001,width=1/24)
    ax2.plot(df.index,df['precipIntensity'].values,color=c_light_blue,zorder=1001)
    ax2.fill_between(df.index,0,df['precipIntensity'].values,alpha=0.8,color=c_light_blue)
    ax.plot(df.index,df['temperature'],color=c_yellow,zorder=1000)
    ax2.set_ylabel('Precipitation')
    ax.yaxis.label.set_color(c_yellow)
    ax2.yaxis.label.set_color(c_light_blue)
    ax.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax.xaxis.set_major_locator(mdates.DayLocator(tz=df.index.tz))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%A",tz=df.index.tz))
    ax.tick_params(axis='x',labelrotation=45)
    ax2.tick_params(axis='x',labelrotation=45)
    
    if df['precipIntensity'].max()>2.5:
        ymax = df['precipIntensity'].max()
    else:
        ymax = 2.5
    ax2.set_ylim(0,ymax)
    
    #ax.text(0,-2.6,'Powered by Dark Sky: https://darksky.net/poweredby/',transform=ax.transAxes,fontdict={'color':'grey','style':'italic','family':'serif','size':8})
    sns.despine(ax=ax,top=True,bottom=True,left=True,right=True)
    sns.despine(ax=ax2,top=True,bottom=True,left=True,right=True)
    ax.tick_params(axis='both', which='both',length=0)
    ax2.tick_params(axis='both', which='both',length=0)
    ax.grid(which='both')   
    
    ax.set_yticklabels([])
    ax2.set_yticklabels([])
    return ax,ax2


from shapely.geometry import Point
import geopandas
from cartopy.io.img_tiles import MapboxStyleTiles,MapboxTiles, GoogleTiles
import cartopy.crs as ccrs


def plot_stations(api,date1,date2=None,extent=None, palette=None):
    
    """
    Plot stations on a map. Station size proportional to usage in date range
    bs: bikedata.BikeShareSystem instance
    date1,date2: date range (date string)
    extent: [lon_min,lon_max,lat_min,lat_max] in lat/lon
    """
    if date2 is None:
        date2 = date1
    
    
    sns.set(style='ticks', palette=palette)  
    color = sns.color_palette()[0]
    color=sns.color_palette()[0]
    color2=sns.color_palette()[1]
    
    tile = MapboxStyleTiles(api.MAPBOX_TOKEN,'mikejarr','ckgebsspl1i8s19qukcae7yg5')

    
    sdf = api.get_stations()
    sdf['geometry'] = [Point(xy) for xy in zip(sdf.lon, sdf.lat)]

    thdf = api.get_station_trips(date1,date2,freq='d')
    
    f,ax = plt.subplots(subplot_kw={'projection': tile.crs},figsize=(7,7))

    if extent is None:
        extent = [sdf.lon.min(),sdf.lon.max(),sdf.lat.min(),sdf.lat.max()]
    ax.set_extent(extent)

    ax.add_image(tile,13)
    
    ax.outline_patch.set_visible(False)
    ax.background_patch.set_visible(False)
    
    
    
    sdf = pd.merge(sdf,thdf,how='inner',on='station_id')
    sdf = geopandas.GeoDataFrame(sdf)
    sdf.crs = {'init' :'epsg:4326'}
    sdf = sdf.to_crs({'init': 'epsg:3857'})
    sdf.plot(ax=ax,markersize='trips',color=color,alpha=0.7)
    sdf[sdf.trips==0].plot(ax=ax,color=color2,alpha=0.7,markersize=10,marker='x')
    
    
    
    l1 = ax.scatter([0],[0], s=10, edgecolors='none',color=color,alpha=0.7)
    l2 = ax.scatter([0],[0], s=100, edgecolors='none',color=color,alpha=0.7)
    l3 = ax.scatter([0],[0], s=10, marker='x',edgecolors='none',color=color2,alpha=0.7)

    labels=['0','10','100']
    ax.legend([l3,l1,l2],labels,title=f'Station Activity')
    
    return f,ax