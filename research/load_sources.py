"""Turn the cached raw downloads into tidy pandas tables (phase-0 research).

Every daily loader returns a DataFrame indexed by local calendar date
(Europe/Sofia) with a subset of these columns:

    tmax, tmin   daily max / min air temperature, deg C
    prcp         daily precipitation, mm (NaN = not measured)
    wet          bool, precipitation >= WET_DAY_MM (NaN when prcp is NaN)
    rain_seen    bool, rain/drizzle/showers/thunder reported (observation flags)
    snow_mm      snowfall, mm water equivalent
    gust_max     maximum wind gust, km/h

Hourly loaders return a DataFrame indexed by local timestamp.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "plovdiv"
TZ = "Europe/Sofia"
WET_DAY_MM = 1.0
LAPSE_RATE = 0.0065  # K per metre, standard atmosphere
STATION_ELEV = 179
NIMH_STATION = "46011"


def _f_to_c(series: pd.Series) -> pd.Series:
    return (series - 32) * 5 / 9


def gsod() -> pd.DataFrame:
    """NOAA GSOD for WMO 15625. Precipitation amounts are only usable 1973-1999."""
    frames = [pd.read_csv(p, dtype=str) for p in sorted((CACHE / "gsod").glob("*.csv"))]
    raw = pd.concat(frames, ignore_index=True)
    out = pd.DataFrame(index=pd.to_datetime(raw["DATE"]))
    out["tmax"] = _f_to_c(raw["MAX"].astype(float).where(lambda s: s < 9000)).values
    out["tmin"] = _f_to_c(raw["MIN"].astype(float).where(lambda s: s < 9000)).values
    prcp = raw["PRCP"].astype(float)
    attr = raw["PRCP_ATTRIBUTES"].fillna("").str.strip()
    # 99.99 = missing; attribute "I" = station reported no precipitation data that day.
    valid = (prcp < 99) & (attr != "I") & (attr != "")
    out["prcp"] = (prcp * 25.4).where(valid).values
    frshtt = raw["FRSHTT"].fillna("").str.zfill(6)
    out["rain_seen"] = ((frshtt.str[1] == "1") | (frshtt.str[4] == "1")).values
    out["snow_seen"] = (frshtt.str[2] == "1").values
    out["wet"] = (out["prcp"] >= WET_DAY_MM).where(out["prcp"].notna())
    return out.sort_index()


def meteostat_daily() -> pd.DataFrame:
    frames = [pd.read_csv(p) for p in sorted((CACHE / "meteostat_daily").glob("*.csv.gz"))]
    raw = pd.concat(frames, ignore_index=True)
    out = pd.DataFrame(index=pd.to_datetime(raw[["year", "month", "day"]]))
    out["tmax"] = raw["tmax"].values
    out["tmin"] = raw["tmin"].values
    # Meteostat's precipitation for this station is model output (dwd_mosmix), not measured.
    return out.sort_index()


def nimh() -> pd.DataFrame:
    """NIMH open data: daily precipitation at station 46011 (Plovdiv), 2022 onwards.

    A blank cell is read as "no precipitation". The files are unverified
    operational data, so blanks could also hide missing reports.
    """
    rows = []
    for path in sorted((CACHE / "nimh_prec").glob("mosv_prec_*.csv")):
        month = pd.Period(path.stem[-6:], freq="M")
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            cells = [c.strip() for c in line.split(",")]
            if cells and cells[0] == NIMH_STATION:
                for day, value in enumerate(cells[2:], start=1):
                    if day > month.days_in_month:
                        break
                    when = pd.Timestamp(month.year, month.month, day)
                    if when.normalize() >= pd.Timestamp.today().normalize():
                        break
                    rows.append((when, float(value.rstrip(".") or 0) if value != "" else 0.0))
    out = pd.DataFrame(rows, columns=["date", "prcp"]).set_index("date")
    out["wet"] = out["prcp"] >= WET_DAY_MM
    return out


def nasa_power() -> pd.DataFrame:
    data = json.loads((CACHE / "nasa_power" / "daily.json").read_text())["properties"]["parameter"]
    out = pd.DataFrame(data)
    out.index = pd.to_datetime(out.index, format="%Y%m%d")
    out = out.replace(-999.0, np.nan).rename(
        columns={"T2M_MAX": "tmax", "T2M_MIN": "tmin", "PRECTOTCORR": "prcp", "WS10M_MAX": "wind_max"}
    )
    out["wet"] = (out["prcp"] >= WET_DAY_MM).where(out["prcp"].notna())
    return out[["tmax", "tmin", "prcp", "wet", "wind_max"]]


def metar_hourly() -> pd.DataFrame:
    """Airport reports (LBPD). One row per local hour with rain/thunder/snow seen."""
    frames = [pd.read_csv(p, dtype=str) for p in sorted((CACHE / "iem_metar").glob("*.csv"))]
    raw = pd.concat(frames, ignore_index=True)
    # Floor in UTC first: flooring local times fails on DST transitions.
    hour = pd.to_datetime(raw["valid"], utc=True).dt.floor("h").dt.tz_convert(TZ)
    wx = raw["wxcodes"].fillna("")
    obs = pd.DataFrame({
        "hour": hour,
        "rain": wx.str.contains(r"RA|DZ|TS|GR|GS"),
        "thunder": wx.str.contains("TS"),
        "snow": wx.str.contains(r"SN|SG|PL"),
        "tmp": _f_to_c(pd.to_numeric(raw["tmpf"], errors="coerce")),
    })
    hourly = obs.groupby("hour").agg(
        rain=("rain", "any"), thunder=("thunder", "any"), snow=("snow", "any"), tmp=("tmp", "mean"), n=("rain", "size")
    )
    return hourly


def metar_daily() -> pd.DataFrame:
    """Days with at least 16 reported hours; rain_seen = any rain/thunder report."""
    hourly = metar_hourly()
    day = hourly.index.tz_localize(None).normalize()
    daily = hourly.groupby(day).agg(rain_seen=("rain", "any"), hours=("n", "size"), tmax=("tmp", "max"))
    return daily[daily["hours"] >= 16]


def era5_hourly(model: str = "copernicus_era5") -> pd.DataFrame:
    """ERA5 point series from the AWS cache, local time, temperature height-corrected."""
    meta = json.loads((CACHE / "aws" / f"{model}_meta.json").read_text())
    columns = {}
    for path in sorted((CACHE / "aws").glob(f"{model}_*.csv.gz")):
        var = path.name[len(model) + 1: -len(".csv.gz")]
        with gzip.open(path, "rt") as fh:
            s = pd.read_csv(fh, index_col=0, parse_dates=True).iloc[:, 0]
        columns[var] = s
    out = pd.DataFrame(columns)
    out.index = out.index.tz_convert(TZ)
    if "wind_gusts_10m" in out:
        out["wind_gusts_10m"] *= 3.6  # the .om files store m/s
    if "temperature_2m" in out:
        out["temperature_2m"] += (meta["grid_elevation_m"] - STATION_ELEV) * LAPSE_RATE
    return out


def era5_daily() -> pd.DataFrame:
    """Daily aggregates from hourly ERA5.

    tmax/tmin come from ERA5 (0.25 deg). ERA5-Land (0.1 deg) is kept as
    tmax_land/tmin_land for comparison: at Plovdiv it runs 2-3 C too cool in
    summer even after height correction, so it is not used as the default.
    """
    era5 = era5_hourly("copernicus_era5")
    day = era5.index.tz_localize(None).normalize()
    agg = {"precipitation": "sum", "snowfall_water_equivalent": "sum", "wind_gusts_10m": "max"}
    out = era5.groupby(day).agg({k: v for k, v in agg.items() if k in era5})
    out = out.rename(columns={"precipitation": "prcp", "snowfall_water_equivalent": "snow_mm", "wind_gusts_10m": "gust_max"})
    out["wet_hours"] = (era5["precipitation"] >= 0.1).groupby(day).sum()
    out["tmax"] = era5["temperature_2m"].groupby(day).max()
    out["tmin"] = era5["temperature_2m"].groupby(day).min()
    if (CACHE / "aws" / "copernicus_era5_land_temperature_2m.csv.gz").exists():
        land = era5_hourly("copernicus_era5_land")["temperature_2m"]
        lday = land.index.tz_localize(None).normalize()
        out["tmax_land"] = land.groupby(lday).max()
        out["tmin_land"] = land.groupby(lday).min()
    out["wet"] = out["prcp"] >= WET_DAY_MM
    # Drop partial first/last days created by the UTC -> local shift.
    counts = era5["precipitation"].groupby(day).size()
    return out[counts.reindex(out.index) >= 23]


def grid_daily(model: str) -> pd.DataFrame:
    """Daily tmax/tmin, and rain and gusts where the model has them, from any cached gridded series."""
    hourly = era5_hourly(model)
    day = hourly.index.tz_localize(None).normalize()
    temp = hourly["temperature_2m"].groupby(day)
    out = pd.DataFrame({"tmax": temp.max(), "tmin": temp.min()})
    if "precipitation" in hourly:
        out["prcp"] = hourly["precipitation"].groupby(day).sum()
        out["wet"] = out["prcp"] >= WET_DAY_MM
    if "wind_gusts_10m" in hourly:
        out["gust_max"] = hourly["wind_gusts_10m"].groupby(day).max()
    return out[temp.count() >= 23]
