import numpy as np
import pandas as pd
import pytest

from weather_odds.checks import check_fills, report
from weather_odds.temperature import CURVE, ERA5, STATION, fill_temperature, gap_lengths

TZ = "Europe/Sofia"


def synthetic(start: str, end: str) -> tuple[pd.Series, pd.Series]:
    """A station with the same daily curve every day, and an ERA5 that is 1.5 C colder with a flatter curve."""
    index = pd.date_range(start, end, freq="h", tz="UTC", inclusive="left")
    curve = np.sin(2 * np.pi * (index.hour - 9) / 24)
    station = pd.Series(10 + 5 * curve, index=index).tz_convert(TZ)
    era5 = pd.Series(8.5 + 3 * curve, index=index).tz_convert(TZ)
    return station, era5


def test_gap_lengths():
    values = pd.Series([np.nan, 1.0, np.nan, np.nan, 4.0, np.nan])
    assert list(gap_lengths(values)) == [np.inf, 0, 2, 2, 0, np.inf]
    assert np.isinf(gap_lengths(pd.Series([np.nan, np.nan]))).all()


def test_measured_hours_are_kept():
    station, era5 = synthetic("2020-01-01", "2020-02-01")
    out = fill_temperature(station, era5)
    assert (out["temperature_source"] == STATION).all()
    pd.testing.assert_series_equal(out["temperature"], station, check_names=False, check_freq=False)
    assert str(out.index.tz) == TZ


def test_short_gaps_follow_the_station_curve():
    station, era5 = synthetic("2020-01-01", "2020-02-01")
    hidden = station.index[100:104]
    out = fill_temperature(station.drop(hidden), era5)
    assert (out.loc[hidden, "temperature_source"] == CURVE).all()
    assert out.loc[hidden, "temperature"].to_numpy() == pytest.approx(station[hidden].to_numpy(), abs=1e-9)


def test_three_hourly_readings_are_rebuilt():
    station, era5 = synthetic("2019-01-01", "2020-03-01")
    early = (station.index.year == 2020) & (station.index.tz_convert("UTC").hour % 3 != 0)
    out = fill_temperature(station[~early], era5)  # 2020 rebuilt with 2019's daily curve
    rebuilt = out["2020-01-01 03:00":"2020-02-28"]  # between the first and last 2020 readings
    assert set(rebuilt["temperature_source"]) == {STATION, CURVE}
    truth = station[rebuilt.index]
    assert rebuilt["temperature"].to_numpy() == pytest.approx(truth.to_numpy(), abs=1e-9)


def test_gaps_of_days_use_corrected_era5():
    station, era5 = synthetic("2020-01-01", "2020-02-01")
    hidden = station.index[200:248]  # two days
    out = fill_temperature(station.drop(hidden), era5)
    assert (out.loc[hidden, "temperature_source"] == ERA5).all()
    assert out.loc[hidden, "temperature"].to_numpy() == pytest.approx(station[hidden].to_numpy(), abs=1e-9)


def test_longer_gaps_and_the_edges_stay_missing():
    station, era5 = synthetic("2020-01-01", "2020-03-01")
    kept = station[(station.index < "2020-01-10") | (station.index >= "2020-01-25")]
    kept = kept[kept.index >= "2020-01-03"]
    out = fill_temperature(kept, era5)
    assert out.loc["2020-01-12":"2020-01-22", "temperature"].isna().all()
    assert out.loc["2020-01-12":"2020-01-22", "temperature_source"].isna().all()
    assert out.loc[:"2020-01-02", "temperature"].isna().all()  # before the first reading


def test_checks_report_each_fill():
    station, era5 = synthetic("2018-01-01", "2020-01-01")
    noise = np.random.default_rng(0).normal(0, 0.5, len(station))
    checks = check_fills(station + noise, era5)
    assert [c.name for c in checks] == ["gaps of 1-6 hours", "gaps of 1-7 days", "3-hourly years rebuilt"]
    assert all(c.hours > 0 for c in checks)
    assert checks[0].passed and checks[2].passed  # the station curve beats a straight line
    text = report(checks)
    assert text.count("\n|") == 4 and "daily max bias" in text
