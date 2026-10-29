"""Does it warm up in early October and get colder again? Checked per data source
and per range of years (phase-0 research, follow-up to issue #3).

Reads the cache filled by fetch_sources.py. Gridded sources come from the `aws`
source; station temperature is added when its cache exists. Writes a chart to
docs/research/img/ and numbers to docs/research/early-october.json. The write-up
is in docs/research/early-october.md.

Tests (daily maximum temperature, 365-day calendar), each for a window and the
ten days before and after it:
- Absolute change: mean of the window minus mean of the days before. Positive
  means it warms up into the window.
- Hump: departure from the smooth seasonal curve in the window minus the average
  departure before and after. Positive means the window stands out above its
  neighbours, i.e. "warmer, then colder again".
- 95% intervals from resampling whole years.

Windows: 1-10 Oct (the owner's description) and 15-25 Oct. The second was picked
after looking at the chart, so its interval overstates the evidence: with many
possible windows, one of them can look like a pattern by chance.
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
from daystats import doy365, harmonic_baseline, pooled, to_matrix, window_mean  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "research" / "img"
OUT_JSON = ROOT / "docs" / "research" / "early-october.json"
RNG = np.random.default_rng(42)
N_BOOT = 1000
LAST = 2025
RANGES = {
    "last 10 years": (2016, LAST),
    "last 15 years": (2011, LAST),
    "last 20 years": (2006, LAST),
    "last 30 years": (1996, LAST),
    "1960-1995": (1960, 1995),
    "all years": (1960, LAST),
}
TESTS = {  # name: (before, window, after)
    "1-10 Oct": (("09-21", "09-30"), ("10-01", "10-10"), ("10-11", "10-20")),
    "15-25 Oct (chosen after seeing the chart)": (("10-05", "10-14"), ("10-15", "10-25"), ("10-26", "11-04")),
}

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3, "font.size": 9})


def day(md: str) -> int:
    return int(doy365(pd.DatetimeIndex([f"2001-{md}"]))[0])


def stats(matrix: np.ndarray, before: tuple, window: tuple, after: tuple) -> dict:
    def one(m: np.ndarray) -> tuple[float, float]:
        curve = pooled(m, 0)
        dep = curve - harmonic_baseline(curve)
        change = window_mean(curve, *window) - window_mean(curve, *before)
        hump = window_mean(dep, *window) - (window_mean(dep, *before) + window_mean(dep, *after)) / 2
        return change, hump

    def per_year(span: tuple) -> np.ndarray:
        return np.nanmean(matrix[:, day(span[0]) - 1:day(span[1])], axis=1)

    value = one(matrix)
    rows = matrix.shape[0]
    reps = np.array([one(matrix[RNG.integers(0, rows, rows)]) for _ in range(N_BOOT)])
    lo, hi = np.percentile(reps, [2.5, 97.5], axis=0)
    inside, pre, post = per_year(window), per_year(before), per_year(after)
    return {
        "change_c": [round(float(value[0]), 2), round(float(lo[0]), 2), round(float(hi[0]), 2)],
        "hump_c": [round(float(value[1]), 2), round(float(lo[1]), 2), round(float(hi[1]), 2)],
        "years_warmer_than_before": int((inside > pre).sum()),
        "years_warmer_then_colder": int(((inside > pre) & (inside > post)).sum()),
    }


# ---------------------------------------------------------------------------
# load

sources = {
    "ERA5 (25 km)": src.grid_daily("copernicus_era5")["tmax"],
    "ERA5-Land (9 km)": src.grid_daily("copernicus_era5_land")["tmax"],
    "ECMWF IFS (9 km)": src.grid_daily("ecmwf_ifs")["tmax"],
}
try:
    sources["CERRA (5.5 km, to mid-2021)"] = src.open_meteo_daily("cerra_daily")["tmax"]
except FileNotFoundError:
    print("CERRA cache missing; CERRA rows skipped")
try:
    sources["Station (GSOD + Meteostat)"] = src.gsod()["tmax"].combine_first(src.meteostat_daily()["tmax"])
except (ValueError, FileNotFoundError):
    print("station cache missing; station rows skipped")

results: dict = {}
for name, series in sources.items():
    results[name] = {}
    for label, (a, b) in RANGES.items():
        matrix = to_matrix(series.dropna(), (a, b))
        matrix = matrix[matrix.notna().sum(axis=1) > 300]  # complete years only
        if len(matrix) < max(8, 0.8 * (b - a + 1)):
            continue
        entry = {"from": int(matrix.index.min()), "to": int(matrix.index.max()), "years": len(matrix)}
        for test, spans in TESTS.items():
            entry[test] = stats(matrix.to_numpy(), *spans)
        results[name][label] = entry
        print(name, label, results[name][label])

OUT_JSON.write_text(json.dumps(results, indent=1))

# ---------------------------------------------------------------------------
# chart: mean daily max by range (top) and each recent year's departure (bottom)

era5 = sources["ERA5 (25 km)"]
x = np.arange(1, 366)
first, last = day("09-15"), day("11-15")
ticks = ["09-15", "10-01", "10-15", "11-01", "11-15"]

fig, axes = plt.subplots(2, 1, figsize=(9, 8.2), gridspec_kw={"height_ratios": [1, 1.25]})
ax = axes[0]
lines = [
    ("ERA5, all years 1960-2025", era5, RANGES["all years"], "#9aa5b1", "-"),
    ("ERA5, last 30 years", era5, RANGES["last 30 years"], "#1b6ca8", "-"),
    ("ERA5, last 10 years", era5, RANGES["last 10 years"], "#d1495b", "-"),
    ("ECMWF IFS 9 km, 2017-2025", sources["ECMWF IFS (9 km)"], (2017, LAST), "#d1495b", ":"),
]
if "Station (GSOD + Meteostat)" in sources:
    lines.append(("Station, last 10 years", sources["Station (GSOD + Meteostat)"], RANGES["last 10 years"], "#2e933c", "--"))
for label, series, years, color, style in lines:
    m = to_matrix(series.dropna(), years).to_numpy()
    ax.plot(x, pooled(m, 3), style, color=color, lw=1.6, label=label)
m10 = to_matrix(era5, RANGES["last 10 years"]).to_numpy()
reps = np.array([pooled(m10[RNG.integers(0, len(m10), len(m10))], 3) for _ in range(300)])
ax.fill_between(x, *np.percentile(reps, [2.5, 97.5], axis=0), color="#d1495b", alpha=0.12, lw=0,
                label="95% interval, last 10 years")
for _, (a, b), _ in TESTS.values():
    ax.axvspan(day(a), day(b), color="0.85", alpha=0.5, lw=0)
ax.set_xlim(first, last)
ax.set_ylim(10, 28)
ax.set_ylabel("mean daily max, °C (±3-day average)")
ax.set_title("Plovdiv: mean daily maximum temperature, 15 Sep - 15 Nov (grey: 1-10 Oct and 15-25 Oct)")
ax.legend(fontsize=7, loc="lower left")

ax = axes[1]
ref = to_matrix(era5, RANGES["last 30 years"]).to_numpy()
baseline = harmonic_baseline(pooled(ref, 0))
recent = to_matrix(era5, (2006, LAST))
smooth = recent.T.rolling(3, center=True, min_periods=1).mean().T  # 3-day running mean per year
dep = smooth.to_numpy() - baseline
im = ax.imshow(dep[:, first - 1:last], aspect="auto", cmap="RdBu_r", vmin=-8, vmax=8,
               extent=(first - 0.5, last + 0.5, recent.index[-1] + 0.5, recent.index[0] - 0.5))
for _, (a, b), _ in TESTS.values():
    for edge in (day(a) - 0.5, day(b) + 0.5):
        ax.axvline(edge, color="k", lw=0.8, ls="--")
ax.set_yticks(recent.index)
ax.set_yticklabels(recent.index, fontsize=7)
ax.set_title("Each year, ERA5: daily max minus the 1996-2025 seasonal curve (3-day mean)")
fig.colorbar(im, ax=ax, label="°C warmer (red) / colder (blue) than normal", fraction=0.03, pad=0.01)
for a in axes:
    a.set_xticks([day(t) for t in ticks])
    a.set_xticklabels([pd.Timestamp(f"2001-{t}").strftime("%d %b") for t in ticks])
fig.tight_layout()
fig.savefig(IMG / "early-october.png")
plt.close(fig)
print("done")
