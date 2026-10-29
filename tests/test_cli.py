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
