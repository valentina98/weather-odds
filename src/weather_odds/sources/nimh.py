"""NIMH (Bulgaria) open data: daily precipitation at the station, 2022 onwards (D38).

One file per month lists every station; each row holds the station id, its name
and one cell per day in mm. A blank cell is read as no precipitation: the files
are unverified operational data, so a blank could also hide a missing report.
A station without a row in a month has no data for that month.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from weather_odds.config import Location
from weather_odds.download import Downloader
from weather_odds.sources.base import Source, empty

INDEX = "https://info.meteo.bg/openData/rain/"
FILE = "https://info.meteo.bg/openData/static/csvs/{name}"
COLUMNS = {"precipitation": "float64"}
PARALLEL = 4  # files fetched at the same time; each takes about 2 s


def fetch(dl: Downloader, raw: Path, location: Location, years: range, today: date, refresh: bool) -> int:
    response = dl.get(INDEX)
    response.raise_for_status()
    names = sorted(set(re.findall(r"mosv_prec_(\d{6})\.csv", response.text)))
    previous = today.replace(day=1) - timedelta(days=1)
    recent = {f"{today:%Y%m}", f"{previous:%Y%m}"}  # files that may still change

    def one(month: str) -> bool:
        name = f"mosv_prec_{month}.csv"
        return dl.fetch(FILE.format(name=name), raw / name, refresh=refresh or month in recent, check=_is_table)

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        return sum(pool.map(one, [m for m in names if int(m[:4]) in years]))


def parse(raw: Path, location: Location, today: date) -> pd.DataFrame:
    rows = []
    for path in sorted(raw.glob("mosv_prec_*.csv")):
        month = pd.Period(path.stem[-6:], freq="M")
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            cells = [c.strip() for c in line.split(",")]
            if cells[0] != location.nimh_station:
                continue
            for day, cell in enumerate(cells[2 : 2 + month.days_in_month], start=1):
                when = date(month.year, month.month, day)
                if when >= today:
                    break
                amount = _amount(cell)
                if amount is not None:
                    rows.append((when, amount))
    if not rows:
        return empty("daily", COLUMNS, location.timezone)
    out = pd.DataFrame(rows, columns=["date", "precipitation"])
    out.index = pd.DatetimeIndex(out.pop("date"), name="date")
    return out[~out.index.duplicated(keep="last")].sort_index()


def _amount(cell: str) -> float | None:
    """mm in a cell: blank is 0, "2." is 2.0, anything unreadable is missing."""
    try:
        return float(cell.rstrip(".") or 0)
    except ValueError:
        return None


def _is_table(content: bytes) -> bool:
    return content.count(b",") > 30


SOURCE = Source(
    name="nimh",
    kind="daily",
    columns=tuple(COLUMNS),
    attribution="NIMH Bulgaria open data (info.meteo.bg/openData)",
    fetch=fetch,
    parse=parse,
)
