"""The outdoor-weather scale (methodology section 4): a score from 0 (bad) to 100 (great) per hour and per period.

Each hour is scored with the thresholds of its time band (night, morning,
afternoon, evening). A period's score is the mean of its hour scores, capped
when the rain over its hours reaches a cap's amount.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from weather_odds.config import BAND_HOURS, Scale, Thresholds


def temperature_factor(t: np.ndarray, th: Thresholds) -> np.ndarray:
    low, high = th.comfort
    cold = np.clip((t - th.cold_zero) / (low - th.cold_zero), 0, 1)
    hot = np.clip((th.hot_zero - t) / (th.hot_zero - high), 0, 1)
    return np.minimum(cold, hot)


def rain_factor(mm: np.ndarray, th: Thresholds) -> np.ndarray:
    r = th.rain
    factor = np.where(mm < r.light_mm, 1.0, np.where(mm < r.heavy_mm, r.light_factor, r.heavy_factor))
    return np.where(np.isnan(mm), np.nan, factor)


def gust_factor(kmh: np.ndarray, th: Thresholds) -> np.ndarray:
    return np.clip((th.gust_zero - kmh) / (th.gust_zero - th.gust_ok), 0, 1)


def thunder_factor(thunder: np.ndarray, th: Thresholds) -> np.ndarray:
    return np.where(thunder, th.thunder_factor, 1.0)


def hour_factors(hourly: pd.DataFrame, scale: Scale) -> pd.DataFrame:
    """Each factor per hour (1 = no problem), with the thresholds of the hour's time band.

    Hours without thunder data count as without thunder.
    """
    hour = hourly.index.hour
    if "thunder" in hourly:
        thunder = hourly["thunder"].fillna(False).to_numpy(dtype=bool)
    else:
        thunder = np.zeros(len(hourly), dtype=bool)
    t = hourly["temperature"].to_numpy(dtype=float)
    mm = hourly["precipitation"].to_numpy(dtype=float)
    gust = hourly["wind_gust"].to_numpy(dtype=float)
    out = np.full((len(hourly), 4), np.nan)
    for band, (start, end) in BAND_HOURS.items():
        rows = (hour >= start) & (hour < end)
        if not rows.any():
            continue
        th = scale.for_band(band)
        out[rows] = np.column_stack(
            [
                temperature_factor(t[rows], th),
                rain_factor(mm[rows], th),
                gust_factor(gust[rows], th),
                thunder_factor(thunder[rows], th),
            ]
        )
    return pd.DataFrame(out, index=hourly.index, columns=["temperature", "rain", "wind", "thunder"])


def hour_scores(hourly: pd.DataFrame, scale: Scale) -> pd.Series:
    """100 x the product of the factors; missing where an input is missing."""
    return 100 * hour_factors(hourly, scale).prod(axis=1, skipna=False)


def day_scores(hourly: pd.DataFrame, scale: Scale) -> pd.Series:
    """Score per local date over the hours given (already cut to the chosen hours), with the rain caps."""
    scores = hour_scores(hourly, scale)
    day = pd.DatetimeIndex(hourly.index.tz_localize(None).normalize(), name="date")
    mean = scores.groupby(day).mean()
    rain = hourly["precipitation"].groupby(day).sum()
    for cap in scale.thresholds.rain_caps:
        mean = mean.where(rain < cap.from_mm, np.minimum(mean, cap.max_score))
    return mean
