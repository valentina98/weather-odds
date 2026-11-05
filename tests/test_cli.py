import subprocess
import sys

import pytest
import yaml

from weather_odds import __version__
from weather_odds.cli import main
from weather_odds.config import Config


def test_config_prints_the_settings(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["config"]) == 0
    assert Config.model_validate(yaml.safe_load(capsys.readouterr().out)) == Config()


def test_config_reports_invalid_files(tmp_path, capsys):
    path = tmp_path / "bad.yaml"
    path.write_text("statistics: {years: 0}\n", encoding="utf-8")
    assert main(["--config", str(path), "config"]) == 1
    assert "years" in capsys.readouterr().err


def test_version(capsys):
    with pytest.raises(SystemExit) as exit_:
        main(["--version"])
    assert exit_.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_runs_as_a_module(tmp_path):
    out = subprocess.run(
        [sys.executable, "-m", "weather_odds", "config"], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    assert "Plovdiv" in out.stdout


def test_build_and_check_need_the_downloads_first(tmp_path, capsys):
    path = tmp_path / "config.yaml"
    path.write_text(f"data: {{cache_dir: {tmp_path.as_posix()}/cache}}\n", encoding="utf-8")
    assert main(["--config", str(path), "build"]) == 1
    assert "weather-odds prefetch" in capsys.readouterr().err
    assert main(["--config", str(path), "check"]) == 1
    assert "weather-odds prefetch" in capsys.readouterr().err


def test_build_from_the_cache(tmp_path, capsys):
    from test_table import sources

    from weather_odds.cache import Cache

    path = tmp_path / "config.yaml"
    path.write_text(
        f"data: {{cache_dir: {tmp_path.as_posix()}/cache, first_year: 2019, rain_calibration_years: [2019, 2020]}}\n",
        encoding="utf-8",
    )
    cache = Cache(tmp_path / "cache", "plovdiv")
    for name, table in zip(("era5", "meteostat", "airport", "gsod"), sources(), strict=True):
        cache.save_table(name, table)
    assert main(["--config", str(path), "build"]) == 0
    assert "hourly table: 17544 hours" in capsys.readouterr().out
    assert cache.table_path("hourly").exists() and cache.table_path("daily").exists()
