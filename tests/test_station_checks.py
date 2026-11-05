import numpy as np
import pandas as pd
from test_table import config, sources

from weather_odds.station_checks import (
    Comparison,
    _years,
    rounded_nimh_check,
    station_checks,
    to_markdown,
    whole_year,
)
from weather_odds.table import assemble

TZ = "Europe/Sofia"


def test_station_checks_run_on_every_source(monkeypatch):
    import weather_odds.station_checks as checks

    monkeypatch.setattr(checks, "CALIBRATION_YEARS", (2019, 2020))
    era5, station, airport, gsod = sources()
    gsod = gsod.assign(tmax=station["temperature"].groupby(station.index.tz_localize(None).normalize()).max())
    days = gsod.index[gsod.index.year == 2020]
    nimh = pd.DataFrame({"precipitation": gsod.loc[days, "precipitation"]}, index=days)
    tables = assemble(config(), era5, station, airport, gsod)
    out = station_checks(tables, {"era5": era5, "gsod": gsod, "nimh": nimh, "airport": airport})
    assert all(isinstance(c, Comparison) for c in out) and len(out) == 14
    calibrated = next(c for c in out if c.name.startswith("Calibrated wet days in the table, 2019"))
    assert calibrated.passed  # calibrated on these years, so the wet-day share matches


def test_whole_year_fill_reports_the_range():
    index = pd.date_range(pd.Timestamp("1994-01-01", tz="UTC"), pd.Timestamp("2001-01-01", tz="UTC"), freq="h")
    index = index.tz_convert(TZ)
    day = 2 * np.pi * index.day_of_year / 365
    era5 = pd.Series(12 - 10 * np.cos(day) - 5 * np.cos(2 * np.pi * index.tz_convert("UTC").hour / 24), index=index)
    weather = 3 * np.sin(np.arange(len(index)) / 50)  # day-to-day swings the station has and ERA5 misses
    station = era5 + 1 + weather
    result = whole_year(station, era5, 1997)
    assert "1997 hidden" in result.name and "%" in result.value
    assert result.passed is None


def test_years_are_listed_as_ranges():
    assert _years([1997, 1998, 1999, 2003, 2012, 2013]) == "1997-1999, 2003, 2012-2013"
    assert _years([]) == ""


def test_markdown_report():
    report = to_markdown(
        [
            Comparison("A number", "5%", "5%", True),
            Comparison("Another", "6%", "5%", False),
            Comparison("Context", "7%", "for information"),
        ]
    )
    assert "| A number | 5% | 5% | matches |" in report
    assert "| Another | 6% | 5% | **differs** |" in report
    assert "| Context | 7% | for information | info |" in report


def test_rounded_nimh_amounts_are_compared_at_half_a_millimetre():
    days = pd.date_range("1980-01-01", "1999-12-31", freq="D")
    rng = np.random.default_rng(3)
    true_rain = pd.Series(np.where(rng.random(len(days)) < 0.3, rng.exponential(2.0, len(days)), 0.0), index=days)
    model = true_rain * 1.5  # a model that rains more than the station
    gsod = true_rain.loc["1980":"1989"]
    nimh = true_rain.loc["1990":"1999"].round()  # whole millimetres, as NIMH writes them
    result = rounded_nimh_check(model, gsod, nimh)
    assert result.passed, result.value
    assert rounded_nimh_check(model, gsod, nimh.iloc[:0]).passed is None
