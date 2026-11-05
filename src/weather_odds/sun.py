"""Sunrise, sunset and daylight hours from the location's coordinates (requirement F14, methodology section 1).

Uses the sunrise equation with the standard altitude of -0.833 degrees
(refraction and the sun's radius), within 2 minutes of the `astral` library at Plovdiv (checked 1965-2026).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

J2000 = 2451545.0
UNIX_EPOCH_JD = 2440587.5
SUN_ALTITUDE = -0.833  # degrees: the sun's upper edge touches the horizon
TILT = 23.4397  # degrees


def sun_times(dates: pd.DatetimeIndex, latitude: float, longitude: float, tz: str) -> pd.DataFrame:
    """Sunrise and sunset in local time for each calendar date, indexed by the date.

    Days without a sunrise or sunset (polar day or night) get NaT.
    """
    dates = pd.DatetimeIndex(dates).normalize()
    if dates.tz is not None:
        dates = dates.tz_localize(None)
    midnight_jd = dates.as_unit("ns").asi8 / 86_400e9 + UNIX_EPOCH_JD
    n = np.ceil(midnight_jd - J2000 + 0.0008)  # days from 1 January 2000, noon, to the date's noon
    j_star = n - longitude / 360
    mean_anomaly = np.radians((357.5291 + 0.98560028 * j_star) % 360)
    centre = 1.9148 * np.sin(mean_anomaly) + 0.0200 * np.sin(2 * mean_anomaly) + 0.0003 * np.sin(3 * mean_anomaly)
    ecliptic = np.radians((np.degrees(mean_anomaly) + centre + 180 + 102.9372) % 360)
    transit = J2000 + j_star + 0.0053 * np.sin(mean_anomaly) - 0.0069 * np.sin(2 * ecliptic)
    sin_decl = np.sin(ecliptic) * np.sin(np.radians(TILT))
    cos_decl = np.cos(np.arcsin(sin_decl))
    lat = np.radians(latitude)
    cos_hour_angle = (np.sin(np.radians(SUN_ALTITUDE)) - np.sin(lat) * sin_decl) / (np.cos(lat) * cos_decl)
    with np.errstate(invalid="ignore"):
        half_day = np.degrees(np.arccos(cos_hour_angle)) / 360  # in days
    rise = _from_julian(transit - half_day, tz)
    set_ = _from_julian(transit + half_day, tz)
    return pd.DataFrame({"sunrise": rise, "sunset": set_}, index=pd.DatetimeIndex(dates, name="date"))


def daylight(hours: pd.DatetimeIndex, latitude: float, longitude: float) -> np.ndarray:
    """True for the hours that start between sunrise and sunset of their local date."""
    local_dates = hours.tz_localize(None).normalize()
    unique = local_dates.unique()
    times = sun_times(unique, latitude, longitude, str(hours.tz)).reindex(local_dates)
    starts = hours.as_unit("ns").asi8
    rise = pd.DatetimeIndex(times["sunrise"]).as_unit("ns").asi8
    set_ = pd.DatetimeIndex(times["sunset"]).as_unit("ns").asi8
    known = times["sunrise"].notna().to_numpy()
    return known & (starts >= rise) & (starts <= set_)


def _from_julian(jd: np.ndarray, tz: str) -> pd.DatetimeIndex:
    nanoseconds = np.round((np.asarray(jd) - UNIX_EPOCH_JD) * 86_400e9)
    valid = np.isfinite(nanoseconds)
    out = pd.to_datetime(np.where(valid, nanoseconds, 0).astype("int64"), unit="ns", utc=True)
    out = out.floor("s").tz_convert(tz)
    return out.where(valid, pd.NaT)
