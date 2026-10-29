"""Day-of-year statistics shared by the research scripts (phase-0 research).

Series are mapped to a 365-day calendar (29 February dropped) and arranged as a
year x day-of-year matrix; "pooling" averages each date with its +-w
neighbouring days over all years.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def doy365(index: pd.DatetimeIndex) -> np.ndarray:
    """Day of year 1..365 with 29 Feb removed (callers drop those rows)."""
    doy = index.dayofyear.to_numpy()
    leap_after_feb = index.is_leap_year & (index.month > 2)
    return np.where(leap_after_feb, doy - 1, doy)


def to_matrix(series: pd.Series, years: tuple[int, int]) -> pd.DataFrame:
    """Year x day-of-year matrix (NaN where missing)."""
    s = series.dropna()
    s = s[(s.index.year >= years[0]) & (s.index.year <= years[1])]
    s = s[~((s.index.month == 2) & (s.index.day == 29))]
    frame = pd.DataFrame({"year": s.index.year, "doy": doy365(s.index), "v": s.to_numpy(dtype=float)})
    return frame.pivot_table(index="year", columns="doy", values="v").reindex(columns=range(1, 366))


def pooled(matrix: np.ndarray, w: int) -> np.ndarray:
    """Mean over all years and the +-w surrounding days (circular), ignoring NaN."""
    total = np.zeros(365)
    count = np.zeros(365)
    vals = np.nan_to_num(matrix, nan=0.0)
    ok = (~np.isnan(matrix)).astype(float)
    for shift in range(-w, w + 1):
        total += np.roll(vals, -shift, axis=1).sum(axis=0)
        count += np.roll(ok, -shift, axis=1).sum(axis=0)
    with np.errstate(invalid="ignore"):
        return total / count


def harmonic_baseline(values: np.ndarray, k: int = 3) -> np.ndarray:
    """Smooth seasonal curve: least-squares fit of k annual harmonics to a 365-day curve."""
    t = 2 * np.pi * np.arange(365) / 365
    cols = [np.ones(365)] + [f(j * t) for j in range(1, k + 1) for f in (np.sin, np.cos)]
    design = np.column_stack(cols)
    ok = ~np.isnan(values)
    coef, *_ = np.linalg.lstsq(design[ok], values[ok], rcond=None)
    return design @ coef


def window_mean(curve: np.ndarray, first: str, last: str) -> float:
    a, b = (doy365(pd.DatetimeIndex([f"2001-{d}"]))[0] - 1 for d in (first, last))
    return float(np.nanmean(curve[a:b + 1]))
