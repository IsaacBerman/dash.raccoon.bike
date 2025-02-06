import pandas as pd
import datetime as dt
import requests
import calendar
import sys


from functools import cached_property, lru_cache

class APIBase():

    def __init__(self):
        self.api_base_url = 'http://api.raccoon.bike'



class LiveAPI(APIBase):
    def __init__(self,system, echo=False):
        super().__init__()
        self.system = system
        self.info = self.get_system_info()
        self.echo = echo
        


        

    def get_system_info(self):
        systems = get_systems()
        return systems[systems['name']==self.system].to_dict('records')[0]

    @lru_cache
    def get_system_trips(self,t1,t2=None,freq='h'):
        t1,t2 = _dates2strings(t1,t2,freq)

        query_url = f'/activity?system={self.system}&start={t1}&end={t2}&frequency={freq}'
        if self.echo:
            print(self.api_base_url + query_url)
        df =  self._to_df(self.api_base_url + query_url)

        # Add any missing dates - we want to return a continuous datetime range
        # There's a bug when I do this with 'm' and 'y' freq. not sure why, need to investigate.
        if freq in ['h','d']:
            #df = df.asfreq(freq)
            df = df.fillna(0)
        return df
        
    
    @lru_cache
    def get_station_trips(self,t1,t2=None,freq='h',station='all',format='long',limit=None):
        t1,t2 = _dates2strings(t1,t2,freq)

        query_url = f'/activity?system={self.system}&start={t1}&end={t2}&frequency={freq}&station={station}&limit={limit}'
        if self.echo:
            print(self.api_base_url + query_url)
        df =  self._to_df(self.api_base_url + query_url)
        if len(df) == 0:
            return None
        return df
    
    @lru_cache
    def get_free_bike_trips(self,t1,t2=None,freq='h'):
        t1,t2 = _dates2strings(t1,t2,freq)

        query_url = f'/activity?system={self.system}&start={t1}&end={t2}&frequency={freq}&station=free_bikes'
        if self.echo:
            print(self.api_base_url + query_url)
        df =  self._to_df(self.api_base_url + query_url)
        if len(df) == 0:
            return None
        return df

    @lru_cache
    def get_stations(self):
        query_url = f"/stations?system={self.system}"
        if self.echo:
            print(self.api_base_url + query_url)
        r = requests.get(APIBase().api_base_url + query_url)
        df =  pd.DataFrame(r.json())

        if len(df) == 0:
            return None
        return df

    
    def query_free_bikes(self):

        """
        Query free_bikes.json
        """

        sys_url = self.get_system_info()['url']
        try:
            url = _get_free_bike_url(sys_url)
        except IndexError:
            return None

        r = requests.get(url)
        data = r.json()

        
        try:
            df = pd.DataFrame(data['data']['bikes'])
        except KeyError:
            df = pd.DataFrame(data['bikes'])
        try:
            df['bike_id'] = df['bike_id'].astype(str)
        except KeyError:
            return None

        try:
            df['datetime'] = data['last_updated']
            df['datetime'] = df['datetime'].map(lambda x: dt.datetime.utcfromtimestamp(x))
        except KeyError:
            df['datetime'] = dt.datetime.utcnow()
        
        df['datetime'] = df['datetime'].dt.tz_localize('UTC')


        df = df[['bike_id','lat','lon','datetime']]

        return df

    def _to_df(self,url):

        r = requests.get(url)
        df =  pd.DataFrame(r.json())
        if len(df) == 0:
            df = pd.DataFrame(columns=['num_bikes_available','num_docks_available','returns','station','station_id','trips'],
                               )
            df.index.name = 'datetime'
            return df

        # Need to import as UTC then re-set TZ because of some DST issues.
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert(self.info['tz'])
        
        df = df.set_index('datetime')
        
        

        return df
    
    
    
    
def get_systems():
    query_url = f'/systems'
    r = requests.get(APIBase().api_base_url + query_url)
    df =  pd.DataFrame(r.json())
#     print(self.api_base_url + query_url)
    return df


def _dates2strings(t1,t2,freq='h'):
    if t2 is None:
        if freq=='h':
            t2 = t1
        elif freq=='d':
            t1 = t1.replace(hour=0)
            t2 = t1.replace(hour=23)
        elif freq=='m':
            t1 = t1.replace(hour=0,day=1)
            last_day = calendar.monthrange(t1.year, t1.month)[1]
            t2 = t1.replace(hour=23,day=last_day)
        elif freq=='y':
            t1 = t1.replace(hour=0,day=1,month=1)
            t2 = t1.replace(hour=23,day=31,month=12)

    if t2 < t1:
        t1,t2 = t2,t1

    t1 = t1.strftime('%Y%m%d%H')
    t2 = t2.strftime('%Y%m%d%H')

    return t1,t2


    
    
    
    



def _get_free_bike_url(sys_url):
    r = requests.get(sys_url)
    data = r.json()
    return [x for x in data['data']['en']['feeds'] if x['name']=='free_bike_status'][0]['url']



