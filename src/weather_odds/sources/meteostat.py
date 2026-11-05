"""The station's hourly temperatures from Meteostat's bulk files (D34).

Meteostat merges several feeds per value and names the feed in `<column>_source`.
Only measured values are kept (NOAA ISD and airport reports); model values such
as `dwd_mosmix` are dropped. Before 1997 the station reported every 3 hours.
Times in the files are UTC.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from weather_odds.config import Location
from weather_odds.download import Downloader
from weather_odds.sources.base import Source, empty, hourly_table

URL = "https://data.meteostat.net/hourly/{year}/{station}.csv.gz"
MEASURED = {"isd_lite", "metar", "synop", "national"}
COLUMNS = {"temperature": "float64"}


def fetch(dl: Downloader, raw: Path, location: Location, years: range, today: date, refresh: bool) -> int:
    written = 0
    for year in years:
        url = URL.format(year=year, station=location.station)
        current = year >= today.year  # this year's file still grows
        written += dl.fetch(url, raw / f"{year}.csv.gz", refresh=refresh or current, check=_is_gzip)
    return written


def parse(raw: Path, location: Location, today: date) -> pd.DataFrame:
    files = sorted(raw.glob("*.csv.gz"))
    if not files:
        return empty("hourly", COLUMNS, location.timezone)
    columns = ["year", "month", "day", "hour", "temp", "temp_source"]
    data = pd.concat([pd.read_csv(p, usecols=columns) for p in files], ignore_index=True)
    utc = pd.to_datetime(data[["year", "month", "day", "hour"]], utc=True)
    temperature = data["temp"].astype(float).where(data["temp_source"].isin(MEASURED))
    out = hourly_table(utc, {"temperature": temperature}, location.timezone).dropna()
    return out[~out.index.duplicated(keep="last")].sort_index()


def _is_gzip(content: bytes) -> bool:
    return content[:2] == b"\x1f\x8b"


SOURCE = Source(
    name="meteostat",
    kind="hourly",
    columns=tuple(COLUMNS),
    attribution="Meteostat (meteostat.net), CC BY-NC 4.0; measurements from NOAA ISD and airport reports",
    fetch=fetch,
    parse=parse,
)
