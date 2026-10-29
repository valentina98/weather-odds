"""Does early October bring a warm-up at a date that varies from year to year?
(phase-0 research, follow-up to the owner's question in issue #3)

Averaging by calendar date can hide a warm-up that comes on a different day each
year. This script therefore finds the events in each year first and only then
counts how often they fall into each 10-day window of September to November.

Events (ERA5 daily maximum temperature, Plovdiv):
- Warm spell: at least 3 days in a row at least 3 deg C above the smooth seasonal
  curve of the years used (detrended within those years). Counted at its first day.
- Warm-up: "warmer, then colder again" in absolute terms. The 3-day mean rises by
  at least 3 deg C from its lowest point in the 7 days before, peaks (highest
  within +-5 days), and falls by at least 3 deg C within the 7 days after.
  Counted at its peak.

A window "has" an event in a year if at least one event falls into it. Early
October is compared with the mean of the other eight windows; 95% intervals come
from resampling whole years.

Writes docs/research/img/warm-spells.png and docs/research/warm-spells.json; the
write-up is in docs/research/early-october.md.
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
from daystats import doy365, harmonic_baseline, pooled, to_matrix  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "research" / "img"
OUT_JSON = ROOT / "docs" / "research" / "warm-spells.json"
RNG = np.random.default_rng(42)
N_BOOT = 2000
RANGES = {"all years": (1961, 2025), "last 30 years": (1996, 2025), "last 10 years": (2016, 2025)}
WINDOWS = [("09-01", "09-10"), ("09-11", "09-20"), ("09-21", "09-30"), ("10-01", "10-10"), ("10-11", "10-20"),
           ("10-21", "10-31"), ("11-01", "11-10"), ("11-11", "11-20"), ("11-21", "11-30")]
EARLY_OCT = 3  # index of 1-10 Oct in WINDOWS
SPELL_ANOMALY, SPELL_DAYS = 3.0, 3
RISE, FALL, LOOK = 3.0, 3.0, 7

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3, "font.size": 9})


def day(md: str) -> int:
    return int(doy365(pd.DatetimeIndex([f"2001-{md}"]))[0])


def warm_spell_starts(anomaly: np.ndarray) -> list[int]:
    """Day-of-year (1-based) of the first day of each warm spell in one year."""
    hot = np.nan_to_num(anomaly, nan=-99) >= SPELL_ANOMALY
    starts, run = [], 0
    for i, h in enumerate(hot):
        run = run + 1 if h else 0
        if run == SPELL_DAYS:
            starts.append(i - SPELL_DAYS + 2)
    return starts


def warm_up_peaks(tmax: np.ndarray) -> list[int]:
    """Day-of-year (1-based) of each warm-up peak in one year (absolute temperatures)."""
    m3 = pd.Series(tmax).rolling(3, center=True).mean().to_numpy()
    peaks = []
    for i in range(LOOK, len(m3) - LOOK):
        if np.isnan(m3[i]) or m3[i] < np.nanmax(m3[max(0, i - 5):i + 6]):
            continue
        if m3[i] - np.nanmin(m3[i - LOOK:i]) >= RISE and m3[i] - np.nanmin(m3[i + 1:i + LOOK + 1]) >= FALL:
            peaks.append(i + 1)
    return peaks


def window_hits(events_by_year: list[list[int]]) -> np.ndarray:
    """(years, windows): 1 if the year has at least one event in the window."""
    bounds = [(day(a), day(b)) for a, b in WINDOWS]
    return np.array([[any(a <= e <= b for e in events) for a, b in bounds] for events in events_by_year], dtype=float)


def summarise(hits: np.ndarray) -> dict:
    def contrast(h: np.ndarray) -> float:
        others = np.delete(h, EARLY_OCT, axis=1)
        return h[:, EARLY_OCT].mean() - others.mean()

    reps = [contrast(hits[RNG.integers(0, len(hits), len(hits))]) for _ in range(N_BOOT)]
    return {
        "share_of_years_by_window": {f"{a}..{b}": round(float(v), 3) for (a, b), v in zip(WINDOWS, hits.mean(axis=0))},
        "early_oct_minus_other_windows": [round(float(contrast(hits)), 3),
                                          *np.round(np.percentile(reps, [2.5, 97.5]), 3).tolist()],
    }


# ---------------------------------------------------------------------------

tmax = src.grid_daily("copernicus_era5")["tmax"]
results: dict = {}
shares: dict = {}
for label, (a, b) in RANGES.items():
    matrix = to_matrix(tmax, (a, b))
    years = matrix.index.to_numpy()
    values = matrix.to_numpy()
    # Detrend within the range so warming does not create or hide warm spells.
    annual = np.nanmean(values, axis=1)
    slope = np.polyfit(years, annual, 1)[0]
    detrended = values - slope * (years - years.mean())[:, None]
    anomaly = detrended - harmonic_baseline(pooled(detrended, 0))
    spells = window_hits([warm_spell_starts(row) for row in anomaly])
    warmups = window_hits([warm_up_peaks(row) for row in values])
    results[label] = {"years": [int(years[0]), int(years[-1])],
                      "warm_spell": summarise(spells), "warm_up": summarise(warmups)}
    shares[label] = (spells.mean(axis=0), warmups.mean(axis=0))
    print(label, json.dumps(results[label]["warm_spell"]["early_oct_minus_other_windows"]),
          json.dumps(results[label]["warm_up"]["early_oct_minus_other_windows"]))

OUT_JSON.write_text(json.dumps({
    "definitions": {"warm_spell": f">= {SPELL_DAYS} days >= {SPELL_ANOMALY} C above the seasonal curve",
                    "warm_up": f"3-day mean rises >= {RISE} C within {LOOK} days, peaks, falls >= {FALL} C within {LOOK} days"},
    "results": results,
}, indent=1))

# ---------------------------------------------------------------------------
# chart: share of years with an event, per 10-day window

labels = [pd.Timestamp(f"2001-{a}").strftime("%d %b") for a, _ in WINDOWS]
x = np.arange(len(WINDOWS))
colors = {"all years": "#9aa5b1", "last 30 years": "#1b6ca8", "last 10 years": "#d1495b"}
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, k, title in zip(axes, (0, 1), ("Warm spell starts\n(≥ 3 days ≥ 3 °C above the seasonal curve)",
                                       "Warm-up peaks\n(rises ≥ 3 °C, then falls ≥ 3 °C, within a week each way)")):
    for i, (label, (a, b)) in enumerate(RANGES.items()):
        ax.bar(x + (i - 1) * 0.27, shares[label][k] * 100, width=0.27, color=colors[label],
               label=f"{label} ({a}-{b})")
    ax.axvspan(EARLY_OCT - 0.5, EARLY_OCT + 0.5, color="0.85", alpha=0.5, lw=0, zorder=0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_title(title, fontsize=9)
axes[0].set_ylabel("% of years with at least one event\nin the 10 days starting on")
axes[0].legend(fontsize=7.5, loc="upper left")
fig.suptitle("Plovdiv, ERA5 daily maximum: when do warm spells and warm-ups happen? (grey: 1-10 Oct)", fontsize=10)
fig.tight_layout()
fig.savefig(IMG / "warm-spells.png")
plt.close(fig)
print("done")
