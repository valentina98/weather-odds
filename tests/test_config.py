from datetime import date
from pathlib import Path

import pytest
import yaml

from weather_odds.config import BAND_HOURS, Config, ConfigError, dump_config, load_config

ROOT = Path(__file__).resolve().parents[1]


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_example_lists_the_defaults():
    assert load_config(ROOT / "config.example.yaml") == Config()


def test_defaults_match_the_methodology():
    config = Config()
    th = config.scale.thresholds
    assert th.comfort == (18, 26) and (th.cold_zero, th.hot_zero) == (0, 38)
    assert [(c.from_mm, c.max_score) for c in th.rain_caps] == [(1, 59), (5, 39)]
    assert (th.gust_ok, th.gust_zero) == (30, 75)
    assert config.statistics.years == 30 and config.statistics.trend_adjustment
    assert config.statistics.pooling_days == 0
    assert config.view.hours() is None and config.view.granularity == "week"


def test_no_file_gives_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_config() == Config()


def test_config_yaml_in_working_directory_is_used(tmp_path, monkeypatch):
    write(tmp_path, "statistics: {years: 10}\n")
    monkeypatch.chdir(tmp_path)
    assert load_config().statistics.years == 10


def test_partial_file_keeps_other_defaults(tmp_path):
    config = load_config(write(tmp_path, "scale:\n  thresholds:\n    comfort: [16, 25]\n"))
    assert config.scale.thresholds.comfort == (16, 25)
    assert config.scale.thresholds.hot_zero == 38
    assert config.view == Config().view


def test_empty_file_gives_defaults(tmp_path):
    assert load_config(write(tmp_path, "")) == Config()


def test_dump_reads_back(tmp_path):
    config = load_config(
        write(tmp_path, "scale: {bands: {evening: {comfort: [15, 26]}}}\nview: {time_of_day: '18-22'}\n")
    )
    assert load_config(write(tmp_path, dump_config(config))) == config


def test_reference_period_span():
    assert Config().statistics.span(date(2026, 10, 29)) == (1996, 2025)
    assert load_config_text("statistics: {years: 10, last_year: 2020}").statistics.span() == (2011, 2020)


def test_band_changes_only_their_band():
    config = load_config_text("scale: {bands: {evening: {comfort: [15, 26], rain: {light_mm: 0.1}}}}")
    evening = config.scale.for_band("evening")
    assert evening.comfort == (15, 26)
    assert evening.rain.light_mm == 0.1 and evening.rain.heavy_mm == 1.0
    for band in BAND_HOURS:
        if band != "evening":
            assert config.scale.for_band(band) == config.scale.thresholds


def test_band_takes_later_changes_to_the_defaults_it_did_not_set():
    config = load_config_text("scale: {thresholds: {gust_ok: 40}, bands: {evening: {comfort: [15, 26]}}}")
    assert config.scale.for_band("evening").gust_ok == 40


@pytest.mark.parametrize(
    "text",
    [
        "statistics: {years: 0}",
        "statistics: {pooling_days: -1}",
        "statistics: {yeras: 30}",
        "location: {timezone: Europe/Nowhere}",
        "scale: {thresholds: {comfort: [26, 18]}}",
        "scale: {thresholds: {cold_zero: 20}}",
        "scale: {thresholds: {gust_ok: 80}}",
        "scale: {thresholds: {rain: {light_mm: 2}}}",
        "scale: {thresholds: {rain: {heavy_factor: 0.9}}}",
        "scale: {thresholds: {rain_caps: [{from_mm: 1, max_score: 120}]}}",
        "scale: {classes: {good: 90}}",
        "scale: {bands: {lunch: {comfort: [15, 26]}}}",
        "scale: {bands: {evening: {comfort: [30, 20]}}}",
        "scale: {bands: {evening: {comfrot: [15, 26]}}}",
        "view: {time_of_day: '22-02'}",
        "view: {time_of_day: evening}",
        "view: {granularity: year}",
        "data: {temperature: []}",
        "data: {temperature: [station, station]}",
        "data: {thunder: [era5]}",
        "- a list",
        "statistics: [",
    ],
)
def test_invalid_values_are_rejected(tmp_path, text):
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, text))


def test_missing_file_is_an_error(tmp_path):
    with pytest.raises(ConfigError, match="cannot read"):
        load_config(tmp_path / "nope.yaml")


def test_settings_are_frozen():
    with pytest.raises(ValueError):
        Config().statistics.years = 10  # type: ignore[misc]


def load_config_text(text: str) -> Config:
    return Config.model_validate(yaml.safe_load(text))
