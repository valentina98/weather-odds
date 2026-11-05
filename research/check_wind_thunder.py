"""Wind and thunder reports at Plovdiv, for the milestone 3 gap plan (docs/research/table-checks.md).

1. ERA5's 10 m wind against the station's measured mean wind (Meteostat, NOAA ISD), 2000-2025.
2. ERA5's gusts against the highest wind the airport reports in each hour (mean wind, or the gust
   where one is reported), 2019-2025.
3. Thunder in the airport's reports by year: thunder at the airport (TS) and in its vicinity (VCTS).

Needs `uv run weather-odds prefetch` first (the station, airport and ERA5 caches). Downloads ERA5's
wind components for 2000-2025 from the Open-Meteo bucket and the airport's wind reports for
2019-2025 from the Iowa Environmental Mesonet into .cache/plovdiv/research/ (about a minute).
Run from the repository root: uv run python research/check_wind_thunder.py
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from weather_odds.config import Location
from weather_odds.sources import era5 as era5_source

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "plovdiv"
OUT = CACHE / "research"
MEASURED = ["isd_lite", "metar", "synop", "national"]
KNOT = 1.852  # km/h
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"


def era5_wind(years: range) -> pd.Series:
    path = OUT / "era5_wind.parquet"
    if path.exists():
        return pd.read_parquet(path)["wind"]
    location = Location()
    bucket = era5_source.open_bucket()
    hsurf = bucket.reader(f"{era5_source.MODEL}/static/HSURF.om")
    iy, ix = era5_source.grid_cell(hsurf.shape, location.latitude, location.longitude)
    cell = (slice(iy, iy + 1), slice(ix, ix + 1))
    whole = bucket.years("wind_u_component_10m")

    def one(job):
        variable, year = job
        return variable, era5_source._read_year(bucket, variable, year, cell, year in whole)

    jobs = [(v, y) for v in ("wind_u_component_10m", "wind_v_component_10m") for y in years]
    with ThreadPoolExecutor(8) as pool:
        parts = list(pool.map(one, jobs))
    u = pd.concat([s for v, s in parts if v.startswith("wind_u")]).sort_index()
    v = pd.concat([s for v, s in parts if v.startswith("wind_v")]).sort_index()
    wind = (np.hypot(u, v) * 3.6).rename("wind")  # m/s to km/h
    OUT.mkdir(parents=True, exist_ok=True)
    wind.to_frame().to_parquet(path)
    return wind


def station_wind(years: range) -> pd.Series:
    columns = ["year", "month", "day", "hour", "wspd", "wspd_source"]
    files = [CACHE / "raw" / "meteostat" / f"{y}.csv.gz" for y in years]
    data = pd.concat([pd.read_csv(p, usecols=columns) for p in files if p.exists()], ignore_index=True)
    data = data[data["wspd_source"].isin(MEASURED)]
    utc = pd.to_datetime(data[["year", "month", "day", "hour"]], utc=True)
    wind = pd.Series(data["wspd"].to_numpy(dtype=float), index=utc)
    return wind[~wind.index.duplicated()]


def airport_wind(years: range) -> pd.DataFrame:
    frames = []
    for year in years:
        path = OUT / f"airport_wind_{year}.csv"
        if not path.exists():
            params = {"station": "LBPD", "data": ["sknt", "gust"], "year1": year, "month1": 1, "day1": 1,
                      "year2": year + 1, "month2": 1, "day2": 1, "tz": "Etc/UTC", "format": "onlycomma",
                      "missing": "empty", "trace": "empty"}
            r = requests.get(IEM, params=params, timeout=300, headers={"User-Agent": "weather-odds research"})
            r.raise_for_status()
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_bytes(r.content)
        frames.append(pd.read_csv(path, dtype=str))
    data = pd.concat(frames, ignore_index=True)
    hour = pd.to_datetime(data["valid"], utc=True).dt.floor("h")
    reports = pd.DataFrame({"wind": pd.to_numeric(data["sknt"], errors="coerce").to_numpy() * KNOT,
                            "gust": pd.to_numeric(data["gust"], errors="coerce").to_numpy() * KNOT}, index=hour.to_numpy())
    hourly = reports.groupby(level=0).max()
    hourly["peak"] = hourly[["wind", "gust"]].max(axis=1)
    return hourly


def thunder_reports() -> pd.DataFrame:
    rows = []
    for path in sorted((CACHE / "raw" / "airport").glob("*.csv")):
        year = int(path.stem)
        if year < 2011:
            continue
        data = pd.read_csv(path, dtype=str)
        codes = data["wxcodes"].fillna("")
        storm = codes.str.contains("TS")
        vicinity = codes.str.contains("VCTS")
        rows.append({"year": year, "thunder reports": int(storm.sum()), "of them in the vicinity (VCTS)": int(vicinity.sum()),
                     "days with thunder": data.loc[storm, "valid"].str[:10].nunique(),
                     "reports per thunder day": round(storm.sum() / max(data.loc[storm, "valid"].str[:10].nunique(), 1), 1)})
    return pd.DataFrame(rows).set_index("year")


def main() -> None:
    years = range(2000, 2026)
    joined = pd.concat([station_wind(years).rename("station"), era5_wind(years).rename("era5")], axis=1, sort=True).dropna()
    month = joined.index.tz_convert("Europe/Sofia").month
    by_month = joined.groupby(month).mean()
    print("1. Mean wind (km/h), measured at the station vs ERA5 10 m, 2000-2025, by month")
    print(by_month.round(1).T.to_string())
    print(f"   all: station {joined['station'].mean():.1f}, ERA5 {joined['era5'].mean():.1f}, "
          f"ratio {joined['era5'].mean() / joined['station'].mean():.2f}, correlation {joined.corr().iloc[0, 1]:.2f}")

    gusts = pd.read_parquet(CACHE / "tables" / "era5.parquet")["wind_gust"]
    gusts.index = gusts.index.tz_convert("UTC")
    airport = airport_wind(range(2019, 2026))
    both = pd.concat([airport, gusts.rename("era5_gust")], axis=1, sort=True).dropna(subset=["peak", "era5_gust"])
    print("\n2. Highest wind reported at the airport in the hour vs ERA5's gust, 2019-2025")
    print(f"   hours {len(both)}; reports with a gust group: {both['gust'].notna().mean():.1%}")
    for limit in (30, 40, 50, 60, 75):
        print(f"   hours >= {limit} km/h: airport {(both['peak'] >= limit).mean():.2%}, ERA5 {(both['era5_gust'] >= limit).mean():.2%}")

    print("\n3. Thunder in the airport's reports")
    print(thunder_reports().to_string())


if __name__ == "__main__":
    main()
