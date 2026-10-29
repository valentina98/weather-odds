"""Download raw weather data for one location into .cache/ (phase-0 research).

This is research tooling, not the application. It fetches every no-key source
we evaluated for Plovdiv so the analysis script can compare them. Downloads are
cached; re-running only fetches what is missing.

Usage:
    python research/fetch_sources.py [--sources gsod,meteostat,...]
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "plovdiv"

# Plovdiv synoptic station WMO 15625, using the coordinates Meteostat lists for it.
# Other listings place the station at the airport (42.07 N, 24.87 E); either way
# the grid sources use this same point so station and grid compare like for like.
LAT, LON, ELEV = 42.1333, 24.75, 179
WMO = "15625"
ICAO = "LBPD"
NIMH_STATION = "46011"  # "Plovdiv" in the NIMH daily precipitation files

FIRST_YEAR, LAST_YEAR = 1940, 2025
TODAY = date.today()

session = requests.Session()
session.headers["User-Agent"] = "weather-odds research (github.com/valentina98/weather-odds)"


def get(url: str, params: dict | None = None, timeout: int = 120) -> requests.Response:
    for attempt in range(5):
        try:
            r = session.get(url, params=params, timeout=timeout)
        except requests.ConnectionError:
            if attempt == 4:
                raise
            time.sleep(5 * 2**attempt)
            continue
        if r.status_code in (429, 502, 503, 504) and attempt < 4:
            time.sleep(5 * 2**attempt)
            continue
        return r
    return r


def save(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def fetch_gsod() -> None:
    """NOAA Global Summary of the Day, one CSV per year."""
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        out = CACHE / "gsod" / f"{year}.csv"
        if out.exists():
            continue
        r = get(f"https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{year}/{WMO}099999.csv")
        if r.status_code == 200:
            save(out, r.content)


def fetch_meteostat() -> None:
    """Meteostat bulk data (daily and hourly), one gzip CSV per year."""
    for kind in ("daily", "hourly"):
        for year in range(FIRST_YEAR, TODAY.year + 1):
            out = CACHE / f"meteostat_{kind}" / f"{year}.csv.gz"
            if out.exists():
                continue
            r = get(f"https://data.meteostat.net/{kind}/{year}/{WMO}.csv.gz")
            if r.status_code == 200:
                save(out, r.content)


def fetch_iem_metar() -> None:
    """Airport reports (METAR) for LBPD from the Iowa Environmental Mesonet."""
    for year in range(1990, TODAY.year + 1):
        out = CACHE / "iem_metar" / f"{year}.csv"
        if out.exists():
            continue
        params = {
            "station": ICAO, "data": "tmpf,sknt,gust,wxcodes,skyc1",
            "year1": year, "month1": 1, "day1": 1,
            "year2": year + 1, "month2": 1, "day2": 1,
            "tz": "Etc/UTC", "format": "onlycomma", "missing": "empty", "trace": "empty",
        }
        r = get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", params, timeout=300)
        if r.status_code == 200 and r.text.count("\n") > 1:
            save(out, r.content)
        time.sleep(1)


def fetch_nimh() -> None:
    """NIMH (Bulgaria) daily precipitation, one CSV per month for 166 stations."""
    index = get("https://info.meteo.bg/openData/rain/").text
    for name in sorted(set(re.findall(r"mosv_prec_\d{6}\.csv", index))):
        out = CACHE / "nimh_prec" / name
        # The current month's file grows daily, so always refresh it.
        if out.exists() and name != f"mosv_prec_{TODAY:%Y%m}.csv":
            continue
        r = get(f"https://info.meteo.bg/openData/static/csvs/{name}")
        if r.status_code == 200:
            save(out, r.content)


def fetch_nasa_power() -> None:
    out = CACHE / "nasa_power" / "daily.json"
    if out.exists():
        return
    params = {
        "parameters": "T2M_MAX,T2M_MIN,T2M,PRECTOTCORR,WS10M_MAX",
        "community": "AG", "latitude": LAT, "longitude": LON,
        "start": "19810101", "end": f"{LAST_YEAR}1231", "format": "JSON",
    }
    r = get("https://power.larc.nasa.gov/api/temporal/daily/point", params, timeout=300)
    r.raise_for_status()
    save(out, r.content)


OPEN_METEO_DAILY = (
    "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,"
    "rain_sum,snowfall_sum,precipitation_hours,wind_speed_10m_max,wind_gusts_10m_max,sunshine_duration"
)
OPEN_METEO_HOURLY = "temperature_2m,precipitation,wind_gusts_10m,cloud_cover"

# (name, model, start, end, kind). CERRA ends in mid-2021.
OPEN_METEO_REQUESTS = [
    ("era5_seamless_daily", "era5_seamless", "1960-01-01", f"{LAST_YEAR}-12-31", "daily"),
    ("cerra_daily", "cerra", "1985-01-01", "2021-06-30", "daily"),
    ("era5_seamless_hourly", "era5_seamless", "1991-01-01", f"{LAST_YEAR}-12-31", "hourly"),
    ("cerra_hourly", "cerra", "1991-01-01", "2021-06-30", "hourly"),
]


def fetch_open_meteo() -> None:
    """Open-Meteo historical API (free tier; often rate-limited from cloud sessions)."""
    for name, model, start, end, kind in OPEN_METEO_REQUESTS:
        out = CACHE / "open_meteo" / f"{name}.json"
        if out.exists():
            continue
        params = {
            "latitude": LAT, "longitude": LON, "elevation": ELEV,
            "start_date": start, "end_date": end, "models": model,
            "timezone": "Europe/Sofia", kind: OPEN_METEO_DAILY if kind == "daily" else OPEN_METEO_HOURLY,
        }
        r = get("https://archive-api.open-meteo.com/v1/archive", params, timeout=600)
        if r.status_code != 200:
            print(f"open-meteo {name}: HTTP {r.status_code} {r.text[:200]}")
            continue
        try:  # a server-side timeout can arrive as HTTP 200 with a plain-text error
            r.json()
        except ValueError:
            print(f"open-meteo {name}: not JSON: {r.text[:100]!r}")
            continue
        save(out, r.content)
        time.sleep(5)


AWS_VARIABLES = {
    "copernicus_era5": [
        "temperature_2m", "precipitation", "snowfall_water_equivalent", "wind_gusts_10m", "cloud_cover",
    ],
    "copernicus_era5_land": ["temperature_2m"],
    # ECMWF IFS HRES (~9 km), archived by Open-Meteo from 2017 on a reduced Gaussian grid.
    "ecmwf_ifs": ["temperature_2m", "precipitation", "wind_gusts_10m"],
}
AWS_FIRST_YEAR = {"ecmwf_ifs": 2017}  # default 1960
GAUSSIAN_MODELS = {"ecmwf_ifs"}
O1280 = 1280  # latitude rows per hemisphere of ECMWF's O1280 grid
CHUNK_HOURS = 504  # from data/<model>/static/meta.json


def _grid_index(shape: tuple[int, ...]) -> tuple[int, int]:
    """Nearest grid cell on a regular global lat/lon grid starting at -90/-180."""
    ny, nx = shape[0], shape[1]
    iy = round((LAT + 90) / 180 * (ny - 1))
    ix = round((LON + 180) / 360 * nx) % nx
    return iy, ix


def _gaussian_index() -> tuple[int, float, float]:
    """Nearest point of the O1280 reduced Gaussian grid, stored as one flat axis.

    Rows run north to south; row y (from the nearer pole) has 4y + 20 points
    starting at 0 E. Returns (flat index, latitude, longitude).
    """
    import numpy as np

    nodes, _ = np.polynomial.legendre.leggauss(2 * O1280)
    lats = np.degrees(np.arcsin(np.sort(nodes)[::-1]))
    counts = [4 * min(y, 2 * O1280 - 1 - y) + 20 for y in range(2 * O1280)]
    y = int(np.argmin(np.abs(lats - LAT)))
    x = round((LON % 360) / (360 / counts[y])) % counts[y]
    return sum(counts[:y]) + x, float(lats[y]), x * 360 / counts[y]


def fetch_aws() -> None:
    """ERA5, ERA5-Land and ECMWF IFS hourly point series from Open-Meteo's AWS open-data bucket.

    No key and no rate limit. Older years are stored as one file per year;
    later data are 21-day chunk files named by hours since 1970 // 504.
    """
    import numpy as np
    import pandas as pd
    import s3fs
    from omfiles import OmFileReader

    fs = s3fs.S3FileSystem(anon=True, client_kwargs={"region_name": "us-west-2"})

    def reader(path: str):
        return OmFileReader.from_fsspec(fs, f"openmeteo/data/{path}")

    for model, variables in AWS_VARIABLES.items():
        hsurf = reader(f"{model}/static/HSURF.om")
        if model in GAUSSIAN_MODELS:
            i, grid_lat, grid_lon = _gaussian_index()
            cell = (slice(0, 1), slice(i, i + 1))
        else:
            iy, ix = _grid_index(hsurf.shape)
            grid_lat, grid_lon = -90 + iy * 180 / (hsurf.shape[0] - 1), -180 + ix * 360 / hsurf.shape[1]
            cell = (slice(iy, iy + 1), slice(ix, ix + 1))
        meta = {"grid_lat": grid_lat, "grid_lon": grid_lon, "grid_elevation_m": float(hsurf[cell].ravel()[0])}
        save(CACHE / "aws" / f"{model}_meta.json", json.dumps(meta).encode())

        years = {int(p.rsplit("_", 1)[1][:4]) for p in fs.glob(f"openmeteo/data/{model}/temperature_2m/year_*.om")}
        for var in variables:
            out = CACHE / "aws" / f"{model}_{var}.csv.gz"
            if out.exists():
                continue
            parts = []
            for year in range(AWS_FIRST_YEAR.get(model, 1960), LAST_YEAR + 1):
                if year in years:
                    r = reader(f"{model}/{var}/year_{year}.om")
                    values = r[cell + (slice(None),)].ravel()
                    index = pd.date_range(f"{year}-01-01", periods=len(values), freq="h", tz="UTC")
                    parts.append(pd.Series(values, index=index))
                    continue
                start = int(pd.Timestamp(f"{year}-01-01", tz="UTC").timestamp() // 3600)
                end = int(pd.Timestamp(f"{year + 1}-01-01", tz="UTC").timestamp() // 3600)
                for chunk in range(start // CHUNK_HOURS, (end - 1) // CHUNK_HOURS + 1):
                    path = f"{model}/{var}/chunk_{chunk}.om"
                    if not fs.exists(f"openmeteo/data/{path}"):
                        continue
                    values = reader(path)[cell + (slice(None),)].ravel()
                    index = pd.date_range(
                        pd.Timestamp(chunk * CHUNK_HOURS * 3600, unit="s", tz="UTC"),
                        periods=len(values), freq="h",
                    )
                    parts.append(pd.Series(values, index=index))
            series = pd.concat(parts)
            series = series[~series.index.duplicated(keep="first")].sort_index()
            series = series[series.index.year <= LAST_YEAR].astype(np.float32)
            series.rename(var).to_csv(out, index_label="time_utc", float_format="%.2f")
            print(f"aws {model} {var}: {len(series)} hours")


SOURCES = {
    "aws": fetch_aws,
    "open_meteo": fetch_open_meteo,
    "gsod": fetch_gsod,
    "meteostat": fetch_meteostat,
    "iem_metar": fetch_iem_metar,
    "nimh": fetch_nimh,
    "nasa_power": fetch_nasa_power,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default=",".join(SOURCES))
    args = parser.parse_args()
    for name in args.sources.split(","):
        t0 = time.time()
        SOURCES[name]()
        files = list((CACHE).glob(f"{name.split('_')[0]}*/*"))
        print(f"{name}: done in {time.time() - t0:.0f}s ({len(files)} cached files)")


if __name__ == "__main__":
    main()
