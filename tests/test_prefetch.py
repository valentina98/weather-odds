from datetime import date

import pandas as pd
import pytest
import samples
from fakes import FakeBucket, FakeSession

from weather_odds import cli
from weather_odds.cache import Cache
from weather_odds.config import Config
from weather_odds.download import Downloader
from weather_odds.prefetch import prefetch
from weather_odds.sources import SOURCES, airport, era5, gsod, meteostat, nimh

TODAY = date(2026, 10, 29)


def config(tmp_path) -> Config:
    return Config.model_validate({"data": {"cache_dir": str(tmp_path / "cache"), "first_year": 2020}})


def all_sources() -> dict:
    return {
        meteostat.URL.format(year=2020, station="15625"): samples.gz(samples.METEOSTAT_2020),
        gsod.URL.format(year=2020, station="15625"): samples.GSOD_1990.encode(),
        airport.URL: lambda params: (
            samples.AIRPORT_2020 if params["year1"] == 2020 else samples.AIRPORT_EMPTY
        ).encode(),
        nimh.INDEX: samples.NIMH_INDEX.encode(),
        nimh.FILE.format(name="mosv_prec_202202.csv"): samples.NIMH_202202.encode(),
    }


def test_prefetch_stores_a_table_per_source(tmp_path, monkeypatch):
    monkeypatch.setattr(era5, "open_bucket", FakeBucket)
    lines = []
    failed = prefetch(
        config(tmp_path),
        downloader=lambda: Downloader(FakeSession(all_sources()), pause=0),
        today=TODAY,
        log=lines.append,
    )
    assert failed == []
    cache = Cache(tmp_path / "cache", "plovdiv")
    for name in SOURCES:
        table = cache.load_table(name)
        assert table is not None and len(table) > 0, name
    hourly = cache.load_table("meteostat")
    assert str(hourly.index.tz) == "Europe/Sofia"
    assert cache.load_table("gsod")["thunder"].dtype == "boolean"
    assert len(lines) == len(SOURCES)


def test_a_failing_source_does_not_stop_the_others(tmp_path, monkeypatch):
    monkeypatch.setattr(era5, "open_bucket", FakeBucket)
    routes = all_sources() | {nimh.INDEX: 500}
    lines = []
    failed = prefetch(
        config(tmp_path),
        downloader=lambda: Downloader(FakeSession(routes), retries=0, pause=0),
        today=TODAY,
        log=lines.append,
    )
    assert failed == ["nimh"]
    assert Cache(tmp_path / "cache", "plovdiv").load_table("meteostat") is not None
    assert any(line.startswith("nimh:") and "download failed" in line for line in lines)


def test_cached_tables_round_trip(tmp_path):
    cache = Cache(tmp_path, "plovdiv")
    index = pd.DatetimeIndex(
        pd.date_range("2020-10-25 01:00", periods=4, freq="h", tz="UTC").tz_convert("Europe/Sofia")
    )
    table = pd.DataFrame({"thunder": pd.array([True, None, False, True], dtype="boolean")}, index=index)
    cache.save_table("x", table)
    pd.testing.assert_frame_equal(cache.load_table("x"), table, check_freq=False)
    assert cache.load_table("missing") is None


def test_cli_prefetch_reports_failures(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "prefetch", lambda config, names, refresh: ["gsod"])
    assert cli.main(["prefetch"]) == 1
    assert "gsod could not be downloaded" in capsys.readouterr().err
    monkeypatch.setattr(cli, "prefetch", lambda config, names, refresh: [])
    assert cli.main(["prefetch", "--sources", "gsod,nimh", "--refresh"]) == 0


def test_cli_rejects_unknown_sources(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exit_:
        cli.main(["prefetch", "--sources", "gsod,bogus"])
    assert exit_.value.code == 2


def test_an_unreadable_cached_file_is_reported(tmp_path):
    cfg = config(tmp_path)
    broken = Cache(tmp_path / "cache", "plovdiv").raw("gsod") / "2020.csv"
    broken.parent.mkdir(parents=True)
    broken.write_text("not,a,gsod,file\n1,2,3,4\n")
    lines = []
    failed = prefetch(
        cfg,
        ["gsod", "meteostat"],
        downloader=lambda: Downloader(FakeSession(all_sources()), pause=0),
        today=TODAY,
        log=lines.append,
    )
    assert failed == ["gsod"]
    assert any("gsod: cached files could not be read" in line for line in lines)
    assert Cache(tmp_path / "cache", "plovdiv").load_table("meteostat") is not None
