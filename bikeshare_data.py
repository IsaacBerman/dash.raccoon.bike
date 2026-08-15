import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import bikeraccoon as br
from datetime import datetime as dt, timedelta
from numpy import cumsum
import numpy as np
from meteostat import Point, Daily
import os
import matplotlib as mpl

# ── Site branding (matches toronto-bike-counters globals.css) ───────────────
PAPER = '#f3f2ec'    # --paper: warm site background
PANEL = '#ffffff'    # --panel: white card the chart sits on
INK = '#16150f'      # --ink: primary text / heavy rules
INK_2 = '#57554b'    # --ink-2: secondary text (axis labels)
INK_3 = '#8a887c'    # --ink-3: muted text (tick labels)
LINE = '#e2e0d6'     # --line: hairline borders and grid
ACCENT = '#e8590c'   # --accent: brand orange

# Distinct hue per year, matching the counters site (see getYearColor in
# toronto-bike-counters/app/components/counterChart.js) so the same year reads
# as the same colour across both. Years get toggled and compared in any
# combination, so any two can end up adjacent: these were solved against the
# all-pairs gate rather than picked, and validated on a white panel — worst
# pair CVD ΔE 8.3, normal-vision ΔE 16.0, all eleven >= 3:1 contrast.
# Keep the two lists in step, and re-validate before changing a value.
YEAR_COLORS = {
    2016: '#fe516b',
    2017: '#a92501',
    2018: '#a07a0c',
    2019: '#00633c',
    2020: '#01a38f',
    2021: '#006fa9',
    2022: '#1d3cff',
    2023: '#8688ff',
    2024: '#6803bf',
    2025: '#ff35de',
    2026: '#b8067e',
}

mpl.rcParams.update({
    # Archivo is the site face; fall back to the closest installed grotesque
    'font.family': 'sans-serif',
    'font.sans-serif': ['Archivo', 'Helvetica Neue', 'Arial', 'DejaVu Sans'],
    'figure.facecolor': PAPER,
    'savefig.facecolor': PAPER,
    'axes.facecolor': PANEL,
    'axes.edgecolor': LINE,
    'axes.linewidth': 1.0,
    'axes.grid': True,
    'axes.axisbelow': True,
    'grid.color': LINE,
    'grid.linewidth': 0.8,
    'axes.labelcolor': INK_2,
    'axes.labelsize': 9.5,
    'axes.labelweight': 'semibold',
    'xtick.color': INK_3,
    'ytick.color': INK_3,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'text.color': INK,
    'legend.frameon': True,
    'legend.facecolor': PANEL,
    'legend.edgecolor': LINE,
    'legend.framealpha': 1.0,
    'legend.fontsize': 8.5,
})


def kicker_text(s):
    """Approximate the site's letter-spaced uppercase kicker (.dd-kicker)."""
    return ' '.join(s.upper())


def style_panel(ax, kicker, title):
    """Style an axes like the site's ruled panel (.dd-panel-ruled):
    white card, hairline border, heavy ink top rule, orange kicker + bold title."""
    for side in ('left', 'right', 'bottom'):
        ax.spines[side].set_color(LINE)
        ax.spines[side].set_linewidth(1.0)
    ax.spines['top'].set_color(INK)
    ax.spines['top'].set_linewidth(3.0)
    ax.grid(axis='y', color=LINE, linewidth=0.8)
    ax.grid(axis='x', visible=False)
    ax.set_axisbelow(True)
    ax.annotate(kicker_text(kicker), xy=(0, 1), xycoords='axes fraction',
                xytext=(0, 30), textcoords='offset points', va='bottom',
                fontsize=8, fontweight='bold', color=ACCENT)
    ax.annotate(title, xy=(0, 1), xycoords='axes fraction',
                xytext=(0, 9), textcoords='offset points', va='bottom',
                fontsize=14, fontweight='bold', color=INK)
# ────────────────────────────────────────────────────────────────────────────

print("about to get systems")
br.get_systems()
api = br.LiveAPI('bike_share_toronto')
sdf = api.get_stations()
print(sdf)

# ── Historical daily ridership ──────────────────────────────────────────────
# The City's trip-level archives, pre-reduced to one row per day by
# scripts/build_bikeshare_daily.py. That file is authoritative through its last
# date; everything after it comes from the live bikeraccoon API.
HISTORICAL_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'data', 'bikeshare_daily.csv')

