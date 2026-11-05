"""Tests of the gap fills on real data: hide hours the station measured, fill them, compare (D46).

A fill is used only if it beats the simplest alternative (a straight line
between readings, or plain ERA5) and its mean error stays within MAX_BIAS.
`weather-odds check` runs these on the cached data; the results are in
docs/research/gap-fills.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from weather_odds.temperature import fill_temperature

MAX_BIAS = 0.3  # deg C
HOURLY_YEAR = 0.9  # share of hours a year needs to count as measured hourly


@dataclass(frozen=True)
class Check:
    name: str
    baseline: str
    hours: int
    mae: float
    bias: float
    baseline_mae: float
    baseline_bias: float
    notes: str = ""

    @property
    def passed(self) -> bool:
        return self.mae < self.baseline_mae and abs(self.bias) <= MAX_BIAS


def check_fills(station: pd.Series, era5: pd.Series, seed: int = 1) -> list[Check]:
    """The three temperature fills, each tested on hours the station measured."""
    tz = station.index.tz
    station, era5 = station.tz_convert("UTC"), era5.tz_convert("UTC")
    index = pd.date_range(
        min(station.index.min(), era5.index.min()), max(station.index.max(), era5.index.max()), freq="h"
    )
    station, era5 = station.reindex(index), era5.reindex(index)
    counts = station.groupby(index.year).count()
    hourly_years = counts[counts >= HOURLY_YEAR * 8760].index
    in_hourly = index.year.isin(hourly_years) & station.notna().to_numpy()
    rng = np.random.default_rng(seed)

    def hide_runs(n: int, lengths: tuple[int, int]) -> np.ndarray:
        hidden = np.zeros(len(index), bool)
        for start in rng.choice(np.flatnonzero(in_hourly), n, replace=False):
            hidden[start : start + int(rng.integers(*lengths))] = True
        return hidden & in_hourly

    def compare(
        name: str, baseline_name: str, hidden: np.ndarray, baseline: Callable[[pd.Series], pd.Series], notes: str = ""
    ) -> Check:
        masked = station.where(~hidden)
        filled = fill_temperature(masked, era5)["temperature"].tz_convert("UTC")
        error, base = (filled - station)[hidden], (baseline(masked) - station)[hidden]
        both = error.notna() & base.notna()
        error, base = error[both], base[both]
        return Check(name, baseline_name, int(both.sum()), *_stats(error), *_stats(base), notes)

    def straight_line(masked: pd.Series) -> pd.Series:
        return masked.interpolate(limit_area="inside")

    checks = [
        compare("gaps of 1-6 hours", "straight line", hide_runs(3000, (1, 7)), straight_line),
        compare("gaps of 1-7 days", "plain ERA5", hide_runs(300, (24, 7 * 24 + 1)), lambda masked: era5),
    ]
    # Every other hourly year thinned to 8 readings a day, as before 1997; the others keep the daily curve.
    thinned_years = hourly_years[1::2]
    thin = np.asarray(index.year.isin(thinned_years) & (index.hour % 3 != 0)) & in_hourly
    masked = station.where(~thin)
    filled = fill_temperature(masked, era5)["temperature"].tz_convert("UTC")
    days = index.year.isin(thinned_years)
    notes = _daily_extremes(station[days], filled[days], masked[days], tz)
    checks.append(compare("3-hourly years rebuilt", "straight line", thin, straight_line, notes))
    return checks


def _stats(error: pd.Series) -> tuple[float, float]:
    return round(float(error.abs().mean()), 2), round(float(error.mean()), 2)


def _daily_extremes(station: pd.Series, filled: pd.Series, readings: pd.Series, tz) -> str:
    """Bias of the daily maximum and minimum, rebuilt and from the 8 readings alone (local days)."""

    def by_day(values: pd.Series):
        local = values.tz_convert(tz)
        return values.groupby(local.index.tz_localize(None).normalize())

    full = by_day(station).count() >= 23
    parts = []
    for extreme in ("max", "min"):
        truth = getattr(by_day(station), extreme)()[full]
        rebuilt = (getattr(by_day(filled), extreme)()[full] - truth).mean()
        eight = (getattr(by_day(readings), extreme)()[full] - truth).mean()
        parts.append(f"daily {extreme} bias {rebuilt:+.2f} (8 readings alone {eight:+.2f})")
    return "; ".join(parts)


def report(checks: list[Check]) -> str:
    lines = [
        "| Fill | Hours | Error | Bias | Baseline | Baseline error | Baseline bias | Passed |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in checks:
        lines.append(
            f"| {c.name} | {c.hours:,} | {c.mae:.2f} | {c.bias:+.2f} | {c.baseline} | {c.baseline_mae:.2f} | "
            f"{c.baseline_bias:+.2f} | {'yes' if c.passed else 'no'} |"
        )
    lines += [f"- {c.name}: {c.notes}" for c in checks if c.notes]
    return "\n".join(lines)
