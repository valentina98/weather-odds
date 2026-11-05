"""The location's hourly and daily tables, combined from the sources (milestone 3, methodology sections 1 and 10).

Hourly table, indexed by the start of each local hour (ERA5's hours):

    temperature          deg C: the station, with gaps filled (weather_odds.temperature, D46)
    temperature_source   station, station curve or era5 corrected; missing where nothing was filled
    precipitation        mm in the hour, ERA5
    wind_gust            km/h, ERA5
    rain_seen            airport reports in the hour saw rain; missing without reports
    thunder              airport reports in the hour saw thunder; missing without reports
    daylight             the hour starts between sunrise and sunset

Daily table, indexed by the local calendar date:

    tmax, tmin           deg C, from the hourly temperatures; missing unless every hour has one
    station_hours        hours with a station reading
    precipitation        mm over the local day, ERA5
    wet                  precipitation reaches the month's calibrated wet-day threshold (D38)
    wind_gust_max        km/h
    thunder              thunder reported that day; missing where no source reports thunder that year
    thunder_source       airport or gsod
    sunrise, sunset      local times

The ERA5 wet-day thresholds are calibrated per month so that ERA5 has as many wet
days as the station had in the calibration years (methodology section 10).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from weather_odds.cache import Cache
from weather_odds.config import Config
from weather_odds.sun import daylight, sun_times
from weather_odds.temperature import fill_temperature

AIRPORT_DAY_HOURS = 16  # hours with reports for an airport day to count as observed
MIN_YEAR_DAYS = 30  # observed days for a source's year to count
MIN_THUNDER_SHARE = 0.01  # thunder on at least 1% of the observed days (Plovdiv: 3-15%)
MIN_RAIN_SHARE = 0.10  # rain seen on at least 10% of the observed days (Plovdiv: 25-45%)


class MissingDataError(RuntimeError):
    """A source the table needs has not been downloaded yet."""


@dataclass
class Tables:
    hourly: pd.DataFrame
    daily: pd.DataFrame
    info: dict[str, Any] = field(default_factory=dict)


def local_dates(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """The local calendar date of each hour."""
    return pd.DatetimeIndex(index.tz_localize(None).normalize(), name="date")


def hours_in_day(days: pd.DatetimeIndex, tz: str) -> pd.Series:
    """Number of hours in each local calendar date: 24, or 23 and 25 on the days the clocks change.

    Counted from a complete run of UTC hours, which also handles clock changes at midnight (Bulgaria, 1979).
    """
    days = pd.DatetimeIndex(days)
    if days.empty:
        return pd.Series(dtype="int64", index=days)
    start = pd.Timestamp(days.min(), tz="UTC") - pd.Timedelta(days=1)
    end = pd.Timestamp(days.max(), tz="UTC") + pd.Timedelta(days=2)
    utc = pd.date_range(start, end, freq="h", inclusive="left")
    counts = pd.Series(1, index=utc).groupby(local_dates(utc.tz_convert(tz))).size()
    return counts.reindex(days).astype("int64")


def complete_days(hourly: pd.Series) -> pd.Series:
    """True for the local dates on which every hour has a value."""
    day = local_dates(hourly.index)
    counts = hourly.groupby(day).count()
    return counts == hours_in_day(counts.index, str(hourly.index.tz))


def daily_sum(hourly: pd.Series) -> pd.Series:
    """Sum over each local day; missing for days without all their hours (23 or 25 on clock changes)."""
    day = local_dates(hourly.index)
    return hourly.groupby(day).sum(min_count=1).where(complete_days(hourly))


def wet_day_thresholds(model_daily: pd.Series, station_daily: pd.Series, wet_mm: float = 1.0) -> pd.Series:
    """Per month, the model's daily amount that is reached as often as the station reached wet_mm.

    Both series are daily precipitation in mm; only the days both have count.
    """
    joined = pd.concat([station_daily.rename("station"), model_daily.rename("model")], axis=1, sort=True).dropna()
    if joined.empty:
        raise ValueError("no days with both model and station precipitation to calibrate on")
    out = {}
    for month, group in joined.groupby(joined.index.month):
        share = (group["station"] >= wet_mm).mean()
        out[int(month)] = float(group["model"].quantile(1 - share)) if share > 0 else float("inf")
    return pd.Series(out, name="wet_mm").rename_axis("month").round(2)


def observed_years(flags: pd.Series, min_share: float, min_days: int = MIN_YEAR_DAYS) -> set[int]:
    """Years in which a source really reports a phenomenon: enough days, and it is seen on enough of them.

    The airport's reports carry no weather codes before 2003, and neither the airport nor NOAA reports
    thunder in 2015-2018, although the reports themselves exist. A year in which thunder or rain is
    (almost) never seen is a year without those reports, not a dry year.
    """
    known = flags.dropna().astype(bool)
    by_year = known.groupby(known.index.year).agg(["size", "mean"])
    ok = (by_year["size"] >= min_days) & (by_year["mean"] >= min_share)
    return {int(y) for y in by_year.index[ok]}


def airport_days(airport: pd.DataFrame, min_hours: int = AIRPORT_DAY_HOURS) -> pd.DataFrame:
    """rain_seen and thunder per local date, for days with reports in at least min_hours hours."""
    reported = airport[airport["reports"] > 0]
    day = local_dates(reported.index)
    hours = reported["thunder"].groupby(day).size()
    seen = reported[["rain_seen", "thunder"]].groupby(day).any().astype("boolean")
    return seen[hours.reindex(seen.index) >= min_hours]


def airport_hours(airport: pd.DataFrame, index: pd.DatetimeIndex) -> pd.DataFrame:
    """rain_seen and thunder on the table's hours, only in the years the airport reports them."""
    reported = airport[airport["reports"] > 0][["rain_seen", "thunder"]].astype("boolean")
    days = airport_days(airport)
    for column, share in (("rain_seen", MIN_RAIN_SHARE), ("thunder", MIN_THUNDER_SHARE)):
        years = observed_years(days[column], share)
        reported[column] = reported[column].where(reported.index.year.isin(years))
    return reported.reindex(index)