SOURCE_NOTE = ('Ridership to {cutoff:%b %-d, %Y}: City of Toronto Open Data '
               '(open.toronto.ca/dataset/bike-share-toronto-ridership-data). '
               'Later days: bikeraccoon live estimates.')

# Which trips the year-over-year charts count.
#   FILTER_USER: 'all' | 'member' | 'casual'
#   FILTER_BIKE: 'all' | 'classic' | 'electric'
# Anything other than all/all is archive-only — the live feed reports totals
# with no splits, so a filtered year stops at the archive cutoff. Bike model
# isn't recorded before 2024, so filtering on it drops the earlier years.
FILTER_USER = 'all'
FILTER_BIKE = 'all'

hist = pd.read_csv(HISTORICAL_CSV, parse_dates=['date'])
HIST_CUTOFF = hist['date'].max()
print(f"Loaded archived ridership: {len(hist):,} days "
      f"({hist['date'].min():%Y-%m-%d} → {HIST_CUTOFF:%Y-%m-%d}), "
      f"{hist['trips'].sum():,} trips.")


def credit(fig):
    """Stamp the data provenance along the bottom of a figure."""
    fig.text(0.01, 0.012, SOURCE_NOTE.format(cutoff=HIST_CUTOFF),
             fontsize=6.5, color=INK_3, ha='left', va='bottom')


def trips_matching(user='all', bike='all'):
    """Daily archive counts for one trip type.

    Only what can't be derived is stored, so a classic/electric total is the
    user x model joint summed over riders. Days where the requested split
    isn't recorded drop out rather than reading as zero.
    """
    if user == 'all' and bike == 'all':
        col = hist['trips']
    elif bike == 'all':
        col = hist[f'trips_{user}']
    elif user == 'all':
        col = hist[f'trips_member_{bike}'] + hist[f'trips_casual_{bike}']
    else:
        col = hist[f'trips_{user}_{bike}']

    out = pd.DataFrame({'date': hist['date'], 'trips': col})
    return out.dropna(subset=['trips']).reset_index(drop=True)


def daily_trips(year, user='all', bike='all'):
    """Trips per day for one calendar year, optionally for one trip type.

    Reads from the archive up to its cutoff and falls back to the live API for
    any later dates, so the current year stitches the two together. The live
    feed reports totals only — a filtered series therefore stops at the cutoff.
    """
    archive = trips_matching(user, bike)
    frames = [archive.loc[archive['date'].dt.year == year]]

    if user == 'all' and bike == 'all':
        live_start = max(HIST_CUTOFF + timedelta(days=1), dt(year, 1, 1))
        live_end = min(dt(year, 12, 31), dt.now())
        if live_start <= live_end:
            live = api.get_trips(t1=live_start.date(), t2=live_end.date(), freq='d')
            live.index.name = 'date'
            live = live.reset_index()[['date', 'trips']]
            live['date'] = pd.to_datetime(live['date'], utc=True).dt.tz_localize(None)
            frames.append(live)

    return (pd.concat(frames, ignore_index=True)
            .dropna(subset=['date'])
            .sort_values('date')
            .reset_index(drop=True))


def monthly_split(left, right, kind):
    """Whole-month totals for a two-way split, e.g. classic vs electric.

    Partial months are dropped: in a bar chart a half-recorded month reads as a
    real fall in ridership.
    """
    cols = ({'classic': ['trips_member_classic', 'trips_casual_classic'],
             'electric': ['trips_member_electric', 'trips_casual_electric']}
            if kind == 'bike' else
            {'member': ['trips_member'], 'casual': ['trips_casual']})

    df = hist[['date']].copy()
    for name, parts in cols.items():
        df[name] = hist[parts].sum(axis=1, min_count=len(parts))
    df = df.dropna(subset=[left, right])
    if df.empty:
        return df

    df['month'] = df['date'].dt.to_period('M')
    grouped = df.groupby('month').agg(
        days=('date', 'size'), **{left: (left, 'sum'), right: (right, 'sum')})
    whole = grouped[grouped['days'] == grouped.index.days_in_month]
    return whole.reset_index()
