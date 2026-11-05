"""Filling the station's missing temperature hours with ERA5 corrected to the station (gap plan, D34, D43).

Two fills, chosen by the length of the gap:

- **Short gaps** (up to `interpolate_hours`): ERA5's shape between the station's
  readings. The station-minus-ERA5 difference is interpolated linearly across
  the gap and added to ERA5. This also rebuilds the hours between the 3-hourly
  readings before 1997.
- **Longer gaps** (up to `fill_days`): ERA5 plus the station-minus-ERA5
  difference typical for the month and hour of day, averaged over the years
  within `window_years` of the gap. ERA5 drifts against the station over the
  decades, so the correction comes from nearby years only.

Gaps longer than `fill_days`, such as 1996 with no station data at all, stay
empty unless `fill_long_gaps` is set (D43). Every fill is checked by hiding
measured hours and filling them the same way (`weather_odds.checks`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

STATION, INTERPOLATED, ERA5 = "station", "interpolated", "era5"
SOURCES = (STATION, INTERPOLATED, ERA5)


@dataclass(frozen=True)
class FillSettings:
    interpolate_hours: int = 12
    fill_days: int = 31
    window_years: int = 3
    fill_long_gaps: bool = False


def run_lengths(missing: np.ndarray) -> np.ndarray:
    """For each position, the length of the run of True values it belongs to; 0 where False."""
    missing = np.asarray(missing, dtype=bool)
    if not missing.any():
        return np.zeros(len(missing), dtype=int)
    edges = np.diff(np.concatenate([[0], missing.astype(int), [0]]))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    out = np.zeros(len(missing), dtype=int)
    for start, end in zip(starts, ends, strict=True):
        out[start:end] = end - start
    return out


def interpolated_difference(station: pd.Series, era5: pd.Series, max_hours: int) -> pd.Series:
    """Station minus ERA5 on ERA5's hours, interpolated across gaps of up to max_hours between readings."""
    difference = station.reindex(era5.index) - era5
    runs = run_lengths(difference.isna().to_numpy())
    filled = difference.interpolate(method="linear", limit_area="inside")
    return filled.where((runs == 0) | (runs <= max_hours))


def typical_difference(difference: pd.Series, window_years: int) -> pd.Series:
    """Mean of `difference` by year, month and UTC hour, each averaged over the years within window_years.

    Returned on difference's index: for every hour, the typical difference of its month and hour of day
    in the surrounding years (NaN when none of them has data).
    """
    utc = difference.index.tz_convert("UTC")
    local = difference.index
    keys = pd.DataFrame({"year": local.year, "month": local.month, "hour": utc.hour, "value": difference.to_numpy()})
    grouped = keys.dropna().groupby(["year", "month", "hour"])["value"].agg(["sum", "count"])
    if grouped.empty:
        return pd.Series(np.nan, index=difference.index)
    years = range(int(local.year.min()), int(local.year.max()) + 1)
    sums = grouped["sum"].unstack(["month", "hour"]).reindex(years).fillna(0.0)
    counts = grouped["count"].unstack(["month", "hour"]).reindex(years).fillna(0.0)
    width = 2 * window_years + 1
    total = sums.rolling(width, center=True, min_periods=1).sum()
    n = counts.rolling(width, center=True, min_periods=1).sum()
    mean = (total / n.where(n > 0)).stack(["month", "hour"], future_stack=True)
    lookup = pd.MultiIndex.from_arrays([keys["year"], keys["month"], keys["hour"]])
    return pd.Series(mean.reindex(lookup).to_numpy(), index=difference.index)


def fill_temperature(station: pd.Series, era5: pd.Series, settings: FillSettings | None = None) -> pd.DataFrame:
    """Hourly temperature on ERA5's hours: the station's readings, with gaps filled from ERA5.

    Returns columns `temperature` and `temperature_source` (station, interpolated or era5; missing where
    nothing was filled).
    """
    settings = settings or FillSettings()
    era5 = era5.sort_index()
    measured = station.reindex(era5.index)
    difference = interpolated_difference(station, era5, settings.interpolate_hours)
    temperature = measured.copy()
    source = pd.Series(pd.NA, index=era5.index, dtype="string")
    source[measured.notna()] = STATION
    short = measured.isna() & difference.notna()
    temperature[short] = era5[short] + difference[short]
    source[short] = INTERPOLATED

    runs = run_lengths(measured.isna().to_numpy())
    allowed = (runs <= settings.fill_days * 24) | settings.fill_long_gaps
    rest = temperature.isna() & era5.notna() & allowed
    if rest.any():
        correction = typical_difference(difference, settings.window_years)
        fill = era5 + correction
        rest &= fill.notna()
        temperature[rest] = fill[rest]
        source[rest] = ERA5
    return pd.DataFrame({"temperature": temperature, "temperature_source": source})