def thunder_days(airport: pd.DataFrame, gsod: pd.DataFrame, priority: list[str]) -> pd.DataFrame:
    """Thunder per local date; each day from the first source in priority order that reports thunder that year."""
    candidates = {}
    if "airport" in priority and not airport.empty:
        candidates["airport"] = airport_days(airport)["thunder"]
    if "gsod" in priority and not gsod.empty:
        candidates["gsod"] = gsod["thunder"].astype("boolean")
    parts = []
    covered = pd.DatetimeIndex([], name="date")
    for name in priority:
        if name not in candidates:
            continue
        values = candidates[name].dropna()
        values = values[values.index.year.isin(observed_years(values, MIN_THUNDER_SHARE))]
        values = values.loc[values.index.difference(covered)]
        parts.append(pd.DataFrame({"thunder": values, "thunder_source": pd.Series(name, index=values.index)}))
        covered = covered.union(values.index)
    if not parts:
        return pd.DataFrame({"thunder": pd.Series(dtype="boolean"), "thunder_source": pd.Series(dtype="string")})
    out = pd.concat(parts).sort_index()
    return out.astype({"thunder": "boolean", "thunder_source": "string"})


def assemble(
    config: Config,
    era5: pd.DataFrame,
    station: pd.DataFrame,
    airport: pd.DataFrame,
    gsod: pd.DataFrame,
    today: date | None = None,
) -> Tables:
    """Build the hourly and daily tables from the parsed source tables."""
    today = today or date.today()
    location, data = config.location, config.data
    era5 = era5.sort_index()
    era5 = era5[era5.index < pd.Timestamp(today, tz=location.timezone)]
    era5 = era5[era5.index.year >= data.first_year]
    if era5.empty:
        raise MissingDataError("ERA5 has no hours for the configured years; run `weather-odds prefetch`")

    temperature = fill_temperature(station["temperature"], era5["temperature"]).reindex(era5.index)
    hourly = pd.concat([temperature, era5[["precipitation", "wind_gust"]], airport_hours(airport, era5.index)], axis=1)
    hourly["daylight"] = daylight(hourly.index, location.latitude, location.longitude)
    hourly.index.name = "time"

    day = local_dates(hourly.index)
    complete = complete_days(hourly["temperature"])
    daily = pd.DataFrame(
        {
            "tmax": hourly["temperature"].groupby(day).max().where(complete),
            "tmin": hourly["temperature"].groupby(day).min().where(complete),
            "station_hours": (hourly["temperature_source"] == "station").groupby(day).sum().astype("int64"),
            "precipitation": daily_sum(hourly["precipitation"]),
            "wind_gust_max": hourly["wind_gust"].groupby(day).max().where(complete_days(hourly["wind_gust"])),
        }
    )
    first, last = data.rain_calibration_years
    calibration = gsod["precipitation"].loc[f"{first}" : f"{last}"].dropna()
    thresholds = wet_day_thresholds(daily["precipitation"], calibration)
    limit = thresholds.reindex(daily.index.month).to_numpy()
    daily["wet"] = (daily["precipitation"] >= limit).astype("boolean").where(daily["precipitation"].notna())
    daily = daily.join(thunder_days(airport, gsod, list(data.thunder)))
    daily = daily.join(sun_times(daily.index, location.latitude, location.longitude, location.timezone))
    daily.index.name = "date"

    info = {
        "built": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
        "hours": [f"{hourly.index.min():%d.%m.%Y %H:%M}", f"{hourly.index.max():%d.%m.%Y %H:%M}"],
        "temperature_sources": hourly["temperature_source"].value_counts(dropna=False).to_dict(),
        "wet_day_thresholds_mm": {int(k): v for k, v in thresholds.items()},
        "rain_calibration_days": int(len(calibration)),
        "thunder_sources": daily["thunder_source"].value_counts().to_dict(),
    }
    info["temperature_sources"] = {str(k): int(v) for k, v in info["temperature_sources"].items()}
    return Tables(hourly=hourly, daily=daily, info=_plain(info))


