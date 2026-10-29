"""Cross-validation of the outdoor-weather scale's calendar colour (phase-0 research, issues #5 and #7).

The calendar colours a date by the chance that a past day there rated Good or
Great. Here each year 1996-2025 is predicted from the years before it (ERA5,
daylight hours) and scored against which days of that year really rated Good or
Great: Brier score, skill against a flat chance (the same chance on every day of
the year), and a reliability table. Compared: +-7-day pooling or none, and the
30 years before or all years before (from 1966), each with and without trend
adjustment.

Writes docs/research/validation-scale.json; the write-up is in
docs/research/validation.md (section "The outdoor-weather scale").
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import load_sources as src  # noqa: E402
from daystats import pooled, to_matrix  # noqa: E402
from scale import GOOD, daylight, period_scores  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs" / "research" / "validation-scale.json"
TARGETS = np.arange(1996, 2026)
FIRST = 1966
CONFIGS = [(7, 30), (0, 30), (0, "all")]  # (pooling days, training years before the target)
BINS = np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001])

hourly = src.era5_hourly("copernicus_era5")[["temperature_2m", "precipitation", "wind_gusts_10m"]]
hourly = hourly[daylight(hourly.index.tz_convert("UTC"))].loc[str(FIRST):"2025"]
actual = to_matrix(period_scores(hourly, min_hours=8) >= GOOD, (FIRST, 2025))
annual_temp = hourly["temperature_2m"].groupby(hourly.index.year).mean()

results = {}
for (pool, n), trend in [(c, t) for c in CONFIGS for t in (False, True)]:
    briers, flats, p_all, o_all = [], [], [], []
    for target in TARGETS:
        first = FIRST if n == "all" else target - n
        train = hourly[(hourly.index.year >= first) & (hourly.index.year < target)]
        if trend:
            years = annual_temp.loc[first:target - 1]
            slope = np.polyfit(years.index, years.to_numpy(), 1)[0]
            train = train.copy()
            train["temperature_2m"] += slope * (target - train.index.year)
        good = to_matrix((period_scores(train, min_hours=8) >= GOOD).astype(float), (first, target - 1)).to_numpy()
        p = pooled(good, pool)
        o = actual.loc[target].to_numpy(dtype=float)
        ok = ~np.isnan(o)
        briers.append(np.mean((p[ok] - o[ok]) ** 2))
        flats.append(np.mean((np.nanmean(good) - o[ok]) ** 2))
        p_all.append(p[ok])
        o_all.append(o[ok])
    p, o = np.concatenate(p_all), np.concatenate(o_all)
    bins = np.digitize(p, BINS) - 1
    key = f"+-{pool} days, {n} years before" + (", trend-adjusted" if trend else "")
    results[key] = {
        "brier": round(float(np.mean(briers)), 4),
        "brier_flat_chance": round(float(np.mean(flats)), 4),
        "skill_vs_flat_chance": round(float(1 - np.mean(briers) / np.mean(flats)), 3),
        "mean_predicted": round(float(p.mean()), 3), "share_good_observed": round(float(o.mean()), 3),
        "reliability": [{"predicted": round(float(p[bins == b].mean()), 3), "observed": round(float(o[bins == b].mean()), 3),
                         "days": int((bins == b).sum())} for b in range(len(BINS) - 1) if (bins == b).any()],
    }
    print(key, {k: v for k, v in results[key].items() if k != "reliability"})

OUT_JSON.write_text(json.dumps({"targets": [int(TARGETS[0]), int(TARGETS[-1])], "first_year": FIRST,
                                "results": results}, indent=1))
