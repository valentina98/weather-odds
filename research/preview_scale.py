"""Preview of the proposed outdoor-weather scale for Plovdiv (phase-0 research,
follow-up to issue #5).

Every daylight hour gets a score from 0 (bad) to 100 (great) from temperature,
rain and wind gusts; a day's score is the mean over its daylight hours, capped
when the day's rain in those hours reaches 1 mm (at most Fair) or 5 mm (at most
Poor). The definition and thresholds are in docs/spec/methodology.md (section 4).
Thunder is not scored yet: ERA5 has no thunder variable.

Writes docs/research/img/scale-preview.png and docs/research/scale-preview.json;
the write-up is in docs/research/weather-scale.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import load_sources as src  # noqa: E402
from daystats import pooled, to_matrix  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "research" / "img"
OUT_JSON = ROOT / "docs" / "research" / "scale-preview.json"
LAT, LON = 42.1333, 24.75
REF = (1996, 2025)
POOL = 7

# Thresholds (defaults proposed in methodology section 4; all configurable)
COMFORT = (18.0, 26.0)  # deg C: no penalty inside this range
COLD_ZERO, HOT_ZERO = 0.0, 38.0  # deg C: temperature factor reaches 0
RAIN = ((0.2, 1.0), (1.0, 0.5), (np.inf, 0.2))  # (hourly mm below which, factor)
RAIN_CAPS = ((5.0, 39.0), (1.0, 59.0))  # (mm in the chosen hours from which, highest score)
GUST_OK, GUST_ZERO = 30.0, 75.0  # km/h
CLASSES = [(80, "Great", "#1a9850"), (60, "Good", "#91cf60"), (40, "Fair", "#fee08b"),
           (20, "Poor", "#fc8d59"), (0, "Bad", "#d73027")]
GOOD = 60

plt.rcParams.update({"figure.dpi": 110, "font.size": 9})


def daylight(utc: pd.DatetimeIndex) -> np.ndarray:
    """True for hours stamped between sunrise and sunset (NOAA approximation)."""
    doy = utc.dayofyear.to_numpy()
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
    half_day = np.degrees(np.arccos(-np.tan(np.radians(LAT)) * np.tan(decl))) / 15
    b = 2 * np.pi * (doy - 81) / 364
    eot_h = (9.87 * np.sin(2 * b) - 7.53 * np.cos(b) - 1.5 * np.sin(b)) / 60
    noon = 12 - LON / 15 - eot_h
    hour = utc.hour.to_numpy()
    return (hour >= noon - half_day) & (hour <= noon + half_day)


def temperature_factor(t: np.ndarray) -> np.ndarray:
    cold = np.clip((t - COLD_ZERO) / (COMFORT[0] - COLD_ZERO), 0, 1)
    hot = np.clip((HOT_ZERO - t) / (HOT_ZERO - COMFORT[1]), 0, 1)
    return np.minimum(cold, hot)


def rain_factor(p: np.ndarray) -> np.ndarray:
    out = np.full(p.shape, RAIN[-1][1])
    for limit, factor in reversed(RAIN):
        out = np.where(p < limit, factor, out)
    return out


def gust_factor(g: np.ndarray) -> np.ndarray:
    return np.clip((GUST_ZERO - g) / (GUST_ZERO - GUST_OK), 0, 1)


# ---------------------------------------------------------------------------
# hourly -> daily score

hourly = src.era5_hourly("copernicus_era5")
hourly = hourly[daylight(hourly.index.tz_convert("UTC"))]
factors = pd.DataFrame({
    "temperature": temperature_factor(hourly["temperature_2m"].to_numpy()),
    "rain": rain_factor(hourly["precipitation"].to_numpy()),
    "wind": gust_factor(hourly["wind_gusts_10m"].to_numpy()),
}, index=hourly.index)
hour_score = 100 * factors.prod(axis=1)
day = hour_score.index.tz_localize(None).normalize()
rain = hourly["precipitation"].groupby(day).sum()
score = hour_score.groupby(day).mean()
for limit, cap in RAIN_CAPS:
    score = score.where(rain < limit, np.minimum(score, cap))
score = score[hour_score.groupby(day).size() >= 8]

matrix = to_matrix(score, REF).to_numpy()
good = pooled(np.where(np.isnan(matrix), np.nan, matrix >= GOOD), POOL)
mean_score = pooled(matrix, POOL)

# Which factor costs the most points, by month
lost = (1 - factors).groupby(factors.index.month).mean().round(3)
days = pd.date_range("2001-01-01", "2001-12-31")
by_month = pd.DataFrame({"good": good, "mean": mean_score}, index=days).groupby(days.month).mean()
summary = {
    "reference_years": list(REF),
    "pooling_days": POOL,
    "chance_good_or_better_by_month": {int(m): round(float(v), 3) for m, v in by_month["good"].items()},
    "mean_score_by_month": {int(m): round(float(v), 1) for m, v in by_month["mean"].items()},
    "mean_factor_shortfall_by_month": {f: {int(m): float(v) for m, v in lost[f].items()} for f in lost},
    "good_or_better_share_by_daylight_rain": {
        label: round(float((score[mask] >= GOOD).mean()), 3)
        for label, mask in {"under 0.2 mm": rain < 0.2, "0.2-1 mm": (rain >= 0.2) & (rain < 1),
                            "1-5 mm": (rain >= 1) & (rain < 5), "5 mm or more": rain >= 5}.items()
        for mask in [mask.reindex(score.index)]},
    "class_share_all_days": {name: round(float(((matrix >= lo) & (matrix < hi)).sum() / np.isfinite(matrix).sum()), 3)
                             for (lo, name, _), hi in zip(CLASSES, [101, 80, 60, 40, 20])},
}
OUT_JSON.write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))

# ---------------------------------------------------------------------------
# chart: chance of a Good or Great day, month x day-of-month, like a calendar

grid = np.full((12, 31), np.nan)
for d, v in zip(days, good):
    grid[d.month - 1, d.day - 1] = v * 100
colors = {"cmap": "RdYlGn", "vmin": 0, "vmax": 100}  # continuous red -> yellow -> green
fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), gridspec_kw={"height_ratios": [3.2, 1]})
ax = axes[0]
im = ax.imshow(grid, aspect="auto", **colors)
ax.set_yticks(range(12))
ax.set_yticklabels([pd.Timestamp(2001, m, 1).strftime("%b") for m in range(1, 13)])
ax.set_xticks(range(0, 31, 2))
ax.set_xticklabels(range(1, 32, 2))
ax.set_xlabel("day of month")
ax.set_title(f"Plovdiv, daylight hours, ERA5 {REF[0]}-{REF[1]}: chance of a Good or Great day (±{POOL} days)")
fig.colorbar(im, ax=ax, label="% of past days", fraction=0.03, pad=0.01)

ax = axes[1]
weeks = pd.Series(good, index=days).groupby((np.arange(365) // 7).clip(max=51)).mean() * 100
ax.imshow(weeks.to_numpy()[None, :], aspect="auto", **colors)
for i, v in enumerate(weeks):
    ax.text(i, 0, f"{v:.0f}", ha="center", va="center", fontsize=6)
starts = [pd.Timestamp(2001, m, 1) for m in range(1, 13)]
ax.set_xticks([(s.day_of_year - 1) / 7 - 0.5 for s in starts])
ax.set_xticklabels([s.strftime("%b") for s in starts])
ax.set_yticks([])
ax.set_title("Same by week of the year (%)")
fig.tight_layout()
fig.savefig(IMG / "scale-preview.png")
plt.close(fig)
print("done")
