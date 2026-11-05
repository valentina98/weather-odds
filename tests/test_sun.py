import pandas as pd
import pytest

from weather_odds.sun import daylight, sun_times

PLOVDIV = (42.1333, 24.75)
TZ = "Europe/Sofia"

# Reference times from the astral library (solar depression 0.833 degrees).
REFERENCE = {
    "2026-06-21": ("05:45:18", "21:00:18"),  # summer time, UTC+3
    "2026-12-21": ("07:46:16", "16:51:47"),  # winter time, UTC+2
    "2026-03-29": ("07:09:21", "19:42:53"),  # the day the clocks go forward
    "2026-10-25": ("06:45:20", "17:24:08"),  # the day the clocks go back
}


@pytest.mark.parametrize("day", REFERENCE)
def test_sunrise_and_sunset_within_two_minutes(day):
    times = sun_times(pd.DatetimeIndex([day]), *PLOVDIV, TZ).iloc[0]
    rise, set_ = (pd.Timestamp(f"{day} {t}", tz=TZ) for t in REFERENCE[day])
    assert abs(times["sunrise"] - rise) < pd.Timedelta(minutes=2)
    assert abs(times["sunset"] - set_) < pd.Timedelta(minutes=2)
    assert str(times["sunrise"].tz) == TZ


def test_dates_with_a_time_or_time_zone_give_the_same_day():
    plain = sun_times(pd.DatetimeIndex(["2026-06-21"]), *PLOVDIV, TZ)
    aware = sun_times(pd.DatetimeIndex([pd.Timestamp("2026-06-21 15:00", tz=TZ)]), *PLOVDIV, TZ)
    assert plain["sunrise"].iloc[0] == aware["sunrise"].iloc[0]
    assert list(plain.index) == [pd.Timestamp("2026-06-21")]


def test_polar_night_has_no_sunrise():
    times = sun_times(pd.DatetimeIndex(["2026-12-21"]), 80.0, 15.0, "Europe/Oslo")
    assert times.isna().all(axis=None)


def test_daylight_hours_start_between_sunrise_and_sunset():
    hours = pd.date_range("2026-06-21", periods=24, freq="h", tz=TZ)
    light = hours[daylight(hours, *PLOVDIV)]
    assert light[0] == pd.Timestamp("2026-06-21 06:00", tz=TZ)
    assert light[-1] == pd.Timestamp("2026-06-21 21:00", tz=TZ)  # starts 2 seconds before sunset
    winter = pd.date_range("2026-12-21", periods=24, freq="h", tz=TZ)
    assert daylight(winter, *PLOVDIV).sum() == 9  # 08:00 to 16:00
