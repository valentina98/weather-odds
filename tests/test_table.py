from datetime import date

import numpy as np
import pandas as pd
import pytest

from weather_odds.config import Config, Data
from weather_odds.table import (
    MissingDataError,
    airport_days,
    airport_hours,
    assemble,
    build,
    daily_sum,
    load,
    observed_years,
    thunder_days,
    wet_day_thresholds,
)

TZ = "Europe/Sofia"


def hours(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(pd.Timestamp(start, tz=TZ), pd.Timestamp(end, tz=TZ), freq="h", inclusive="left", name="time")


def dates(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="D", inclusive="left", name="date")


def test_daily_sum_needs_every_hour_of_the_local_day():
    index = hours("2020-03-28", "2020-03-31")  # 29 March has 23 hours
    rain = pd.Series(1.0, index=index)
    sums = daily_sum(rain)
    assert list(sums) == [24.0, 23.0, 24.0]
    assert np.isnan(daily_sum(rain.drop(index[5])).iloc[0])


def test_hours_in_day_with_clock_changes_at_midnight():
    from weather_odds.table import hours_in_day

    days = pd.DatetimeIndex(["1979-10-01", "2020-03-29", "2020-10-25", "2020-06-01"])
    assert list(hours_in_day(days, TZ)) == [25, 23, 25, 24]  # 1979: the clocks went back at midnight


def test_wet_day_thresholds_match_the_station_frequency():
    days = dates("2001-01-01", "2001-03-01")
    model = pd.Series(np.tile(np.arange(10, dtype=float), 6)[: len(days)], index=days)  # 0..9 mm
    station = pd.Series(np.where(model >= 7, 5.0, 0.0), index=days)  # wet when the model has 7 mm or more
    thresholds = wet_day_thresholds(model, station)
    assert list(thresholds.index) == [1, 2]
    for month, value in thresholds.items():
        in_month = model[model.index.month == month]
        assert (in_month >= value).mean() == pytest.approx((station[station.index.month == month] >= 1).mean())
    dry = wet_day_thresholds(model, station * 0)
    assert np.isinf(dry).all()
    with pytest.raises(ValueError):
        wet_day_thresholds(model, pd.Series(dtype=float))


def test_observed_years_need_enough_days_and_the_phenomenon():
    days = dates("2014-01-01", "2017-01-01")
    flags = pd.Series(False, index=days)
    flags[(days.year == 2014) & (days.month == 6)] = True  # 30 thunder days in 2014
    flags[(days.year == 2016) & (days.day == 1) & (days.month == 6)] = True  # 1 day in 2016
    assert observed_years(flags, 0.01) == {2014}
    assert observed_years(flags.loc["2014-06-01":"2014-06-20"], 0.01) == set()  # too few days


def airport_table(index: pd.DatetimeIndex, thunder_hours: list[pd.Timestamp]) -> pd.DataFrame:
    table = pd.DataFrame({"rain_seen": False, "thunder": False, "snow_seen": False, "reports": 2}, index=index).astype(
        {"rain_seen": bool, "thunder": bool, "snow_seen": bool, "reports": "int64"}
    )
    table.loc[thunder_hours, ["thunder", "rain_seen"]] = True
    return table


def test_airport_counts_only_in_years_with_thunder_reports():
    index = hours("2014-01-01", "2016-01-01")
    storms = [t for t in index if t.year == 2014 and t.month in (5, 6, 7) and t.hour == 16 and t.day % 3 == 0]
    airport = airport_table(index, storms)
    airport.loc[index[100:110], "reports"] = 0  # hours without reports
    hourly = airport_hours(airport, index)
    assert hourly.loc[storms[0], "thunder"]
    assert not hourly.loc[storms[0] + pd.Timedelta(hours=1), "thunder"]
    assert hourly.loc[index[105], "thunder"] is pd.NA
    assert hourly.loc["2015", "thunder"].isna().all()  # no thunder all year: not reported
    assert hourly.loc["2015", "rain_seen"].isna().all()
    days = airport_days(airport)
    assert len(days) == 729  # 5 January has reports in only 14 hours
    assert days.loc[storms[0].normalize().tz_localize(None), "thunder"]


def test_thunder_days_take_each_day_from_the_first_source_that_reports_it():
    index = hours("2014-01-01", "2016-01-01")
    storms = [t for t in index if t.year == 2014 and t.month == 6 and t.hour == 16]
    airport = airport_table(index, storms)
    days = dates("2013-01-01", "2016-01-01")
    gsod = pd.DataFrame({"thunder": pd.array([False] * len(days), dtype="boolean")}, index=days)
    gsod.loc["2013-07-01":"2013-07-10", "thunder"] = True
    gsod.loc["2015-07-01":"2015-07-10", "thunder"] = True
    out = thunder_days(airport, gsod, ["airport", "gsod"])
    assert out.loc["2014-06-15", "thunder"] and out.loc["2014-06-15", "thunder_source"] == "airport"
    assert out.loc["2013-07-01", "thunder_source"] == "gsod"
    assert (out.loc["2015", "thunder_source"] == "gsod").all()  # the airport saw no thunder in 2015
    only_gsod = thunder_days(airport, gsod, ["gsod"])
    assert (only_gsod["thunder_source"] == "gsod").all()
    assert thunder_days(airport.iloc[:0], gsod.iloc[:0], ["airport", "gsod"]).empty


def sources(start: str = "2019-01-01", end: str = "2021-01-01"):
    """Two invented years of every source the table combines."""
    index = hours(start, end)
    utc_hour = index.tz_convert("UTC").hour
    rng = np.random.default_rng(0)
    rain = np.where(rng.random(len(index)) < 0.05, rng.exponential(1.5, len(index)), 0.0)
    era5 = pd.DataFrame(
        {
            "temperature": 12
            - 6 * np.cos(2 * np.pi * utc_hour / 24)
            - 10 * np.cos(2 * np.pi * index.day_of_year / 365),
            "precipitation": rain,
            "wind_gust": 20 + 10 * rng.random(len(index)),
        },
        index=index,
    )
    station = (era5[["temperature"]] + 0.5).drop(index[1000:1003]).drop(index[5000:5100])
    storms = [t for t in index if t.month == 6 and t.hour == 17 and t.day % 4 == 0]
    airport = airport_table(index, storms)
    days = dates(start, end)
    daily_rain = era5["precipitation"].groupby(index.tz_localize(None).normalize()).sum()
    gsod = pd.DataFrame(
        {"precipitation": np.where(daily_rain.reindex(days) > 2.5, 3.0, 0.0), "thunder": pd.NA},
        index=days,
    ).astype({"thunder": "boolean"})
    return era5, station, airport, gsod


def config(tmp_path=None) -> Config:
    data = Data(first_year=2019, rain_calibration_years=(2019, 2020), **({"cache_dir": tmp_path} if tmp_path else {}))
    return Config(data=data)


def test_assemble_combines_the_sources():
    era5, station, airport, gsod = sources()
    tables = assemble(config(), era5, station, airport, gsod, today=date(2026, 11, 5))
    hourly, daily = tables.hourly, tables.daily
    assert list(hourly.columns) == [
        "temperature",
        "temperature_source",
        "precipitation",
        "wind_gust",
        "rain_seen",
        "thunder",
        "daylight",
    ]
    assert hourly["temperature"].notna().all()
    assert set(hourly["temperature_source"]) == {"station", "station curve", "era5 corrected"}
    assert np.allclose(hourly["temperature"], era5["temperature"] + 0.5, atol=0.1)
    assert hourly.index.name == "time" and daily.index.name == "date"
    assert daily.loc["2019-06-21", "sunrise"].hour == 5 and daily.loc["2019-06-21", "sunset"].hour == 21
    assert daily.loc["2019-06-04", "thunder"] and daily.loc["2019-06-04", "thunder_source"] == "airport"
    assert not daily.loc["2019-06-05", "thunder"]
    assert daily["wet"].mean() == pytest.approx((gsod["precipitation"] >= 1).mean(), abs=0.01)
    assert daily.loc["2019-06-21", "tmax"] == pytest.approx(hourly.loc["2019-06-21", "temperature"].max())
    assert daily["station_hours"].max() == 25 and daily["station_hours"].min() < 23  # 25: clocks go back
    assert tables.info["temperature_sources"]["station curve"] == 3
    assert len(tables.info["wet_day_thresholds_mm"]) == 12


def test_assemble_stops_at_today_and_at_the_first_year():
    era5, station, airport, gsod = sources()
    tables = assemble(config(), era5, station, airport, gsod, today=date(2020, 7, 1))
    assert tables.hourly.index.max() < pd.Timestamp("2020-07-01", tz=TZ)
    with pytest.raises(MissingDataError):
        assemble(config(), era5.loc["2019"], station, airport, gsod, today=date(2019, 1, 1))


def test_build_saves_and_load_reads_back(tmp_path):
    from weather_odds.cache import Cache

    cfg = config(tmp_path)
    with pytest.raises(MissingDataError, match="prefetch"):
        build(cfg, log=lambda _: None)
    assert load(cfg) is None
    cache = Cache(cfg.data.cache_dir, cfg.location.slug)
    for name, table in zip(("era5", "meteostat", "airport", "gsod"), sources(), strict=True):
        cache.save_table(name, table)
    lines = []
    built = build(cfg, today=date(2026, 11, 5), log=lines.append)
    assert lines[0].startswith("hourly table:")
    loaded = load(cfg)
    pd.testing.assert_frame_equal(loaded.daily, built.daily)
    assert loaded.info["wet_day_thresholds_mm"] == built.info["wet_day_thresholds_mm"]
