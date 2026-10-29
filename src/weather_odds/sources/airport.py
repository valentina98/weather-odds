"""Airport reports (METAR) from the Iowa Environmental Mesonet: rain and thunder by hour (D37).

Each report's present-weather codes say whether rain, thunder or snow was seen.
A thunderstorm (TS) counts as rain seen. Reports come every 30 minutes; an hour
holds the reports from its start to its end. Hours without reports are absent,
which is not the same as dry. Times are requested in UTC.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from weather_odds.config import Location
from weather_odds.download import Downloader
from weather_odds.sources.base import Source, empty, hourly_table

URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
COLUMNS = {"rain_seen": "bool", "thunder": "bool", "snow_seen": "bool", "reports": "int64"}
PAUSE = 1.0  # seconds between requests; the Mesonet asks for gentle use


def fetch(dl: Downloader, raw: Path, location: Location, years: range, today: date, refresh: bool) -> int:
    written = 0
    for year in years:
        params = {
            "station": location.airport,
            "data": "wxcodes",
            "year1": year,
            "month1": 1,
            "day1": 1,
            "year2": year + 1,
            "month2": 1,
            "day2": 1,
            "tz": "Etc/UTC",
            "format": "onlycomma",
            "missing": "empty",
            "trace": "empty",
        }
        path = raw / f"{year}.csv"
        new = dl.fetch(URL, path, params, refresh=refresh or year >= today.year, timeout=300, check=_is_report)
        written += new
        if new:
            dl.wait(PAUSE)
    return written


def parse(raw: Path, location: Location, today: date) -> pd.DataFrame:
    files = sorted(raw.glob("*.csv"))
    data = pd.concat([pd.read_csv(p, dtype=str) for p in files], ignore_index=True) if files else None
    if data is None or data.empty:
        return empty("hourly", COLUMNS, location.timezone)
    codes = data["wxcodes"].fillna("")
    reports = hourly_table(
        data["valid"],
        {
            "rain_seen": codes.str.contains(r"RA|DZ|TS|GR|GS"),
            "thunder": codes.str.contains("TS"),
            "snow_seen": codes.str.contains(r"SN|SG|PL"),
            "reports": pd.Series(1, index=data.index),
        },
        location.timezone,
    )
    hourly = reports.groupby(level="time").agg(
        {"rain_seen": "any", "thunder": "any", "snow_seen": "any", "reports": "sum"}
    )
    return hourly.astype(COLUMNS).sort_index()


def _is_report(content: bytes) -> bool:
    return content.startswith(b"station,valid")


SOURCE = Source(
    name="airport",
    kind="hourly",
    columns=tuple(COLUMNS),
    attribution="Iowa Environmental Mesonet (mesonet.agron.iastate.edu), airport reports",
    fetch=fetch,
    parse=parse,
)
