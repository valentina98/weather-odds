"""What every data adapter provides, and helpers they share."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import pandas as pd

from weather_odds.config import Location
from weather_odds.download import Downloader

# fetch(downloader, raw folder, location, years, today, refresh) -> files written
Fetch = Callable[[Downloader, Path, Location, range, date, bool], int]
# parse(raw folder, location, today) -> tidy table
Parse = Callable[[Path, Location, date], pd.DataFrame]


@dataclass(frozen=True)
class Source:
    name: str
    kind: Literal["hourly", "daily"]
    columns: tuple[str, ...]
    attribution: str
    fetch: Fetch
    parse: Parse


def f_to_c(values: pd.Series) -> pd.Series:
    return (values - 32) * 5 / 9


def hourly_table(utc: pd.Series, columns: dict[str, pd.Series], tz: str) -> pd.DataFrame:
    """A table indexed by the start of each hour in local time, from UTC timestamps.

    Hours are floored in UTC first: flooring local times fails on the DST changes.
    """
    index = pd.DatetimeIndex(pd.to_datetime(utc, utc=True)).floor("h").tz_convert(tz)
    out = pd.DataFrame({name: values.to_numpy() for name, values in columns.items()}, index=index)
    out.index.name = "time"
    return out


def daily_index(dates: pd.Series) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(dates), name="date").normalize()


def empty(kind: Literal["hourly", "daily"], columns: dict[str, str], tz: str) -> pd.DataFrame:
    """A table with no rows, for a source with nothing downloaded."""
    index = pd.DatetimeIndex([], tz=tz if kind == "hourly" else None, name="time" if kind == "hourly" else "date")
    return pd.DataFrame({name: pd.Series(dtype=dtype) for name, dtype in columns.items()}, index=index)
