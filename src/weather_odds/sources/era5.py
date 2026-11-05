"""ERA5 hourly point series from Open-Meteo's open-data bucket on AWS: rain, gusts and the temperature fill-in.

ERA5 (Copernicus, 0.25 degree) gives rain and wind gusts for every hour (D34),
and temperatures where the station has none. The bucket needs no key and has no
daily limit (D45). Only plain ERA5 (`copernicus_era5`) is read, never the
"ERA5 seamless" mix, whose temperatures are ERA5-Land (D35).

Older years are one file per year; recent data are 21-day chunk files named by
hours since 1970 // 504. Conversions to the tidy vocabulary:

- temperature: corrected from the grid cell's height to the station's with the
  standard lapse rate (0.65 deg C per 100 m);
- precipitation and wind gusts: Open-Meteo stamps them at the end of their hour,
  so they move one hour back to the hour's start; gusts from m/s to km/h.

A year still being filled is saved as `<year>.partial.csv.gz` and fetched again
on the next prefetch.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from weather_odds.config import Location
from weather_odds.download import Downloader
from weather_odds.sources.base import Source, empty

BUCKET = "openmeteo/data"
MODEL = "copernicus_era5"
VARIABLES = {"temperature_2m": "temperature", "precipitation": "precipitation", "wind_gusts_10m": "wind_gust"}
END_OF_HOUR = {"precipitation", "wind_gusts_10m"}
CHUNK_HOURS = 504
LAPSE_RATE = 0.0065  # deg C per metre
PARALLEL = 8
COLUMNS = {"temperature": "float64", "precipitation": "float64", "wind_gust": "float64"}


class Bucket:
    """The bucket, read anonymously through fsspec."""

    def __init__(self, fs: Any = None):
        if fs is None:
            import s3fs

            fs = s3fs.S3FileSystem(anon=True, client_kwargs={"region_name": "us-west-2"})
        self.fs = fs

    def reader(self, path: str) -> Any:
        from omfiles import OmFileReader

        return OmFileReader.from_fsspec(self.fs, f"{BUCKET}/{path}")

    def exists(self, path: str) -> bool:
        return self.fs.exists(f"{BUCKET}/{path}")

    def years(self, variable: str) -> set[int]:
        """Years stored as whole-year files."""
        return {int(p.rsplit("_", 1)[1][:4]) for p in self.fs.glob(f"{BUCKET}/{MODEL}/{variable}/year_*.om")}


def open_bucket() -> Bucket:
    return Bucket()


def grid_cell(shape: tuple[int, ...], latitude: float, longitude: float) -> tuple[int, int]:
    """Nearest cell of a regular global grid whose rows start at 90 S and columns at 180 W."""
    ny, nx = shape[0], shape[1]
    return round((latitude + 90) / 180 * (ny - 1)), round((longitude + 180) / 360 * nx) % nx


def fetch(dl: Downloader, raw: Path, location: Location, years: range, today: date, refresh: bool) -> int:
    bucket = open_bucket()
    hsurf = bucket.reader(f"{MODEL}/static/HSURF.om")
    iy, ix = grid_cell(hsurf.shape, location.latitude, location.longitude)
    cell = (slice(iy, iy + 1), slice(ix, ix + 1))
    meta = {
        "grid_latitude": -90 + iy * 180 / (hsurf.shape[0] - 1),
        "grid_longitude": -180 + ix * 360 / hsurf.shape[1],
        "grid_elevation_m": float(np.asarray(hsurf[cell]).ravel()[0]),
    }
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "meta.json").write_text(json.dumps(meta))
    whole_years = bucket.years("temperature_2m")

    def one(job: tuple[str, int]) -> bool:
        variable, year = job
        folder = raw / variable
        if not refresh and (folder / f"{year}.csv.gz").exists():
            return False
        series = _read_year(bucket, variable, year, cell, year in whole_years)
        partial = folder / f"{year}.partial.csv.gz"
        partial.unlink(missing_ok=True)
        if series.empty:
            return False
        hours = 366 * 24 if pd.Timestamp(year=year, month=1, day=1).is_leap_year else 365 * 24
        path = folder / f"{year}.csv.gz" if len(series) == hours else partial
        folder.mkdir(parents=True, exist_ok=True)
        series.rename("value").to_csv(path, index_label="time_utc", float_format="%.2f")
        return True

    jobs = [(variable, year) for variable in VARIABLES for year in years]
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        return sum(pool.map(one, jobs))


def _read_year(bucket: Bucket, variable: str, year: int, cell: tuple[slice, slice], whole: bool) -> pd.Series:
    """One year of hourly values at the cell, UTC, without the hours not yet filled."""
    start = pd.Timestamp(year=year, month=1, day=1, tz="UTC")
    end = pd.Timestamp(year=year + 1, month=1, day=1, tz="UTC")
    parts = []
    if whole:
        values = np.asarray(bucket.reader(f"{MODEL}/{variable}/year_{year}.om")[cell + (slice(None),)]).ravel()
        parts.append(pd.Series(values, index=pd.date_range(start, periods=len(values), freq="h")))
    else:
        first, last = int(start.timestamp() // 3600), int(end.timestamp() // 3600) - 1
        for chunk in range(first // CHUNK_HOURS, last // CHUNK_HOURS + 1):
            path = f"{MODEL}/{variable}/chunk_{chunk}.om"
            if not bucket.exists(path):
                continue
            values = np.asarray(bucket.reader(path)[cell + (slice(None),)]).ravel()
            chunk_start = pd.Timestamp(chunk * CHUNK_HOURS * 3600, unit="s", tz="UTC")
            parts.append(pd.Series(values, index=pd.date_range(chunk_start, periods=len(values), freq="h")))
    if not parts:
        return pd.Series(dtype="float64")
    series = pd.concat(parts).astype("float64")
    series = series[~series.index.duplicated(keep="first")].sort_index()
    return series[(series.index >= start) & (series.index < end)].dropna()


def parse(raw: Path, location: Location, today: date) -> pd.DataFrame:
    meta_path = raw / "meta.json"
    if not meta_path.exists():
        return empty("hourly", COLUMNS, location.timezone)
    meta = json.loads(meta_path.read_text())
    columns = {}
    for variable, name in VARIABLES.items():
        files = sorted((raw / variable).glob("*.csv.gz"))
        if not files:
            continue
        series = pd.concat([pd.read_csv(p, index_col=0).iloc[:, 0] for p in files])
        series.index = pd.DatetimeIndex(pd.to_datetime(series.index, utc=True))
        if variable in END_OF_HOUR:
            series.index = series.index - pd.Timedelta(hours=1)
        if variable == "temperature_2m":
            series = series + (meta["grid_elevation_m"] - location.elevation_m) * LAPSE_RATE
        if variable == "wind_gusts_10m":
            series = series * 3.6
        columns[name] = series[~series.index.duplicated(keep="last")]
    if not columns:
        return empty("hourly", COLUMNS, location.timezone)
    out = pd.DataFrame(columns).reindex(columns=list(COLUMNS)).astype(COLUMNS).sort_index()
    out.index = out.index.tz_convert(location.timezone)
    out.index.name = "time"
    return out


SOURCE = Source(
    name="era5",
    kind="hourly",
    columns=tuple(COLUMNS),
    attribution="Copernicus Climate Change Service ERA5 (CC BY 4.0), via Open-Meteo open data on AWS (CC BY 4.0)",
    fetch=fetch,
    parse=parse,
)
