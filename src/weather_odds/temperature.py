"""The location's hourly temperature: the station's measurements, with gaps filled (methodology §1 and §10).

How each gap is filled was chosen by hiding hours the station did measure,
filling them, and comparing (`weather_odds.checks`, D46):

- gaps of up to SHORT_GAP hours, including the hours between the 3-hourly
  readings before 1997: the station's own mean daily curve for the month,
  pinned to the readings on both sides;
- gaps of up to LONG_GAP hours: ERA5, corrected by the station-minus-ERA5
  difference for the same month and hour of day in the years around the gap
  (ERA5 drifts against the station over the decades);
- longer gaps stay missing, so years without station data (1996, 1961-1964,
  1968-1972) are left out (D43).

Every hour records where its value came from in `temperature_source`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SHORT_GAP = 6  # hours
LONG_GAP = 7 * 24  # hours
WINDOW = 2  # years on each side for the ERA5 correction
FULL_DAY = 24  # readings a day needs to count towards the station's daily curve: complete days only

STATION, CURVE, ERA5 = "station", "station curve", "era5 corrected"


def fill_temperature(station: pd.Series, era5: pd.Series) -> pd.DataFrame:
    """Hourly temperature over the span of both series, with the source of each hour.

    Both inputs are hourly with time-zone-aware indexes; the result is in the station's time zone.
    """
    tz = station.index.tz
    station, era5 = station.tz_convert("UTC"), era5.tz_convert("UTC")
    index = pd.date_range(
        min(station.index.min(), era5.index.min()), max(station.index.max(), era5.index.max()), freq="h", name="time"
    )
    station, era5 = station.reindex(index), era5.reindex(index)

    gap = gap_lengths(station)
    curve = station_curve(station)
    from_curve = pinned(station, curve)
    from_era5 = era5 + era5_correction(station, era5)

    measured = station.notna().to_numpy()
    short = ~measured & (gap <= SHORT_GAP) & from_curve.notna().to_numpy()
    long = ~measured & ~short & (gap <= LONG_GAP) & from_era5.notna().to_numpy()
    choices = [measured, short, long]
    values = np.select(choices, [station.to_numpy(), from_curve.to_numpy(), from_era5.to_numpy()], np.nan)
    sources = pd.array(np.select(choices, [STATION, CURVE, ERA5], ""), dtype="string")
    out = pd.DataFrame({"temperature": values, "temperature_source": sources}, index=index)
    out.loc[out["temperature_source"] == "", "temperature_source"] = pd.NA
    out.index = out.index.tz_convert(tz)
    return out


def gap_lengths(values: pd.Series) -> np.ndarray:
    """For each missing hour, the length of the run of missing hours it belongs to; 0 where measured.

    Runs at the start or end of the series, without a reading on one side, count as endless.
    """
    present = values.notna().to_numpy()
    if not present.any():
        return np.full(len(values), np.inf)
    position = np.arange(len(values))
    readings = position[present]
    after = np.searchsorted(readings, position)  # the next reading at or after each hour
    previous = np.where(after > 0, readings[np.maximum(after - 1, 0)], -np.inf)
    following = np.where(after < len(readings), readings[np.minimum(after, len(readings) - 1)], np.inf)
    return np.where(present, 0, following - previous - 1)


def station_curve(station: pd.Series) -> pd.Series:
    """The station's mean daily curve: each hour's departure from its day's mean, by month and UTC hour,
    from days with at least FULL_DAY readings. Returned for every hour of the index."""
    day = station.index.normalize()
    counts = station.groupby(day).transform("count")
    full = station.where(counts >= FULL_DAY)
    departure = full - full.groupby(day).transform("mean")
    index = station.index
    mean = departure.groupby([index.month, index.hour]).mean()
    keys = pd.MultiIndex.from_arrays([index.month, index.hour])
    return pd.Series(mean.reindex(keys).to_numpy(), index=index)


def pinned(station: pd.Series, shape: pd.Series) -> pd.Series:
    """shape plus the station's offset from it, interpolated linearly between readings."""
    offset = (station - shape).interpolate(limit_area="inside")
    return shape + offset


def era5_correction(station: pd.Series, era5: pd.Series) -> pd.Series:
    """Mean station-minus-ERA5 difference by month and hour of day over the WINDOW years on each side."""
    difference = station - era5
    index = difference.index
    grouped = difference.groupby([index.month, index.hour, index.year])
    sums, counts = grouped.sum().unstack(), grouped.count().unstack()  # (month, hour) x year
    years = range(index.year.min(), index.year.max() + 1)
    sums, counts = sums.reindex(columns=years, fill_value=0), counts.reindex(columns=years, fill_value=0)
    width = 2 * WINDOW + 1
    rolled = (
        sums.T.rolling(width, center=True, min_periods=1).sum()
        / counts.T.rolling(width, center=True, min_periods=1).sum()
    )
    table = rolled.T.stack()  # (month, hour, year)
    keys = pd.MultiIndex.from_arrays([index.month, index.hour, index.year])
    return pd.Series(table.reindex(keys).to_numpy(), index=index)
