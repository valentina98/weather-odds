from datetime import date

import pandas as pd
import pytest
import samples
from fakes import FakeSession

from weather_odds.config import Location
from weather_odds.download import Downloader
from weather_odds.sources import SOURCES, airport, gsod, meteostat, nimh

PLOVDIV = Location()
TODAY = date(2026, 10, 29)


def local(text: str) -> pd.Timestamp:
    return pd.Timestamp(text, tz="Europe/Sofia")


def test_meteostat_keeps_measured_temperatures_in_local_time(tmp_path):
    (tmp_path / "2020.csv.gz").write_bytes(samples.gz(samples.METEOSTAT_2020))
    (tmp_path / "2021.csv.gz").write_bytes(samples.gz(samples.METEOSTAT_2021))
    table = meteostat.parse(tmp_path, PLOVDIV, TODAY)
    assert list(table.columns) == ["temperature"]
    assert table.loc[local("2020-01-01 02:00"), "temperature"] == 6.0  # 00 UTC, winter time UTC+2
    assert table.loc[local("2020-01-01 03:00"), "temperature"] == 7.5  # airport report
    assert local("2020-01-01 04:00") not in table.index  # model value dropped
    assert local("2020-01-01 05:00") not in table.index  # not measured
    assert table.loc[local("2020-07-01 15:00"), "temperature"] == 31.4  # summer time UTC+3
    assert table.loc[local("2021-01-01 02:00"), "temperature"] == -2.5
    assert table.index.is_monotonic_increasing and table.index.name == "time"


def test_meteostat_across_the_spring_clock_change(tmp_path):
    (tmp_path / "2020.csv.gz").write_bytes(samples.gz(samples.METEOSTAT_2020))
    table = meteostat.parse(tmp_path, PLOVDIV, TODAY)
    assert table.loc[local("2020-03-29 02:00"), "temperature"] == 4.0  # 00 UTC
    assert table.loc[local("2020-03-29 04:00"), "temperature"] == 5.0  # 01 UTC; 03:00 local does not exist


def test_gsod_converts_units_and_reads_the_flags(tmp_path):
    (tmp_path / "1990.csv").write_text(samples.GSOD_1990)
    table = gsod.parse(tmp_path, PLOVDIV, TODAY)
    first = table.loc["1990-06-01"]
    assert first["tmax"] == pytest.approx(30.0) and first["tmin"] == pytest.approx(15.0)
    assert first["precipitation"] == pytest.approx(12.7)
    assert first["rain_seen"] and first["thunder"] and not first["snow_seen"]
    assert pd.isna(table.loc["1990-06-02", "tmax"])
    assert pd.isna(table.loc["1990-06-02", "precipitation"])  # "I": no rain report that day
    assert pd.isna(table.loc["1990-06-03", "precipitation"])  # 99.99: missing
    assert table.loc["1990-06-03", "snow_seen"] and not table.loc["1990-06-03", "rain_seen"]
    assert pd.isna(table.loc["1990-06-04", "thunder"])  # flags missing, not "no thunder"
    assert table.index.name == "date"


def test_airport_reports_become_hours(tmp_path):
    (tmp_path / "2020.csv").write_text(samples.AIRPORT_2020)
    (tmp_path / "2021.csv").write_text(samples.AIRPORT_EMPTY)
    table = airport.parse(tmp_path, PLOVDIV, TODAY)
    noon = table.loc[local("2020-07-01 12:00")]
    assert noon["rain_seen"] and noon["thunder"] and not noon["snow_seen"] and noon["reports"] == 2
    one = table.loc[local("2020-07-01 13:00")]
    assert not one["rain_seen"] and not one["thunder"] and one["reports"] == 2
    assert table.loc[local("2020-12-01 08:00"), "snow_seen"]
    assert len(table) == 3


