import numpy as np
import pandas as pd
import pytest

from weather_odds.fill import (
    ERA5,
    INTERPOLATED,
    STATION,
    FillSettings,
    fill_temperature,
    interpolated_difference,
    run_lengths,
    typical_difference,
)

TZ = "Europe/Sofia"


def hours(start: str, periods: int) -> pd.DatetimeIndex:
    return pd.date_range(pd.Timestamp(start, tz="UTC"), periods=periods, freq="h").tz_convert(TZ)


def era5_series(index: pd.DatetimeIndex) -> pd.Series:
    """A daily cycle: 10 deg C plus 5 at 12 UTC, minus 5 at midnight."""
    return pd.Series(10 - 5 * np.cos(2 * np.pi * index.tz_convert("UTC").hour / 24), index=index)


def test_run_lengths():
    assert list(run_lengths(np.array([0, 1, 1, 0, 1, 0, 0, 1, 1, 1], bool))) == [0, 2, 2, 0, 1, 0, 0, 3, 3, 3]
    assert list(run_lengths(np.array([], bool))) == []
    assert list(run_lengths(np.zeros(3, bool))) == [0, 0, 0]


def test_short_gaps_follow_era5_between_readings():
    index = hours("2020-07-01", 48)
    era5 = era5_series(index)
    # the station reads 2 deg C warmer than ERA5 at the start and 4 deg C warmer 10 hours later
    station = pd.concat([era5.iloc[:5] + 2, era5.iloc[15:] + 4])
    difference = interpolated_difference(station, era5, max_hours=12)
    assert difference.iloc[4] == pytest.approx(2) and difference.iloc[15] == pytest.approx(4)
    assert difference.iloc[10] == pytest.approx(2 + 2 * 6 / 11)  # linear between the two readings
    out = fill_temperature(station, era5, FillSettings(interpolate_hours=12))
    assert (out["temperature_source"].iloc[5:15] == INTERPOLATED).all()
    assert out["temperature"].iloc[10] == pytest.approx(era5.iloc[10] + 2 + 2 * 6 / 11)
    assert (out["temperature_source"].iloc[:5] == STATION).all()


def test_gaps_longer_than_the_limit_are_not_interpolated():
    index = hours("2020-07-01", 48)
    era5 = era5_series(index)
    station = pd.concat([era5.iloc[:5] + 2, era5.iloc[20:] + 2])
    assert interpolated_difference(station, era5, max_hours=12).iloc[5:20].isna().all()
    assert interpolated_difference(station, era5, max_hours=15).iloc[5:20].notna().all()


def test_hours_before_the_first_reading_are_not_interpolated():
    index = hours("2020-07-01", 24)
    era5 = era5_series(index)
    difference = interpolated_difference(era5.iloc[5:] + 1, era5, max_hours=12)
    assert difference.iloc[:5].isna().all()


def test_typical_difference_comes_from_the_nearby_years():
    index = hours("2010-01-01", 24 * 365 * 12)
    years = index.year
    # the difference grows by 0.1 deg C a year, and is 1 deg C larger at 12 UTC
    difference = pd.Series(0.1 * (years - 2010) + (index.tz_convert("UTC").hour == 12), index=index, dtype=float)
    hidden = difference.where(years != 2015)
    typical = typical_difference(hidden, window_years=2)
    at = (years == 2015) & (index.month == 6)
    noon = at & (index.tz_convert("UTC").hour == 12)
    assert typical[at & ~noon].mean() == pytest.approx(0.5)  # mean of 2013, 2014, 2016, 2017
    assert typical[noon].mean() == pytest.approx(1.5)


def test_long_gaps_use_era5_corrected_and_very_long_gaps_stay_empty():
    index = hours("2018-01-01", 24 * 365 * 3)
    era5 = era5_series(index)
    station = era5 + 1.5
    week = (index >= pd.Timestamp("2019-03-01", tz=TZ)) & (index < pd.Timestamp("2019-03-08", tz=TZ))
    year = index.year == 2020
    station = station[~week & ~year]
    out = fill_temperature(station, era5, FillSettings(interpolate_hours=12, fill_days=31, window_years=1))
    assert (out["temperature_source"][week] == ERA5).all()
    assert np.allclose(out["temperature"][week], era5[week] + 1.5)
    assert out["temperature"][year].isna().all() and out["temperature_source"][year].isna().all()

    all_filled = fill_temperature(station, era5, FillSettings(fill_days=31, window_years=1, fill_long_gaps=True))
    assert np.allclose(all_filled["temperature"][year], era5[year] + 1.5)
