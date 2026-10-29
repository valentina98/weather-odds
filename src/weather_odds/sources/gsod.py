"""NOAA Global Summary of the Day for the station: daily extremes, rain and weather flags.

Used to calibrate ERA5's wet days (D38) and for thunder days before the airport
reports (D37). Units in the files: deg F and inches; 9999.9 and 99.99 mean missing.
Precipitation counts only with a reporting flag other than "I" (no report that day);
for Plovdiv that leaves 1973-1999. FRSHTT holds six 0/1 flags: fog, rain, snow,
hail, thunder, tornado.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from weather_odds.config import Location
from weather_odds.download import Downloader
from weather_odds.sources.base import Source, daily_index, empty, f_to_c

URL = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{year}/{station}099999.csv"
COLUMNS = {
    "tmax": "float64",
    "tmin": "float64",
    "precipitation": "float64",
    "rain_seen": "boolean",
    "snow_seen": "boolean",
    "thunder": "boolean",
}


def fetch(dl: Downloader, raw: Path, location: Location, years: range, today: date, refresh: bool) -> int:
    written = 0
    for year in years:
        url = URL.format(year=year, station=location.station)
        written += dl.fetch(url, raw / f"{year}.csv", refresh=refresh or year >= today.year, check=_is_gsod)
    return written


def parse(raw: Path, location: Location, today: date) -> pd.DataFrame:
    files = sorted(raw.glob("*.csv"))
    if not files:
        return empty("daily", COLUMNS, location.timezone)
    data = pd.concat([pd.read_csv(p, dtype=str) for p in files], ignore_index=True)
    number = {c: pd.to_numeric(data[c], errors="coerce") for c in ("MAX", "MIN", "PRCP")}
    attribute = data["PRCP_ATTRIBUTES"].fillna("").str.strip()
    reported = (number["PRCP"] < 99) & ~attribute.isin(["", "I"])
    reported_flags = data["FRSHTT"].fillna("").str.strip()
    known = reported_flags.str.fullmatch(r"[01]{1,6}")
    flags = reported_flags.str.zfill(6)

    def flag(*positions: int) -> pd.Series:
        seen = pd.Series(False, index=data.index)
        for p in positions:
            seen |= flags.str[p] == "1"
        return seen.astype("boolean").where(known, pd.NA)

    out = pd.DataFrame(
        {
            "tmax": f_to_c(number["MAX"].where(number["MAX"] < 9000)).array,
            "tmin": f_to_c(number["MIN"].where(number["MIN"] < 9000)).array,
            "precipitation": (number["PRCP"] * 25.4).where(reported).array,
            "rain_seen": flag(1, 4).array,
            "snow_seen": flag(2).array,
            "thunder": flag(4).array,
        },
        index=daily_index(data["DATE"]),
    )
    return out[~out.index.duplicated(keep="last")].sort_index()


def _is_gsod(content: bytes) -> bool:
    return content.lstrip(b"\xef\xbb\xbf").startswith(b'"STATION"')


SOURCE = Source(
    name="gsod",
    kind="daily",
    columns=tuple(COLUMNS),
    attribution="NOAA National Centers for Environmental Information, Global Summary of the Day",
    fetch=fetch,
    parse=parse,
)
