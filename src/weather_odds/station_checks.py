"""The tables compared with the measurements (milestone 3, #17): the numbers of docs/research/all-sources.md.

`weather-odds check` runs these after the gap-fill tests (weather_odds.checks)
and prints the report written up in docs/research/table-checks.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from weather_odds.cache import Cache
from weather_odds.config import Config
from weather_odds.table import Tables, airport_days, build, daily_sum, local_dates, wet_day_thresholds
from weather_odds.temperature import era5_correction

HIDDEN_YEAR = 1997  # the gap plan's test for filling 1996: hide 1997 and fill it from corrected ERA5


@dataclass(frozen=True)
class Comparison:
    name: str
    value: str
    expected: str = ""
    passed: bool | None = None  # None: for information


def compare_with_station(config: Config, today: date | None = None) -> list[Comparison]:
    """Build the tables from the cache and compare them with the measurements."""
    tables = build(config, today, log=lambda _: None)
    cache = Cache(config.data.cache_dir, config.location.slug)
    sources = {name: cache.load_table(name) for name in ("era5", "meteostat", "airport", "gsod", "nimh")}
    out = station_checks(tables, sources)
    out.append(whole_year(sources["meteostat"]["temperature"], sources["era5"]["temperature"], HIDDEN_YEAR))
    return out


def whole_year(station: pd.Series, era5: pd.Series, year: int) -> Comparison:
    """Hide a year and fill it from ERA5 corrected to the station, as 1996 could be (D43, D47)."""
    rows = (era5.index.year >= year - 3) & (era5.index.year <= year + 3)
    era5 = era5[rows].sort_index()
    measured = station.reindex(era5.index)
    hidden = measured.where(era5.index.year != year)
    filled = era5 + era5_correction(hidden.tz_convert("UTC"), era5.tz_convert("UTC")).to_numpy()
    in_year = era5.index.year == year
    day = local_dates(era5.index[in_year])
    complete = measured[in_year].groupby(day).count() >= 23
    true_max = measured[in_year].groupby(day).max()[complete]
    fill_max = filled[in_year].groupby(day).max()[complete]
    diff = fill_max - true_max

    def spread(s: pd.Series) -> float:
        return float((s - s.groupby(s.index.month).transform("mean")).std())

    ratio = spread(fill_max) / spread(true_max)
    return Comparison(
        f"Whole year filled from corrected ERA5 ({year} hidden; how 1996 could be filled)",
        f"daily maximum error {diff.abs().mean():.2f} °C, bias {diff.mean():+.2f} °C; "
        f"day-to-day range {ratio:.0%} of the station's",
        "range near 100%: not met, so 1996 stays out (D47)",
    )


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


def station_checks(tables: Tables, sources: dict[str, pd.DataFrame]) -> list[Comparison]:
    era5, gsod, nimh, airport = sources["era5"], sources["gsod"], sources["nimh"], sources["airport"]
    out = []
    e5 = era5["temperature"].dropna()
    day = local_dates(e5.index)
    e5_max = e5.groupby(day).max()[e5.groupby(day).count() >= 23]
    station_max = gsod["tmax"].dropna()
    for (start, end), (bias0, mae0, corr0) in ALL_SOURCES_TMAX.items():
        j = pd.concat([station_max.rename("st"), e5_max.rename("x")], axis=1, sort=True).dropna().loc[start:end]
        d = j["x"] - j["st"]
        bias, mae, corr = float(d.mean()), float(d.abs().mean()), float(j.corr().iloc[0, 1])
        out.append(
            Comparison(
                f"ERA5 daily maximum minus the station's, {start[:4]}-{end[:4]} ({len(j)} days)",
                f"bias {bias:+.1f} °C, difference {mae:.2f} °C, correlation {corr:.3f}",
                f"{bias0:+.1f} °C, {mae0:.2f} °C, {corr0:.3f}",
                _close(bias, bias0, 0.1) and _close(mae, mae0, 0.05) and _close(corr, corr0, 0.005),
            )
        )
    j = (
        pd.concat([station_max.rename("st"), tables.daily["tmax"].rename("x")], axis=1, sort=True)
        .dropna()
        .loc["1997":"2025"]
    )
    d = j["x"] - j["st"]
    out.append(
        Comparison(
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
            [station.rename("st"), (as_research >= 1.0).rename("old"), (model >= 1.0).rename("x")], axis=1, sort=True
        ).dropna()
        j = j.astype(bool)
        agree = float((j["old"] == j["st"]).mean())
        out.append(
            Comparison(
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
        j = (
            pd.concat([station.rename("st"), tables.daily["wet"].rename("cal")], axis=1, sort=True)
            .dropna()
            .astype(bool)
        )
        j = j.loc[f"{start}" : f"{end}"]
        out.append(
            Comparison(
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
        Comparison(
            f"Wet-day thresholds by month (mm), calibrated on NOAA GSOD {first}-{last}",
            " ".join(f"{v:.1f}" for v in old) + "; with the table's hours " + " ".join(f"{v:.1f}" for v in thresholds),
            " ".join(f"{v:.1f}" for v in ALL_SOURCES_THRESHOLDS),
            bool(np.all(np.abs(old - np.array(ALL_SOURCES_THRESHOLDS)) <= 0.05)),
        )
    )
    recent = nimh["precipitation"].loc["2022":"2025"]
    out.append(rounded_nimh_check(model, gsod["precipitation"].loc[f"{first}" : f"{last}"].dropna(), recent))
    try:
        old = wet_day_thresholds(as_research, recent).to_numpy()
        new = wet_day_thresholds(model, recent).to_numpy()
        value = " ".join(f"{v:.1f}" for v in old) + "; with the table's hours " + " ".join(f"{v:.1f}" for v in new)
    except ValueError:
        value = "no NIMH data for 2022-2025"
    out.append(
        Comparison(
            "The same thresholds calibrated on NIMH 2022-2025 (4 years, for information)",
            value,
            "0.8 2.5 1.4 1.6 1.1 1.7 0.9 0.4 0.7 1.2 1.4 1.0",
        )
    )

    rain_hour = tables.hourly["rain_seen"]
    for (start, end), (obs0, model0, hit0, far0) in ALL_SOURCES_HOURLY_RAIN.items():
        j = pd.concat([rain_hour.rename("obs"), (era5["precipitation"] >= 0.2).rename("x")], axis=1, sort=True)
        j = j.loc[start:end].dropna().astype(bool)
        obs, x = j["obs"], j["x"]
        hit, far = float(x[obs].mean()), float((~obs)[x].mean())
        out.append(
            Comparison(
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
        Comparison(
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
        Comparison(
            f"Days with thunder by month in the table: only years with thunder reports ({_years(years)})",
            " ".join(f"{v:.0%}" for v in by_month),
            "higher than above: 2015-2018 have no thunder reports and no longer count as thunder-free",
        )
    )
    return out


def rounded_nimh_check(model: pd.Series, gsod: pd.Series, nimh: pd.Series) -> Comparison:
    """Calibrate on NOAA at 0.5 mm, which is what NIMH's rounded 1 mm means, and check on NIMH's years (D51)."""
    if nimh.dropna().empty:
        return Comparison("Wet-day thresholds across the periods (NIMH)", "no NIMH data for 2022-2025")
    thresholds = wet_day_thresholds(model, gsod, wet_mm=0.5)
    days = nimh.dropna().index
    era5 = model.reindex(days)
    era5_wet = era5 >= thresholds.reindex(days.month).to_numpy()
    station_wet = nimh.loc[days] >= 1
    first, last = gsod.index.year.min(), gsod.index.year.max()
    return Comparison(
        f"ERA5 calibrated on NOAA GSOD {first}-{last} at 0.5 mm, checked on NIMH {days.year.min()}-{days.year.max()} "
        "(NIMH rounds to whole mm, so its 1 mm is 0.5 mm)",
        f"ERA5 {era5_wet.mean():.1%}, NIMH {station_wet.mean():.1%} (agree on {(era5_wet == station_wet).mean():.0%})",
        "within 1 point: the periods agree once NIMH's rounding is allowed for",
        _close(float(era5_wet.mean()), float(station_wet.mean()), 0.01),
    )


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


def to_markdown(comparisons: list[Comparison]) -> str:
    marks = {True: "matches", False: "**differs**", None: "info"}
    lines = ["| Check | Result | all-sources.md / expected | |", "|---|---|---|---|"]
    lines += [f"| {c.name} | {c.value} | {c.expected} | {marks[c.passed]} |" for c in comparisons]
    return "\n".join(lines)