# ────────────────────────────────────────────────────────────────────────────

# Create separate figures
fig1, ax1 = plt.subplots(figsize=(10, 6))
fig2, ax2 = plt.subplots(figsize=(10, 6))
fig3, ax3 = plt.subplots(figsize=(10, 6))
fig4, ax4 = plt.subplots(figsize=(10, 6))

# Hourly graph (Last 2 Weeks)
now = dt.now()
print(now)
t1 = now
t2 = t1 - timedelta(days=15)
hourly_df = api.get_trips(t1, t2, freq='h').reset_index()
ax1.bar(hourly_df['datetime'], hourly_df['trips'], color=ACCENT)
style_panel(ax1, "Bike Share Toronto", "Hourly trips — last two weeks")
ax1.set_ylabel("Trips")

# Annual graphs
daily_trips_2025_data = None
daily_trips_2026_data = None

for year in range(2016, 2027):
    temp_start = dt(year, 1, 1)
    temp_end = dt(year, 12, 31)
    location = Point(43.6532, -79.3832)
    data = Daily(location, temp_start, temp_end)
    data = data.fetch()

    trips_by_day = daily_trips(year, FILTER_USER, FILTER_BIKE)
    if trips_by_day.empty:
        continue

    # Create a day-of-year column for plotting (all years aligned)
    # Use a reference year (2020 is a leap year) for consistent day-of-year mapping
    reference_year = 2020
    trips_by_day['date_for_plot'] = trips_by_day['date'].apply(
        lambda x: dt(reference_year, x.month, x.day)
    )
    
    trips_by_day['daily_trips'] = trips_by_day.rolling(window=14)['trips'].mean()
    trips_by_day['total_trips'] = cumsum(trips_by_day['trips'])

    if year == 2025:
        daily_trips_2025_data = trips_by_day[['date_for_plot', 'daily_trips', 'total_trips', 'trips']].copy()
    if year == 2026:
        daily_trips_2026_data = trips_by_day[['date_for_plot', 'daily_trips', 'total_trips', 'trips']].copy()

    color = YEAR_COLORS.get(year, INK_3)
    # Scatter plot with month-day on x-axis (dots share the year's legend entry)
    ax3.scatter(
        trips_by_day['date_for_plot'],
        trips_by_day['trips'],
        label='_nolegend_',
        alpha=0.2,
        s=9,
        color=color
    )
    ax3.plot(
        trips_by_day['date_for_plot'].iloc[0:-1],
        trips_by_day['daily_trips'].iloc[0:-1],
        label=f"{year} (14-day avg)",
        color=color,
        linewidth=2
    )

    ax4.plot(
        trips_by_day['date_for_plot'].iloc[0:-1],
        trips_by_day['total_trips'].iloc[0:-1],
        label=str(year),
        color=color,
        linewidth=2
    )

