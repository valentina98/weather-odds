"""Which data predicts the Plovdiv station's temperatures best? (phase-0 research, issues #3 and #7)

validate_odds.py checks ERA5 against ERA5. Here the target is what the station
measured: each year 2001-2025 is predicted from the 30 years before it (only
those years with station data count), with +-7-day pooling, and scored against
the station's daily maximum temperature.

Predictions compared:
- the station's own past years;
- ERA5 as it is;
- ERA5 corrected to the station: minus its mean monthly difference from the
  station over the training years.
Each with and without trend adjustment (the warming trend of the same data,
fitted to the training years).

Writes docs/research/validation-station.json; the write-up is in
docs/research/validation.md (section "Against the station").
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import load_sources as src  # noqa: E402
from daystats import to_matrix  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs" / "research" / "validation-station.json"
TARGETS = np.arange(2001, 2026)
TRAIN_YEARS, POOL, MIN_DAYS = 30, 7, 330
MONTH_OF_DOY = pd.date_range("2001-01-01", "2001-12-31").month.to_numpy()


def ensemble(train: np.ndarray, w: int) -> np.ndarray:
    return np.concatenate([np.roll(train, -s, axis=1) for s in range(-w, w + 1)], axis=0)


def scores(ens: np.ndarray, obs: np.ndarray) -> tuple[float, float, float]:
    """Mean CRPS, bias and 10-90% coverage over the days with an observation, ignoring missing members."""
    crps, bias, inside = [], [], []
    for d in np.flatnonzero(~np.isnan(obs)):
        x = np.sort(ens[:, d][~np.isnan(ens[:, d])])
        m = len(x)
        i = np.arange(1, m + 1)
        crps.append(np.mean(np.abs(x - obs[d])) - np.sum((2 * i - m - 1) * x) / m**2)
        bias.append(obs[d] - x.mean())
        inside.append(x[int(0.1 * (m - 1))] <= obs[d] <= x[int(np.ceil(0.9 * (m - 1)))])
    return float(np.mean(crps)), float(np.mean(bias)), float(np.mean(inside))


def trend_shift(values: np.ndarray, years: np.ndarray, target: int) -> np.ndarray:
    annual = np.nanmean(values, axis=1)
    ok = np.sum(~np.isnan(values), axis=1) >= MIN_DAYS
    slope = np.polyfit(years[ok], annual[ok], 1)[0]
    return slope * (target - years)[:, None]


station = src.gsod()["tmax"].combine_first(src.meteostat_daily()["tmax"])
era5 = src.grid_daily("copernicus_era5")["tmax"]
S = to_matrix(station, (1961, 2025))
E = to_matrix(era5, (1961, 2025)).reindex(S.index)
years = S.index.to_numpy()
S, E = S.to_numpy().copy(), E.to_numpy()
S[np.sum(~np.isnan(S), axis=1) < MIN_DAYS] = np.nan  # years with too little station data do not count

rows = {}
for target in TARGETS:
    sel = (years >= target - TRAIN_YEARS) & (years < target) & (np.sum(~np.isnan(S), axis=1) >= MIN_DAYS)
    obs = S[years == target][0]
    if np.sum(~np.isnan(obs)) < MIN_DAYS:
        continue
    # monthly mean difference ERA5 - station over the training years
    diff = E[sel] - S[sel]
    monthly = pd.Series(np.nanmean(diff, axis=0)).groupby(MONTH_OF_DOY).transform("mean").to_numpy()
    candidates = {"station": S[sel], "ERA5": E[sel], "ERA5 corrected to the station": E[sel] - monthly}
    for name, train in candidates.items():
        for trend in (False, True):
            t = train + trend_shift(train, years[sel], target) if trend else train
            rows.setdefault((name, trend), []).append(scores(ensemble(t, POOL), obs))

table = []
for (name, trend), vals in rows.items():
    v = np.array(vals)
    table.append({"training_data": name, "trend_adjusted": trend, "target_years": len(v),
                  "tmax_crps_c": round(float(v[:, 0].mean()), 3), "tmax_bias_c": round(float(v[:, 1].mean()), 2),
                  "tmax_in_10_90_range": round(float(v[:, 2].mean()), 3)})
    print(table[-1])
OUT_JSON.write_text(json.dumps({"targets": [int(TARGETS[0]), int(TARGETS[-1])], "training_years": TRAIN_YEARS,
                                "pooling_days": POOL, "results": table}, indent=1))
