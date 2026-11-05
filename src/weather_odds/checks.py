"""Checks of the tables against the measurements (milestone 3, #17), and the hidden-data test of every fill.

`weather-odds check` runs both and prints a report:

- **Fills** (gap plan): measured station hours are hidden, filled the way the
  table fills real gaps, and compared with what was measured. A fill is used
  only if its test passes (criteria in FILL_CRITERIA).
- **Against the station**: the numbers of docs/research/all-sources.md,
  recomputed from the cached sources and the built table.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

import numpy as np
import pandas as pd

from weather_odds.cache import Cache
from weather_odds.config import Config
from weather_odds.fill import FillSettings, fill_temperature
from weather_odds.stats.scale import day_scores
from weather_odds.sun import daylight
from weather_odds.table import (
    Tables,
    airport_days,
    build,
    daily_sum,
    fill_settings,
    local_dates,
    wet_day_thresholds,
)

TEST_YEARS = (1997, 2025)  # hourly station years used to test the fills
SHORT_GAPS = (1, 2, 3, 6, 12)  # hours hidden at a time
LONG_GAPS = (1, 7, 31)  # days hidden at a time
GAPS_PER_LENGTH = 300
HIDDEN_YEAR = 1997  # the gap plan's test for filling 1996: hide 1997 and fill it the same way

# Pass criteria of each fill test, in deg C (score points for the scale).
FILL_CRITERIA = {
    "short": {"hour_mae": 1.5, "hour_bias": 0.2},
    "long": {"hour_mae": 1.5, "hour_bias": 0.2, "tmax_bias": 0.3},
    "three_hourly": {"tmax_mae": 0.5, "tmax_bias": 0.2, "score_mae": 3.0},
    "year": {"tmax_mae": 1.3, "tmax_bias": 0.3, "spread_low": 0.95, "spread_high": 1.05},
}


@dataclass(frozen=True)
class Check:
    section: str
    name: str
    value: str
    expected: str = ""
    passed: bool | None = None  # None: for information


def run_checks(config: Config, today: date | None = None, seed: int = 0) -> list[Check]:
    """Build the tables from the cache and run every check."""
    tables = build(config, today, log=lambda _: None)
    cache = Cache(config.data.cache_dir, config.location.slug)
    sources = {name: cache.load_table(name) for name in ("era5", "meteostat", "airport", "gsod", "nimh")}
    checks = fill_checks(sources["meteostat"]["temperature"], sources["era5"], config, seed)
    return checks + station_checks(tables, sources)


# ---------------------------------------------------------------------------
# fills


def _test_span(series: pd.Series) -> pd.Series:
    """The test years and a few before them, for the corrections from nearby years."""
    first, last = TEST_YEARS
    return series[(series.index.year >= first - 4) & (series.index.year <= last)]


def hide_runs(
    measured: np.ndarray, length: int, count: int, rng: np.random.Generator, allowed: np.ndarray
) -> np.ndarray:
    """Up to `count` non-overlapping runs of `length` measured positions, with measured neighbours on both sides."""
    hidden = np.zeros(len(measured), dtype=bool)
    candidates = np.flatnonzero(allowed[1 : len(allowed) - length]) + 1
    if len(candidates) == 0:
        return hidden
    cumulative = np.concatenate([[0], np.cumsum(measured)])
    found = 0
    for start in rng.permutation(candidates):
        end = start + length
        if cumulative[end + 1] - cumulative[start - 1] != length + 2:
            continue
        if hidden[max(start - 2, 0) : end + 2].any():
            continue
        hidden[start:end] = True
        found += 1
        if found == count:
            break
    return hidden


def _errors(filled: pd.Series, truth: pd.Series, hidden: np.ndarray) -> tuple[float, float]:
    diff = (filled[hidden] - truth[hidden]).dropna()
    return float(diff.abs().mean()), float(diff.mean())


def _daily_extremes(hourly: pd.Series, days: pd.Index) -> tuple[pd.Series, pd.Series]:
    day = local_dates(hourly.index)
    return hourly.groupby(day).max().reindex(days), hourly.groupby(day).min().reindex(days)


def fill_checks(station: pd.Series, era5: pd.DataFrame, config: Config, seed: int = 0) -> list[Check]:
    rng = np.random.default_rng(seed)
    settings = fill_settings(config)
    e5 = _test_span(era5["temperature"].dropna().sort_index())
    measured = station.reindex(e5.index)
    in_years = np.asarray(e5.index.year >= TEST_YEARS[0])
    have = measured.notna().to_numpy()
    out = []

    # short gaps: ERA5's shape between readings
    hidden = np.zeros(len(e5), dtype=bool)
    for length in SHORT_GAPS:
        hidden |= hide_runs(have & ~hidden, length, GAPS_PER_LENGTH, rng, in_years)
    filled = fill_temperature(measured[~hidden], e5, settings)["temperature"]
    mae, bias = _errors(filled, measured, hidden)
    c = FILL_CRITERIA["short"]
    out.append(
        Check(
            "fills",
            f"Short gaps ({min(SHORT_GAPS)}-{max(SHORT_GAPS)} h hidden, {hidden.sum()} hours, "
            f"{TEST_YEARS[0]}-{TEST_YEARS[1]})",
            f"error {mae:.2f} °C, bias {bias:+.2f} °C",
            f"error ≤ {c['hour_mae']} °C, bias within ±{c['hour_bias']} °C",
            mae <= c["hour_mae"] and abs(bias) <= c["hour_bias"],
        )
    )

    # longer gaps: ERA5 with the typical difference of nearby years
    hidden = np.zeros(len(e5), dtype=bool)
    for days in LONG_GAPS:
        hidden |= hide_runs(have & ~hidden, days * 24, GAPS_PER_LENGTH // 10, rng, in_years)
    filled = fill_temperature(measured[~hidden], e5, settings)["temperature"]
    mae, bias = _errors(filled, measured, hidden)
    day = local_dates(e5.index)
    whole = pd.Series(hidden, index=e5.index).groupby(day).all() & measured.groupby(day).count().eq(
        measured.groupby(day).size()
    )
    days_hidden = whole.index[whole]
    true_max, _ = _daily_extremes(measured, days_hidden)
    fill_max, _ = _daily_extremes(filled, days_hidden)
    tmax_bias = float((fill_max - true_max).mean())
    c = FILL_CRITERIA["long"]
    out.append(
        Check(
            "fills",
            f"Longer gaps ({', '.join(str(d) for d in LONG_GAPS)} days hidden, {len(days_hidden)} whole days)",
            f"error {mae:.2f} °C, bias {bias:+.2f} °C; daily maximum bias {tmax_bias:+.2f} °C",
            f"error ≤ {c['hour_mae']} °C, bias within ±{c['hour_bias']} °C, daily maximum within ±{c['tmax_bias']} °C",
            mae <= c["hour_mae"] and abs(bias) <= c["hour_bias"] and abs(tmax_bias) <= c["tmax_bias"],
        )
    )

    out.append(three_hourly_check(measured, era5, e5, settings, config, in_years))
    out.append(year_check(station, e5, settings, HIDDEN_YEAR))
    return out


def three_hourly_check(
    measured: pd.Series, era5: pd.DataFrame, e5: pd.Series, settings: FillSettings, config: Config, in_years: np.ndarray
) -> Check:
    """Thin the hourly years to the 3-hourly readings of before 1997, rebuild them and compare."""
    utc_hour = e5.index.tz_convert("UTC").hour
    thinned = measured.where((utc_hour % 3 == 0) | ~in_years)
    filled = fill_temperature(thinned.dropna(), e5, settings)["temperature"]
    day = local_dates(e5.index)
    full = (
        measured.groupby(day).count().eq(measured.groupby(day).size())
        & pd.Series(in_years, index=e5.index).groupby(day).all()
    )
    days = full.index[full]
    true_max, true_min = _daily_extremes(measured, days)
    fill_max, fill_min = _daily_extremes(filled, days)
    tmax = fill_max - true_max
    tmin = fill_min - true_min

    rest = era5[["precipitation", "wind_gust"]].reindex(e5.index)
    light = daylight(e5.index, config.location.latitude, config.location.longitude)
    on_days = pd.Series(day, index=e5.index).isin(days).to_numpy()
    rows = light & on_days
    truth = rest[rows].assign(temperature=measured[rows])
    rebuilt = rest[rows].assign(temperature=filled[rows])
    score_true = day_scores(truth, config.scale)
    score_fill = day_scores(rebuilt, config.scale)
    score_mae = float((score_fill - score_true).abs().mean())
    classes = config.scale.classes
    edges = [classes.poor, classes.fair, classes.good, classes.great]
    same_class = float((np.digitize(score_fill, edges) == np.digitize(score_true, edges)).mean())
    c = FILL_CRITERIA["three_hourly"]
    return Check(
        "fills",
        f"3-hourly readings rebuilt ({len(days)} days of {TEST_YEARS[0]}-{TEST_YEARS[1]} thinned to every 3 hours)",
        f"daily maximum error {tmax.abs().mean():.2f} °C, bias {tmax.mean():+.2f} °C; "
        f"minimum bias {tmin.mean():+.2f} °C; daylight score error {score_mae:.1f} points, same class {same_class:.0%}",
        f"maximum error ≤ {c['tmax_mae']} °C, bias within ±{c['tmax_bias']} °C, "
        f"score error ≤ {c['score_mae']:g} points",
        bool(tmax.abs().mean() <= c["tmax_mae"] and abs(tmax.mean()) <= c["tmax_bias"] and score_mae <= c["score_mae"]),
    )


def year_check(station: pd.Series, e5: pd.Series, settings: FillSettings, year: int) -> Check:
    """Hide a whole year and fill it like 1996 would be (the D43 option)."""
    hidden = station[station.index.year != year]
    filled = fill_temperature(hidden, e5, replace(settings, fill_long_gaps=True))["temperature"]
    measured = station.reindex(e5.index)
    rows = e5.index.year == year
    day = local_dates(e5.index[rows])
    complete = measured[rows].groupby(day).count() >= 23
    true_max = measured[rows].groupby(day).max()[complete]
    fill_max = filled[rows].groupby(day).max()[complete]
    diff = fill_max - true_max

    def spread(s: pd.Series) -> float:
        return float((s - s.groupby(s.index.month).transform("mean")).std())

    ratio = spread(fill_max) / spread(true_max)
    c = FILL_CRITERIA["year"]
    passed = abs(diff.mean()) <= c["tmax_bias"] and diff.abs().mean() <= c["tmax_mae"]
    passed = passed and c["spread_low"] <= ratio <= c["spread_high"]
    return Check(
        "fills",
        f"Whole year without station data ({year} hidden; the option for 1996, D43)",
        f"daily maximum error {diff.abs().mean():.2f} °C, bias {diff.mean():+.2f} °C; "
        f"day-to-day range {ratio:.0%} of the station's",
        f"error ≤ {c['tmax_mae']} °C, bias within ±{c['tmax_bias']} °C, "
        f"range {c['spread_low']:.0%}-{c['spread_high']:.0%}",
        bool(passed),
    )


# ---------------------------------------------------------------------------
# against the station (docs/research/all-sources.md)

ALL_SOURCES_TMAX = {  # period: (bias, mean absolute difference, correlation) of ERA5 against the station
    ("1991-01-01", "2021-06-30"): (0.0, 1.24, 0.987),
    ("2017-01-01", "2025-12-31"): (0.6, 1.20, 0.988),
}
ALL_SOURCES_WET = {  # period: (station, ERA5 at 1 mm, agreement)
    "gsod": (("1985", "1999"), 0.166, 0.230, 0.84),
    "nimh": (("2022", "2025"), 0.203, 0.220, 0.81),
}
STATION_NAMES = {"gsod": "NOAA GSOD", "nimh": "NIMH"}
CALIBRATION_YEARS = (1973, 1999)  # as in all-sources.md
ALL_SOURCES_THRESHOLDS = [1.4, 1.7, 2.1, 2.0, 1.9, 1.9, 1.7, 2.2, 1.7, 1.2, 1.6, 1.4]
ALL_SOURCES_HOURLY_RAIN = {  # period: (airport share, ERA5 share, hit rate, false alarm ratio)
    ("2012-01-01", "2021-06-30"): (0.091, 0.093, 0.53, 0.48),
    ("2017-01-01", "2025-12-31"): (0.092, 0.088, 0.54, 0.43),
}
ALL_SOURCES_THUNDER_DAYS = [0.01, 0.00, 0.01, 0.06, 0.17, 0.24, 0.14, 0.13, 0.05, 0.02, 0.01, 0.00]


def _close(value: float, expected: float, tolerance: float) -> bool:
    return bool(abs(value - expected) <= tolerance + 1e-9)


def station_checks(tables: Tables, sources: dict[str, pd.DataFrame]) -> list[Check]:
    era5, gsod, nimh, airport = sources["era5"], sources["gsod"], sources["nimh"], sources["airport"]
    out = []
    e5 = era5["temperature"].dropna()
    day = local_dates(e5.index)
    e5_max = e5.groupby(day).max()[e5.groupby(day).count() >= 23]
    station_max = gsod["tmax"].dropna()
    for (start, end), (bias0, mae0, corr0) in ALL_SOURCES_TMAX.items():
        j = pd.concat([station_max.rename("st"), e5_max.rename("x")], axis=1).dropna().loc[start:end]
        d = j["x"] - j["st"]
        bias, mae, corr = float(d.mean()), float(d.abs().mean()), float(j.corr().iloc[0, 1])
        out.append(
            Check(
                "station",
                f"ERA5 daily maximum minus the station's, {start[:4]}-{end[:4]} ({len(j)} days)",
                f"bias {bias:+.1f} °C, difference {mae:.2f} °C, correlation {corr:.3f}",
                f"{bias0:+.1f} °C, {mae0:.2f} °C, {corr0:.3f}",
                _close(bias, bias0, 0.1) and _close(mae, mae0, 0.05) and _close(corr, corr0, 0.005),
            )
        )
    j = pd.concat([station_max.rename("st"), tables.daily["tmax"].rename("x")], axis=1).dropna().loc["1997":"2025"]
    d = j["x"] - j["st"]
    out.append(
        Check(
            "station",
            f"Table daily maximum (hourly readings) minus the station's daily maximum, 1997-2025 ({len(j)} days)",
            f"bias {d.mean():+.2f} °C, difference {d.abs().mean():.2f} °C",
            "slightly negative: the true maximum falls between the hourly readings",
        )
    )

    # The research summed ERA5's rain stamped at the end of each hour as if stamped at its start, so its
    # days run one hour early. Its numbers are reproduced that way; the table uses the hours as they are.
    model = daily_sum(era5["precipitation"])
    as_research = daily_sum(era5["precipitation"].shift(1, freq="h"))
    for name, ((start, end), share0, era0, agree0) in ALL_SOURCES_WET.items():
        station = (sources[name]["precipitation"].dropna() >= 1.0).loc[start:end]
        j = pd.concat(
            [station.rename("st"), (as_research >= 1.0).rename("old"), (model >= 1.0).rename("x")], axis=1
        ).dropna()
        j = j.astype(bool)
        agree = float((j["old"] == j["st"]).mean())
        out.append(
            Check(
                "station",
                f"Wet days (≥ 1 mm), {start}-{end}, station = {STATION_NAMES[name]} ({len(j)} days)",
                f"station {j['st'].mean():.1%}, ERA5 {j['old'].mean():.1%} (agrees on {agree:.0%}); "
                f"with the table's hours ERA5 {j['x'].mean():.1%} ({(j['x'] == j['st']).mean():.0%})",
                f"{share0:.1%}, {era0:.1%} ({agree0:.0%})",
                _close(j["st"].mean(), share0, 0.0025)
                and _close(j["old"].mean(), era0, 0.0025)
                and _close(agree, agree0, 0.005),
            )
        )
    first, last = CALIBRATION_YEARS
    station = (gsod["precipitation"].dropna() >= 1.0).loc[f"{first}" : f"{last}"]
    for (start, end), expected in ((CALIBRATION_YEARS, "near the station"), (("1985", "1999"), "for information")):
        j = pd.concat([station.rename("st"), tables.daily["wet"].rename("cal")], axis=1).dropna().astype(bool)
        j = j.loc[f"{start}" : f"{end}"]
        out.append(
            Check(
                "station",
                f"Calibrated wet days in the table, {start}-{end}",
                f"{j['cal'].mean():.1%}, station {j['st'].mean():.1%} "
                f"(they agree on {(j['cal'] == j['st']).mean():.0%} of days)",
                expected,
                _close(j["cal"].mean(), j["st"].mean(), 0.005) if expected.startswith("near") else None,
            )
        )
    thresholds = pd.Series(tables.info["wet_day_thresholds_mm"]).astype(float).to_numpy()
    old = wet_day_thresholds(as_research, gsod["precipitation"].loc[f"{first}" : f"{last}"].dropna()).to_numpy()
    out.append(
        Check(
            "station",
            f"Wet-day thresholds by month (mm), calibrated on NOAA GSOD {first}-{last}",
            " ".join(f"{v:.1f}" for v in old) + "; with the table's hours " + " ".join(f"{v:.1f}" for v in thresholds),
            " ".join(f"{v:.1f}" for v in ALL_SOURCES_THRESHOLDS),
            bool(np.all(np.abs(old - np.array(ALL_SOURCES_THRESHOLDS)) <= 0.05)),
        )
    )
    recent = nimh["precipitation"].loc["2022":"2025"]
    old = wet_day_thresholds(as_research, recent).to_numpy()
    new = wet_day_thresholds(model, recent).to_numpy()
    out.append(
        Check(
            "station",
            "The same thresholds calibrated on NIMH 2022-2025 (4 years, for information)",
            " ".join(f"{v:.1f}" for v in old) + "; with the table's hours " + " ".join(f"{v:.1f}" for v in new),
            "0.8 2.5 1.4 1.6 1.1 1.7 0.9 0.4 0.7 1.2 1.4 1.0",
        )
    )

    rain_hour = tables.hourly["rain_seen"]
    for (start, end), (obs0, model0, hit0, far0) in ALL_SOURCES_HOURLY_RAIN.items():
        j = pd.concat([rain_hour.rename("obs"), (era5["precipitation"] >= 0.2).rename("x")], axis=1)
        j = j.loc[start:end].dropna().astype(bool)
        obs, x = j["obs"], j["x"]
        hit, far = float(x[obs].mean()), float((~obs)[x].mean())
        out.append(
            Check(
                "station",
                f"Rainy hours, airport reports vs ERA5 ≥ 0.2 mm, {start[:4]}-{end[:4]} ({len(j)} hours)",
                f"airport {obs.mean():.1%}, ERA5 {x.mean():.1%}; ERA5 rains in {hit:.0%} of the airport's rainy hours, "
                f"{far:.0%} of ERA5's rainy hours are dry at the airport",
                f"{obs0:.1%}, {model0:.1%}; {hit0:.0%}, {far0:.0%}",
                _close(obs.mean(), obs0, 0.003)
                and _close(x.mean(), model0, 0.003)
                and _close(hit, hit0, 0.015)
                and _close(far, far0, 0.015),
            )
        )

    days = airport_days(airport)["thunder"].loc["2012":"2025"].dropna().astype(bool)
    as_research = days.groupby(days.index.month).mean().to_numpy()
    out.append(
        Check(
            "station",
            "Days with thunder by month, airport 2012-2025, every day with reports (as in all-sources.md)",
            " ".join(f"{v:.0%}" for v in as_research),
            " ".join(f"{v:.0%}" for v in ALL_SOURCES_THUNDER_DAYS),
            bool(np.all(np.abs(as_research - np.array(ALL_SOURCES_THUNDER_DAYS)) <= 0.01)),
        )
    )
    table = tables.daily.loc["2012":"2025"]
    table = table[table["thunder_source"] == "airport"]["thunder"].astype(bool)
    by_month = table.groupby(table.index.month).mean().to_numpy()
    years = sorted(set(table.index.year))
    out.append(
        Check(
            "station",
            f"Days with thunder by month in the table: only years with thunder reports ({_years(years)})",
            " ".join(f"{v:.0%}" for v in by_month),
            "higher than above: 2015-2018 have no thunder reports and no longer count as thunder-free",
        )
    )
    return out


def _years(years: list[int]) -> str:
    """1997, 1998, 1999, 2003 -> '1997-1999, 2003'."""
    parts, start, prev = [], None, None
    for y in years:
        if start is None:
            start = prev = y
        elif y == prev + 1:
            prev = y
        else:
            parts.append(f"{start}-{prev}" if prev > start else f"{start}")
            start = prev = y
    if start is not None:
        parts.append(f"{start}-{prev}" if prev > start else f"{start}")
    return ", ".join(parts)


def to_markdown(checks: list[Check]) -> str:
    titles = {"fills": "Filling the station's gaps (hidden data)", "station": "Against the station (all-sources.md)"}
    marks = {True: "pass", False: "**fail**", None: "info"}
    fill_marks = {**marks, False: "**fail**: not used"}
    lines = []
    for section, title in titles.items():
        rows = [c for c in checks if c.section == section]
        if not rows:
            continue
        lines += [f"### {title}", "", "| Check | Result | Expected | |", "|---|---|---|---|"]
        mark = fill_marks if section == "fills" else marks
        lines += [f"| {c.name} | {c.value} | {c.expected} | {mark[c.passed]} |" for c in rows]
        lines.append("")
    return "\n".join(lines)