def test_nimh_reads_the_station_row(tmp_path):
    (tmp_path / "mosv_prec_202202.csv").write_text(samples.NIMH_202202)
    table = nimh.parse(tmp_path, PLOVDIV, TODAY)
    assert len(table) == 27  # February 2022 without the unreadable 4th; 30 February is ignored
    assert pd.Timestamp("2022-02-04") not in table.index
    assert table.loc["2022-02-02", "precipitation"] == 2.0
    assert table.loc["2022-02-03", "precipitation"] == 12.0
    assert table.loc["2022-02-01", "precipitation"] == 0.0  # blank cell


def test_nimh_stops_at_today(tmp_path):
    (tmp_path / "mosv_prec_202202.csv").write_text(samples.NIMH_202202)
    table = nimh.parse(tmp_path, PLOVDIV, date(2022, 2, 3))
    assert list(table.index.day) == [1, 2]


@pytest.mark.parametrize("name", list(SOURCES))
def test_nothing_downloaded_gives_an_empty_table(tmp_path, name):
    table = SOURCES[name].parse(tmp_path, PLOVDIV, TODAY)
    assert table.empty and list(table.columns) == list(SOURCES[name].columns)


def test_yearly_sources_refresh_only_the_current_year(tmp_path):
    session = FakeSession(
        {meteostat.URL.format(year=y, station="15625"): samples.gz(samples.METEOSTAT_HEADER) for y in (2025, 2026)}
    )
    dl = Downloader(session, pause=0)
    assert meteostat.fetch(dl, tmp_path, PLOVDIV, range(2024, 2027), TODAY, refresh=False) == 2
    assert meteostat.fetch(dl, tmp_path, PLOVDIV, range(2024, 2027), TODAY, refresh=False) == 1
    asked = [url for url, _ in session.calls]
    assert asked.count(meteostat.URL.format(year=2026, station="15625")) == 2
    assert asked.count(meteostat.URL.format(year=2025, station="15625")) == 1
    assert asked.count(meteostat.URL.format(year=2024, station="15625")) == 1  # 404, remembered


def test_airport_asks_for_the_configured_airport(tmp_path):
    session = FakeSession({airport.URL: samples.AIRPORT_EMPTY.encode()})
    airport.fetch(Downloader(session, pause=0), tmp_path, PLOVDIV, range(2025, 2026), TODAY, refresh=False)
    ((_, params),) = session.calls
    assert params["station"] == "LBPD" and params["year1"] == 2025 and params["year2"] == 2026


def test_nimh_fetches_the_listed_months_in_range(tmp_path):
    session = FakeSession(
        {
            nimh.INDEX: samples.NIMH_INDEX.encode(),
            nimh.FILE.format(name="mosv_prec_202202.csv"): samples.NIMH_202202.encode(),
        }
    )
    written = nimh.fetch(Downloader(session, pause=0), tmp_path, PLOVDIV, range(2022, 2027), TODAY, refresh=False)
    assert written == 1
    assert [p.name for p in tmp_path.iterdir()] == ["mosv_prec_202202.csv"]


def test_nimh_refreshes_this_and_last_month(tmp_path):
    months = ("202608", "202609", "202610")
    files = {nimh.FILE.format(name=f"mosv_prec_{m}.csv"): samples.NIMH_202202.encode() for m in months}
    index = " ".join(f"mosv_prec_{m}.csv" for m in months).encode()
    session = FakeSession({nimh.INDEX: index} | files)
    dl = Downloader(session, pause=0)
    assert nimh.fetch(dl, tmp_path, PLOVDIV, range(2026, 2027), TODAY, refresh=False) == 3
    assert nimh.fetch(dl, tmp_path, PLOVDIV, range(2026, 2027), TODAY, refresh=False) == 2
    asked = [url.rsplit("_", 1)[-1] for url, _ in session.calls if url != nimh.INDEX]
    assert asked.count("202608.csv") == 1 and asked.count("202609.csv") == 2 and asked.count("202610.csv") == 2