def build(config: Config, today: date | None = None, log=print) -> Tables:
    """Build the tables from the cached sources and save them in the cache."""
    cache = Cache(config.data.cache_dir, config.location.slug)
    sources = {}
    for name in ("era5", "meteostat", "airport", "gsod"):
        table = cache.load_table(name)
        if table is None:
            raise MissingDataError(f"{name} has not been downloaded yet; run `weather-odds prefetch`")
        sources[name] = table
    tables = assemble(config, sources["era5"], sources["meteostat"], sources["airport"], sources["gsod"], today)
    save(cache, tables)
    info = tables.info
    log(f"hourly table: {len(tables.hourly)} hours, {info['hours'][0]} to {info['hours'][1]}")
    log("temperature: " + ", ".join(f"{k} {v}" for k, v in info["temperature_sources"].items()))
    log("wet-day thresholds (mm): " + " ".join(f"{v:g}" for v in info["wet_day_thresholds_mm"].values()))
    return tables


def save(cache: Cache, tables: Tables) -> None:
    cache.save_table("hourly", tables.hourly)
    cache.save_table("daily", tables.daily)
    path = cache.table_path("build").with_suffix(".json")
    path.write_text(json.dumps(tables.info, indent=1), encoding="utf-8")


def load(config: Config) -> Tables | None:
    """The tables saved by the last build, or None."""
    cache = Cache(config.data.cache_dir, config.location.slug)
    hourly, daily = cache.load_table("hourly"), cache.load_table("daily")
    if hourly is None or daily is None:
        return None
    path = cache.table_path("build").with_suffix(".json")
    info = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return Tables(hourly=hourly, daily=daily, info=info)


def _plain(value: Any) -> Any:
    """JSON-ready copy: numpy numbers become Python numbers."""
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value
