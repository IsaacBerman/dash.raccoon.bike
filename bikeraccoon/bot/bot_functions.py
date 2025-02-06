import datetime as dt
import bikeraccoon as br
import bikeraccoon.bot.plots as plots
import matplotlib.pyplot as plt
import pandas as pd
import os
from glob import glob

# Get dates and date strings
today = dt.datetime.now().replace(hour=23)
yday = today - dt.timedelta(1)
yday_min30 = (today - dt.timedelta(32)).replace(hour=0)
yday_min7 = (today - dt.timedelta(8)).replace(hour=0)


def check_zero_trips(api,m=0):
    # Get yesterday's data
    t1 = yday.replace(hour=0)
    t2 = yday.replace(hour=23)
    sdf = api.get_stations()
    thdf = api.get_station_trips(t1,t2,freq='d')
    sdf = pd.merge(sdf,thdf,how='inner',on='station_id')

    ntrips = sdf['trips'].sum()

    if ntrips <= m:
        return True
    else:
        return False

def make_tweet_text(api,path='./', lang='EN'):
    
   
    # Get yesterday's data
    t1 = yday.replace(hour=0)
    t2 = yday.replace(hour=23)
    sdf = api.get_stations()
    thdf = api.get_station_trips(t1,t2,freq='d')
    sdf = pd.merge(sdf,thdf,how='inner',on='station_id')

    ntrips = sdf['trips'].sum()

    sdf = api.get_stations()
    sdf = sdf[sdf['active']]
    thdf = api.get_station_trips(t1,t2,freq='d')
    sdf = pd.merge(sdf,thdf,how='inner',on='station_id')

    sdf = sdf.sort_values('trips', ascending=False)

    busiest_station = sdf['name'].iloc[0]
    busiest_station = busiest_station.split('(')[0].strip() # trip parentheticals to shorten name
    busiest_station_trips = int(sdf['trips'].iloc[0])
    n_busiest_stations = len(sdf[sdf['trips']==busiest_station_trips])

    plural = "" if n_busiest_stations == 2 else "s"

    if n_busiest_stations > 1:
        n_busiest_str = f" and {n_busiest_stations-1} other{plural}"
    else:
        n_busiest_str = ""

    least_busy_station = sdf['name'].iloc[-1]
    least_busy_station = least_busy_station.split('(')[0].strip() # trip parentheticals to shorten name
    least_busy_station_trips = sdf['trips'].iloc[-1]

    n_least_busy_stations = len(sdf[sdf['trips']==least_busy_station_trips])
    plural = "" if n_least_busy_stations == 2 else "s"
    if n_least_busy_stations > 1:
        if lang=='EN':
            n_least_busy_str = f" and {n_least_busy_stations-1} other{plural}"  
        elif lang=='FR':
            n_least_busy_str = f" et {n_least_busy_stations-1} autre{plural}"
    else:
        n_least_busy_str = ""

    active_stations = len(sdf)

    if lang=='EN':
        s = f"""Yesterday there were approximately {ntrips:,} {api.brand} bikeshare trips
Most used station: {busiest_station}{n_busiest_str} ({busiest_station_trips} trips)
Least used station: {least_busy_station}{n_least_busy_str} ({least_busy_station_trips} trips)
Active stations: {active_stations}
{api.hashtag}"""
        
    elif lang=='FR':
        s=f"""Hier, il y a eu approximativement {ntrips:,} déplacements en vélopartage {api.brand}.
Station la plus utilisée: {busiest_station}{n_busiest_str} ({busiest_station_trips} déplacements)
Station la moins utilisée: {least_busy_station}{n_least_busy_str} ({least_busy_station_trips} déplacements)
Stations actives: {active_stations}"""

    print(s)
    with open(f'{path}/{api.sys_name}_bot_text.txt','w') as ofile:
        ofile.write(s)
    
    
    
# Last month daily 
def make_monthly_trips_plot(api,path='./'):
    t1 = yday
    t2 = yday_min30

    f,ax = plt.subplots(2,sharex=True,gridspec_kw={'height_ratios':[4.5,1]})
    plots.plot_daily_trips(api,api.sys_type,t1,t2,ax=ax[0],palette=api.palette)
    plots.plot_daily_weather(api,t1,t2,ax[1])
    f.tight_layout()
    f.savefig(f"{path}/2.{api.sys_name}_last_month.png")


# Last week
def make_weekly_trips_plot(api,path='./'):
    t1 = yday
    t2 = yday_min7

    f,ax = plt.subplots(2,sharex=True,gridspec_kw={'height_ratios':[4.5,1]})
    plots.plot_hourly_trips(api,api.sys_type,t1,t2,ax=ax[0],palette=api.palette)
    plots.plot_hourly_weather(api,t1,t2,ax[1])
    f.tight_layout()
    f.savefig(f"{path}/1.{api.sys_name}_last_week.png")

# All time
def make_alltime_plot(api,path='./'):
    t1 = dt.datetime(2018,1,1,0)
    t2 = yday

    f,ax = plt.subplots()
    plots.plot_alltime_trips(api,t1,t2,api.sys_type,ax=ax, palette=api.palette)
    f.tight_layout()
    f.savefig(f"{path}/3.{api.sys_name}_alltime.png")
           
# Stations
def make_stations_map(api,path='./'):
    t1 = yday.replace(hour=0)
    t2 = yday.replace(hour=23)
    f,ax = plots.plot_stations(api,t1,t2,extent=api.extent, palette=api.palette)
    f.savefig(f'{path}/4.{api.sys_name}_stations.png',
                  bbox_inches='tight',pad_inches=0.0,transparent=False,dpi=300)
