import numpy as np
from test_table import config, sources

from weather_odds.checks import Check, _years, fill_checks, hide_runs, to_markdown


def test_hide_runs_leave_measured_neighbours():
    rng = np.random.default_rng(0)
    measured = np.ones(500, dtype=bool)
    measured[100:120] = False
    hidden = hide_runs(measured, 5, 20, rng, np.ones(500, dtype=bool))
    starts = np.flatnonzero(np.diff(np.concatenate([[0], hidden.astype(int)])) == 1)
    assert len(starts) == 20 and hidden.sum() == 100
    for start in starts:
        assert measured[start - 1] and measured[start + 5] and measured[start : start + 5].all()
        assert not hidden[start - 1] and not hidden[start + 5]


def test_hide_runs_respect_the_allowed_positions():
    rng = np.random.default_rng(1)
    allowed = np.zeros(300, dtype=bool)
    allowed[200:] = True
    hidden = hide_runs(np.ones(300, dtype=bool), 3, 10, rng, allowed)
    assert not hidden[:200].any() and hidden.sum() == 30
    assert not hide_runs(np.ones(10, dtype=bool), 3, 5, rng, np.zeros(10, dtype=bool)).any()


def test_fill_checks_pass_when_era5_has_the_station_shape(monkeypatch):
    import weather_odds.checks as checks

    monkeypatch.setattr(checks, "TEST_YEARS", (2019, 2020))
    monkeypatch.setattr(checks, "GAPS_PER_LENGTH", 30)
    monkeypatch.setattr(checks, "LONG_GAPS", (1, 3))
    monkeypatch.setattr(checks, "HIDDEN_YEAR", 2019)
    era5, station, _, _ = sources("2015-01-01", "2021-01-01")
    out = fill_checks(station["temperature"], era5, config(), seed=0)
    assert [c.section for c in out] == ["fills"] * 4
    assert all(c.passed for c in out), [c.value for c in out]


def test_years_are_listed_as_ranges():
    assert _years([1997, 1998, 1999, 2003, 2012, 2013]) == "1997-1999, 2003, 2012-2013"
    assert _years([]) == ""


def test_markdown_report():
    report = to_markdown(
        [
            Check("fills", "A fill", "error 1 °C", "≤ 2 °C", True),
            Check("fills", "Another fill", "error 3 °C", "≤ 2 °C", False),
            Check("station", "A number", "5%", "5%", True),
            Check("station", "Context", "7%", "for information"),
        ]
    )
    assert "| Another fill | error 3 °C | ≤ 2 °C | **fail**: not used |" in report
    assert "| Context | 7% | for information | info |" in report
    assert report.index("### Filling") < report.index("### Against the station")
