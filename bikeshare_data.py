import pandas
import matplotlib.pyplot as plt
import bikeraccoon as br
import datetime
from datetime import datetime as dt, timedelta
from numpy import cumsum
import numpy as np
from meteostat import Point, Daily

# api = br.LiveAPI('bike_share_toronto')
# bixi_api = br.LiveAPI('bixi_montreal')
# trips_by_day = api.get_system_trips(t1=datetime.date(2016,4,13),t2=datetime.date.today(), freq='d')
# trips_by_day_mtl = bixi_api.get_system_trips(t1=datetime.date(2016,4,13),t2=datetime.date.today(), freq='d')
# trips_by_day.index.name = 'date'
# trips_by_day_mtl.index.name = 'date'
# trips_by_day.reset_index(inplace=True)
# trips_by_day_mtl.reset_index(inplace=True)
# trips_by_day['daily_trips'] = trips_by_day.rolling(window=14)['station trips'].mean()
# trips_by_day_mtl['daily_trips'] = trips_by_day_mtl.rolling(window=14)['station trips'].mean()
# fig, ax = plt.subplots()
# ax.plot(trips_by_day.date, trips_by_day.daily_trips, label = "toronto")
# ax.plot(trips_by_day_mtl.date, trips_by_day_mtl.daily_trips, label = "montreal")
# plt.show()

api = br.LiveAPI('bike_share_toronto')
sdf = api.get_stations()
# print(f"Bikes: {bikes + api.get_free_bike_trips(datetime.datetime.now(), freq='h')['num_bikes_available'].sum()}")
print(f"Active Stations: {len(sdf[sdf['active']])}")
fig, ax = plt.subplots()
ax3 = ax.twinx()
fig_2, ax_2 = plt.subplots()
for year in range(2020, 2026):
    temp_start = dt(year,1,1)
    temp_end = dt(year, 12, 31)
    location = Point(43.6532, -79.3832)
    # Get daily data for 2018
    data = Daily(location, temp_start, temp_end)
    data = data.fetch() 
    print(data)
    print(year)
    trips_by_day = api.get_system_trips(t1=datetime.date(year,1,1),t2=datetime.date(year,12,31), freq='d')
    trips_by_day.index.name = 'date'
    trips_by_day.reset_index(inplace=True)
    if year == 2024:
        trips_by_day.loc[328, 'station trips'] = 16500
        trips_by_day.loc[329, 'station trips'] = 16000
        trips_by_day.loc[330, 'station trips'] = 17000
        trips_by_day.loc[331, 'station trips'] = 18000
    trips_by_day['daily_trips'] = trips_by_day.rolling(window=14)['station trips'].mean()
    trips_by_day['total_trips'] = cumsum(trips_by_day['station trips'])
    while(len(trips_by_day.daily_trips) > 365):
        trips_by_day = trips_by_day[:-1]
    if year == 2024:
        daily_trips_2024 = np.array(trips_by_day.daily_trips)
        total_trips_2024 = np.array(trips_by_day.total_trips)
    if year == 2025:
        daily_trips_2025 = np.array(trips_by_day.daily_trips)
        total_trips_2025 = np.array(trips_by_day.total_trips)
    temperature = data.rolling(window=14)['tavg'].mean()
    temperature = temperature[:len(trips_by_day.daily_trips)]
    ax.plot(list(range(1,len(trips_by_day.daily_trips)   )), trips_by_day.daily_trips[0:-1], label = str(year) + " - 14 day rolling average")
    ax3.plot(list(range(1,len(temperature)+1)), temperature, label="Average Temp: " + str(year), alpha=0.3)
    ax.scatter(list(range(1,len(trips_by_day['station trips'])+1)), trips_by_day['station trips'], label = str(year) + " - daily trips", alpha=0.4, s=10)
    length = len(trips_by_day.total_trips)
    print(f"{year} trips: {trips_by_day.total_trips[length-1]}")
    ax_2.plot(list(range(1,len(trips_by_day.total_trips) )), trips_by_day.total_trips[0:-1], label = str(year))

day_number = daily_trips_2025.size
fig_3, ax_3 = plt.subplots()
diff_daily = np.subtract(daily_trips_2025, daily_trips_2024[:day_number])
fig_4, ax_4 = plt.subplots()
print("Trips 2024/2025")
print(total_trips_2025)
print(total_trips_2024[:day_number])
diff_total = np.subtract(total_trips_2025, total_trips_2024[:day_number])
ax_3.plot(list(range(1,len(trips_by_day.total_trips))), list(diff_daily[:-1]))
ax_4.plot(list(range(1,len(trips_by_day.total_trips))), list(diff_total[:-1]))


plt.xlabel("Day of Year")
plt.ylabel("Number of Rides (Million)")
ax.set_ylabel("Number of Trips")
ax.set_xlabel("Day of Year")
ax.set_title("Bike Share Toronto Daily Trips")
ax_2.set_ylabel("Number of Rides (Million)")
ax_2.set_xlabel("Day of Year")
ax_2.set_title("Bike Share Toronto Cumulative Annual Trips")
ax3.set_ylabel("Average temp")
ax.legend(loc="upper left", bbox_to_anchor=(0,1))
ax_2.legend(loc="upper left", bbox_to_anchor=(0,1))

ax3.legend(loc="upper left", bbox_to_anchor=(0,0.6))
plt.legend()
plt.show()
