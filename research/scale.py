"""The outdoor-weather scale (phase-0 research; definition in docs/spec/methodology.md, section 4).

Every hour gets a score from 0 (bad) to 100 (great) from temperature, rain and
wind gusts; a period (one day and the chosen hours) is the mean of its hour
scores, capped when its rain reaches 1 mm (at most Fair) or 5 mm (at most Poor).
Thunder is not scored yet: ERA5 has no thunder variable.

Used by preview_scale.py and the dashboard prototype in research/prototype/.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

LAT, LON = 42.1333, 24.75  # Plovdiv, WMO 15625
GOOD = 60
CLASSES = [(80, "Great", "#1a9850"), (60, "Good", "#91cf60"), (40, "Fair", "#fee08b"),
           (20, "Poor", "#fc8d59"), (0, "Bad", "#d73027")]


@dataclass(frozen=True)
class Thresholds:
    """Defaults from methodology section 4; the dashboard can override each one."""

    comfort: tuple[float, float] = (18.0, 26.0)  # deg C: no penalty inside this range
    cold_zero: float = 0.0  # deg C: temperature factor reaches 0
    hot_zero: float = 38.0
    rain: tuple = ((0.2, 1.0), (1.0, 0.5), (np.inf, 0.2))  # (hourly mm below which, factor)
    rain_caps: tuple = ((5.0, 39.0), (1.0, 59.0))  # (mm in the chosen hours from which, highest score)
    gust_ok: float = 30.0  # km/h
    gust_zero: float = 75.0


def sun_hours_utc(doy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sunrise and sunset in decimal UTC hours for a day of year (NOAA approximation)."""
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
    half_day = np.degrees(np.arccos(-np.tan(np.radians(LAT)) * np.tan(decl))) / 15
    b = 2 * np.pi * (doy - 81) / 364
    eot_h = (9.87 * np.sin(2 * b) - 7.53 * np.cos(b) - 1.5 * np.sin(b)) / 60
    noon = 12 - LON / 15 - eot_h
    return noon - half_day, noon + half_day


def daylight(utc: pd.DatetimeIndex) -> np.ndarray:
    """True for hours stamped between sunrise and sunset."""
    rise, set_ = sun_hours_utc(utc.dayofyear.to_numpy())
    hour = utc.hour.to_numpy()
    return (hour >= rise) & (hour <= set_)


def temperature_factor(t: np.ndarray, th: Thresholds = Thresholds()) -> np.ndarray:
    cold = np.clip((t - th.cold_zero) / (th.comfort[0] - th.cold_zero), 0, 1)
    hot = np.clip((th.hot_zero - t) / (th.hot_zero - th.comfort[1]), 0, 1)
    return np.minimum(cold, hot)


def rain_factor(p: np.ndarray, th: Thresholds = Thresholds()) -> np.ndarray:
    out = np.full(p.shape, th.rain[-1][1])
    for limit, factor in reversed(th.rain):
        out = np.where(p < limit, factor, out)
    return out


def gust_factor(g: np.ndarray, th: Thresholds = Thresholds()) -> np.ndarray:
    return np.clip((th.gust_zero - g) / (th.gust_zero - th.gust_ok), 0, 1)


def hour_factors(hourly: pd.DataFrame, th: Thresholds = Thresholds()) -> pd.DataFrame:
    """Factor per hour (1 = no problem) for an hourly table with ERA5 column names."""
    return pd.DataFrame({
        "temperature": temperature_factor(hourly["temperature_2m"].to_numpy(), th),
        "rain": rain_factor(hourly["precipitation"].to_numpy(), th),
        "wind": gust_factor(hourly["wind_gusts_10m"].to_numpy(), th),
    }, index=hourly.index)


def period_scores(hourly: pd.DataFrame, th: Thresholds = Thresholds(), min_hours: int = 1) -> pd.Series:
    """Score per local date over the hours in `hourly` (already cut to the chosen hours)."""
    hour_score = 100 * hour_factors(hourly, th).prod(axis=1)
    day = hour_score.index.tz_localize(None).normalize()
    rain = hourly["precipitation"].groupby(day).sum()
    score = hour_score.groupby(day).mean()
    for limit, cap in th.rain_caps:
        score = score.where(rain < limit, np.minimum(score, cap))
    return score[hour_score.groupby(day).size() >= min_hours]


def class_of(score: float) -> str:
    return next(name for low, name, _ in CLASSES if score >= low)
