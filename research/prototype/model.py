"""Data and statistics shared by the two dashboard prototypes (Streamlit and Dash).

Throwaway research code for issue #8: both prototypes call these functions, so
the comparison is only about the screens, not the numbers.
"""

from __future__ import annotations

import datetime as dt
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import load_sources as src  # noqa: E402
from daystats import doy365  # noqa: E402
from scale import CLASSES, GOOD, Thresholds, class_of, daylight, hour_factors, period_scores, sun_hours_utc  # noqa: E402

# Stands in for config.yaml (requirement F18).
CONFIG = {"reference_years": 30, "trend_adjustment": True, "pooling_days": 7}
LAST_COMPLETE_YEAR = 2025
FIRST_YEAR = 1961
TODAY = dt.date.today()
DEFAULT_YEARS = (LAST_COMPLETE_YEAR - CONFIG["reference_years"] + 1, LAST_COMPLETE_YEAR)
LIMITS = ("temperature", "rain", "wind")


@lru_cache(maxsize=1)
def load_hourly() -> pd.DataFrame:
    hourly = src.era5_hourly("copernicus_era5")[["temperature_2m", "precipitation", "wind_gusts_10m"]]
    hourly = hourly.loc[str(FIRST_YEAR):str(LAST_COMPLETE_YEAR)].copy()
    hourly["daylight"] = daylight(hourly.index.tz_convert("UTC"))
    return hourly


@lru_cache(maxsize=16)
def daily_table(years: tuple[int, int], hours: tuple[int, int] | None, trend: bool,
                th: Thresholds) -> tuple[pd.DataFrame, float]:
    """One row per past day: score and the numbers the detail panel needs, for the chosen hours.

    Cached; callers must not modify the returned table.
    """
    hourly = load_hourly()
    hourly = hourly[(hourly.index.year >= years[0]) & (hourly.index.year <= years[1])]
    chosen = hourly["daylight"] if hours is None else (hourly.index.hour >= hours[0]) & (hourly.index.hour < hours[1])
    hourly = hourly[chosen].copy()
    slope = 0.0
    if trend:  # shift each year's temperatures by the fitted warming trend, up to this year
        annual = hourly["temperature_2m"].groupby(hourly.index.year).mean()
        slope = float(np.polyfit(annual.index, annual.to_numpy(), 1)[0])
        hourly["temperature_2m"] += slope * (TODAY.year - hourly.index.year)
    factors = hour_factors(hourly, th)
    day = hourly.index.tz_localize(None).normalize()
    temp = hourly["temperature_2m"].groupby(day)
    out = pd.DataFrame({
        "score": period_scores(hourly, th),
        "tmax": temp.max(),
        "tmin": temp.min(),
        "rain_any": (hourly["precipitation"] >= 0.2).groupby(day).any(),
        "rain_mm": hourly["precipitation"].groupby(day).sum(),
        "gust": hourly["wind_gusts_10m"].groupby(day).max(),
        **{f"lack_{k}": (1 - factors[k]).groupby(day).mean() for k in LIMITS},
    })
    out = out[~((out.index.month == 2) & (out.index.day == 29))]
    out["doy"] = doy365(out.index)
    out["good"] = out["score"] >= GOOD
    return out, slope


def past_days(daily: pd.DataFrame, dates: list, pool: int) -> pd.DataFrame:
    """Past days whose day of year matches the cell's dates (+-pool days for a single day)."""
    doys = set(doy365(pd.DatetimeIndex(dates)))
    if len(dates) == 1:
        d = next(iter(doys))
        doys = {(d - 1 + s) % 365 + 1 for s in range(-pool, pool + 1)}
    return daily[daily["doy"].isin(doys)]


def calendar_grid(daily: pd.DataFrame, start: dt.date, end: dt.date, granularity: str, pool: int,
                  measure: str, relative: bool) -> pd.DataFrame:
    """One row per calendar cell: its dates, chance of good weather, average score and colour value."""
    dates = pd.date_range(start, end)
    if granularity == "Day":
        keys = dates
    elif granularity == "Week":
        keys = dates - pd.to_timedelta(dates.day_of_week, unit="D")
    else:
        keys = dates.to_period("M").to_timestamp()
    grid = pd.DataFrame({"key": keys, "date": dates}).groupby("key")["date"].agg(["min", "max", list]).reset_index()
    grid = grid.rename(columns={"min": "first", "max": "last", "list": "dates"})
    values = []
    for dates_of_cell in grid["dates"]:
        past = past_days(daily, dates_of_cell, pool)
        values.append((past["good"].mean() * 100, past["score"].mean(), len(past)))
    grid[["chance", "mean", "n"]] = values
    grid["value"] = grid[measure]
    grid["colour"] = grid["value"]
    if relative and grid["value"].max() > grid["value"].min():
        grid["colour"] = (grid["value"] - grid["value"].min()) / (grid["value"].max() - grid["value"].min()) * 100
    grid["label"] = [f.strftime("%d.%m.%Y") if f == la else f"{f:%d.%m.}–{la:%d.%m.%Y}"
                     for f, la in zip(grid["first"], grid["last"])]
    grid["key"] = grid["key"].dt.strftime("%Y-%m-%d")
    return grid


def details(daily: pd.DataFrame, dates: list, pool: int, th: Thresholds) -> dict:
    """The numbers of the detail panel for one calendar cell."""
    past = past_days(daily, dates, pool)
    classes = [(name, colour, float(((past["score"] >= low) & (past["score"] < high)).mean() * 100))
               for (low, name, colour), high in zip(CLASSES, [101, 80, 60, 40, 20])]
    spoiled = None
    not_good = past[~past["good"]]
    if len(not_good):
        lack = {k: not_good[f"lack_{k}"].mean() for k in LIMITS}
        spoiled = max(lack, key=lack.get)
        if spoiled == "temperature":
            spoiled = "cold" if not_good["tmax"].median() < th.comfort[0] else "heat"
    rise, set_ = sun_hours_utc(doy365(pd.DatetimeIndex(dates)))
    offset = pd.Timestamp(dates[0]).tz_localize("Europe/Sofia").utcoffset().total_seconds() / 3600

    def clock(hours: float) -> str:
        minutes = int(round((hours + offset) * 60))
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    return {
        "days": len(past), "pooled": len(dates) == 1,
        "chance": past["good"].mean() * 100, "mean": past["score"].mean(), "class": class_of(past["score"].mean()),
        "tmax_median": past["tmax"].median(), "tmax_p10": past["tmax"].quantile(0.1), "tmax_p90": past["tmax"].quantile(0.9),
        "rain_any": past["rain_any"].mean() * 100, "rain_1mm": (past["rain_mm"] >= 1).mean() * 100,
        "heat": (past["tmax"] >= 32).mean() * 100, "frost": (past["tmin"] < 0).mean() * 100,
        "gusts": (past["gust"] >= 50).mean() * 100,
        "classes": classes, "spoiled": spoiled,
        "sunrise": f"{clock(rise.min())}–{clock(rise.max())}", "sunset": f"{clock(set_.min())}–{clock(set_.max())}",
    }
