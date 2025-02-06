import pandas as pd
import json
import urllib
import datetime as dt

def query_weather_day(api,freq,time):
    
    sdf = api.get_stations()
    lat = sdf['lat'].mean()
    lon = sdf['lon'].mean()
    
    
    timestr = time.strftime('%Y-%m-%dT01:00:00')

    weather_url = f'https://api.darksky.net/forecast/{api.DARKSKY_KEY}/{lat},{lon},{timestr}?units=si'
    with urllib.request.urlopen(weather_url) as url:    
        data = json.loads(url.read().decode())

    hdf = pd.DataFrame(data['hourly']['data']).set_index('time')
    hdf.index = [dt.datetime.utcfromtimestamp(x,) for x in hdf.index]
    hdf.index = hdf.index.tz_localize('UTC').tz_convert(api.info['tz'])

    ddf = pd.DataFrame(data['daily']['data']).set_index('time')
    ddf.index = [dt.datetime.utcfromtimestamp(x) for x in ddf.index]
    ddf.index = ddf.index.tz_localize('UTC').tz_convert(api.info['tz'])

    if freq == 'hourly':
        return hdf
    elif freq == 'daily':
        return ddf
    elif freq == 'both':
        return hdf,ddf
    else:
        raise ValueError("Unrecognized option for freq. Use hourly, daily or both")
                            
    return df


def get_weather_range(api,freq,day1,day2=None):
    """
    api: a bikeraccoon API instance
    freq: 'daily' or 'hourly'
    day1,day2: pandas.Timestamp object representing the start and end days (inclusive)
    
    Returns a pandas.DataFrame
    
    """

    
    if day2 is None:
        df = query_weather_day(api,freq,day1)
    else:
        
        if day2 < day1:
            day1,day2 = day2,day1
        
        days = list(pd.date_range(day1,day2,freq='d', ambiguous=True))
        df = pd.concat([query_weather_day(api,freq,x) for x in days])
    

    
    return df