import numpy as np
import pandas as pd
import pytest

from weather_odds.config import Scale, Thresholds
from weather_odds.stats.scale import (
    day_scores,
    gust_factor,
    hour_factors,
    hour_scores,
    rain_factor,
    temperature_factor,
)

TH = Thresholds()


def test_temperature_factor_follows_the_methodology():
    t = np.array([-5.0, 0.0, 9.0, 18.0, 22.0, 26.0, 32.0, 38.0, 40.0])
    assert list(temperature_factor(t, TH)) == pytest.approx([0, 0, 0.5, 1, 1, 1, 0.5, 0, 0])


def test_rain_factor_steps_and_missing_values():
    mm = np.array([0.0, 0.19, 0.2, 0.99, 1.0, 12.0, np.nan])
    out = rain_factor(mm, TH)
    assert list(out[:-1]) == [1, 1, 0.5, 0.5, 0.2, 0.2]
    assert np.isnan(out[-1])


def test_gust_factor_falls_linearly():
    assert list(gust_factor(np.array([10.0, 30.0, 52.5, 75.0, 90.0]), TH)) == pytest.approx([1, 1, 0.5, 0, 0])


def hourly(temperature, precipitation=0.0, gust=10.0, thunder=False, start="2020-07-01 00:00", periods=24):
    index = pd.date_range(start, periods=periods, freq="h", tz="Europe/Sofia")
    return pd.DataFrame(
        {"temperature": temperature, "precipitation": precipitation, "wind_gust": gust, "thunder": thunder},
        index=index,
    )


def test_hour_score_multiplies_the_factors():
    table = hourly(22.0, precipitation=0.5, gust=52.5, thunder=True, periods=1)
    assert hour_scores(table, Scale()).iloc[0] == pytest.approx(100 * 0.5 * 0.5 * 0.2)


def test_missing_thunder_counts_as_none_and_missing_temperature_as_unknown():
    table = hourly(22.0, periods=2)
    table["thunder"] = pd.array([pd.NA, True], dtype="boolean")
    table.loc[table.index[1], "temperature"] = np.nan
    scores = hour_scores(table, Scale())
    assert scores.iloc[0] == 100 and np.isnan(scores.iloc[1])


def test_each_band_uses_its_own_thresholds():
    scale = Scale(bands={"evening": {"comfort": [15, 26]}})
    scores = hour_scores(hourly(16.5), scale)
    assert scores.iloc[18] == 100 and scores.iloc[23] == 100  # evening: 15-26 deg C is comfortable
    assert scores.iloc[12] == pytest.approx(100 * 16.5 / 18)  # afternoon: the default 18-26
    factors = hour_factors(hourly(16.5), scale)
    assert list(factors.columns) == ["temperature", "rain", "wind", "thunder"]


def test_day_score_is_the_mean_with_rain_caps():
    table = hourly(22.0)
    assert day_scores(table, Scale()).iloc[0] == 100
    wet = hourly(22.0, precipitation=[1.2] + [0.0] * 23)  # one rainy hour: 1.2 mm
    assert day_scores(wet, Scale()).iloc[0] == 59  # mean 96.7, capped at Fair
    soaked = hourly(22.0, precipitation=[5.0] + [0.0] * 23)
    assert day_scores(soaked, Scale()).iloc[0] == 39
    two_days = pd.concat([table, hourly(9.0, start="2020-07-02 00:00")])
    assert list(day_scores(two_days, Scale())) == pytest.approx([100, 50])
