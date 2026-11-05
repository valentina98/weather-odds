from datetime import date

import pandas as pd
import pytest
from fakes import FakeBucket

from weather_odds.config import Location
from weather_odds.sources import era5

PLOVDIV = Location()
TODAY = date(2026, 10, 29)


@pytest.fixture
def bucket(monkeypatch):
    fake = FakeBucket()
    monkeypatch.setattr(era5, "open_bucket", lambda: fake)
    return fake


def test_grid_cell_for_plovdiv():
    assert era5.grid_cell((721, 1440), 42.1333, 24.75) == (529, 819)  # 42.25 N, 24.75 E


def test_fetch_saves_whole_and_partial_years(tmp_path, bucket):
    years = range(2020, 2021)
    assert era5.fetch(None, tmp_path, PLOVDIV, years, TODAY, refresh=False) == 3
    assert sorted(p.name for p in (tmp_path / "temperature_2m").iterdir()) == ["2020.csv.gz"]
    assert era5.fetch(None, tmp_path, PLOVDIV, range(2026, 2027), TODAY, refresh=False) == 3
    assert sorted(p.name for p in (tmp_path / "precipitation").iterdir()) == ["2020.csv.gz", "2026.partial.csv.gz"]
    bucket.read.clear()
    assert era5.fetch(None, tmp_path, PLOVDIV, range(2020, 2027), TODAY, refresh=False) == 3  # only 2026 again
    assert not any("year_2020" in path for path in bucket.read)


def test_parse_converts_to_the_tidy_vocabulary(tmp_path, bucket):
    era5.fetch(None, tmp_path, PLOVDIV, range(2020, 2021), TODAY, refresh=False)
    table = era5.parse(tmp_path, PLOVDIV, TODAY)
    assert list(table.columns) == ["temperature", "precipitation", "wind_gust"]
    assert str(table.index.tz) == "Europe/Sofia"
    first = table.loc[pd.Timestamp("2020-01-01 02:00", tz="Europe/Sofia")]
    assert first["temperature"] == pytest.approx(10.0 + (300 - 179) * 0.0065)  # height-corrected
    assert first["wind_gust"] == pytest.approx(36.0)  # 10 m/s
    rain = table["precipitation"]
    assert rain.idxmax() == pd.Timestamp("2020-01-01 04:00 UTC")  # stamped 05 UTC, the hour starting 04 UTC
    assert rain.sum() == 1.0


def test_parse_without_downloads_is_empty(tmp_path):
    table = era5.parse(tmp_path, PLOVDIV, TODAY)
    assert table.empty and list(table.columns) == ["temperature", "precipitation", "wind_gust"]