# Check if we have both datasets before trying to merge
if daily_trips_2025_data is not None and daily_trips_2026_data is not None:
    # Merge on date_for_plot (month-day)
    merged_data = pd.merge(
        daily_trips_2025_data[['date_for_plot', 'daily_trips', 'total_trips']],
        daily_trips_2026_data[['date_for_plot', 'daily_trips', 'total_trips']],
        on='date_for_plot',
        how='inner',
        suffixes=('_2025', '_2026')
    )
    
    # Extract aligned data
    common_dates = merged_data['date_for_plot'].values
    daily_2025_aligned = merged_data['daily_trips_2025'].values
    daily_2026_aligned = merged_data['daily_trips_2026'].values
    total_2025_aligned = merged_data['total_trips_2025'].values
    total_2026_aligned = merged_data['total_trips_2026'].values
    
    # Calculate differences only for aligned dates
    diff_daily = daily_2026_aligned - daily_2025_aligned
    diff_total = total_2026_aligned - total_2025_aligned
    
    # Create difference plots with month-day on x-axis
    fig_diff, (ax_diff1, ax_diff2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Only plot where we have data for both years
    plot_dates = common_dates[:-1] if len(common_dates) > 1 else common_dates
    plot_diff_daily = diff_daily[:-1] if len(diff_daily) > 1 else diff_daily
    plot_diff_total = diff_total[:-1] if len(diff_total) > 1 else diff_total
    
    ax_diff1.plot(plot_dates, plot_diff_daily, color=ACCENT, linewidth=2)
    style_panel(ax_diff1, "2026 vs 2025", "Daily trips difference")
    ax_diff1.set_xlabel("Date")
    ax_diff1.set_ylabel("Difference in trips")

    ax_diff2.plot(plot_dates, plot_diff_total, color=ACCENT, linewidth=2)
    style_panel(ax_diff2, "2026 vs 2025", "Cumulative trips difference")
    ax_diff2.set_xlabel("Date")
    ax_diff2.set_ylabel("Difference in total trips")

    # Ink zero baseline so above/below last year reads at a glance
    for ax in [ax_diff1, ax_diff2]:
        ax.axhline(0, color=INK, linewidth=1)
    
    # Format x-axis to show month-day on difference plots
    for ax in [ax_diff1, ax_diff2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Name the active filter in the kicker so a filtered chart can't be mistaken
# for the full record.
FILTER_LABEL = ' · '.join(
    [p for p in (None if FILTER_USER == 'all' else f'{FILTER_USER} riders',
                 None if FILTER_BIKE == 'all' else f'{FILTER_BIKE} bikes') if p])
KICKER = f"Bike Share Toronto — {FILTER_LABEL}" if FILTER_LABEL else "Bike Share Toronto"

ax3.set_xlabel("Date")
ax3.set_ylabel("Trips per day")
style_panel(ax3, KICKER, "Daily trips by year")
ax3.legend(loc="upper left")

ax4.set_ylabel("Total trips (millions)")
# Ticks in millions (e.g. 4.5) instead of raw counts with a 1e6 offset label
ax4.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, pos: f'{x / 1e6:g}'))
ax4.set_xlabel("Date")
style_panel(ax4, KICKER, "Cumulative annual trips")
ax4.legend(loc="upper left")

# Format x-axis to show month-day on main plots
for ax in [ax3, ax4]:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

# ── Trip type comparison ────────────────────────────────────────────────────
# Two-way splits as paired monthly bars. Categorical, not ordered, so the two
# hues are distinct rather than steps of one ramp; both pairs clear the
# colour-blind separation target and 3:1 contrast on the panel.
SPLIT_COLORS = {'classic': '#006fa9', 'electric': '#a07a0c',
                'member': '#00633c', 'casual': '#ff35de'}

fig5, (ax5a, ax5b) = plt.subplots(2, 1, figsize=(13, 9))

for ax, (left, right, kind, kicker, title, sub) in zip(
    (ax5a, ax5b),
    [('classic', 'electric', 'bike', 'Bike type',
      'E-bike vs classic trips by month',
      'Bike model is only recorded from January 2024.'),
     ('member', 'casual', 'user', 'Rider type',
      'Member vs casual trips by month',
      'Oct 2021-Dec 2023 not shown: source data not accurate.')],
):
    split = monthly_split(left, right, kind)
    if split.empty:
        continue

    x = np.arange(len(split))
    width = 0.42
    ax.bar(x - width / 2, split[left], width, label=left.capitalize(),
           color=SPLIT_COLORS[left])
    ax.bar(x + width / 2, split[right], width, label=right.capitalize(),
           color=SPLIT_COLORS[right])

    # Roughly a dozen labels however many months are in range
    step = max(1, len(split) // 12)
    ax.set_xticks(x[::step])
    ax.set_xticklabels([p.strftime('%b %Y') for p in split['month'][::step]],
                       rotation=45, ha='right')
    ax.set_xlim(-1, len(split))
    ax.set_ylabel('Trips per month')
    ax.yaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda v, pos: f'{v / 1000:g}k' if v else '0'))
    style_panel(ax, kicker, title)
    ax.legend(loc='upper left')
    # Right-aligned in the header band, clear of the legend inside the panel
    ax.annotate(sub, xy=(1, 1), xycoords='axes fraction',
                xytext=(0, 12), textcoords='offset points', va='bottom',
                ha='right', fontsize=7.5, color=INK_3)

# Lay out every figure, reserving headroom for the kicker + title lockup
for num in plt.get_fignums():
    fig = plt.figure(num)
    fig.tight_layout(rect=[0, 0.03, 1, 0.9])
    credit(fig)
plt.show()