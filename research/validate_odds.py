"""Cross-validation of the historical odds (phase-0 research, follow-up to issue #7).

Pretend one year's weather is unknown, predict it only from other years'
statistics, score the prediction against what happened, and repeat for every
year. This shows how good the odds are and which settings work best.

Settings compared:
- training years: the N years before the target year (N = 10, 15, 20, 30, or all
  since 1961), i.e. only what the tool could have known at the time; and, as the
  owner suggested, all other years (also later ones) of 1996-2025 or 1961-2025;
- pooling window: +-0, 3, 7 or 15 days around the date;
- temperature only: with or without shifting older years by the warming trend
  fitted to the training years.

Targets: ERA5 at Plovdiv, every day of the 30 target years 1996-2025.
- daily maximum temperature: CRPS (the error of the whole predicted distribution,
  in deg C; lower is better), bias (observed minus predicted mean), and how often
  the day fell inside the predicted 10-90% range (80% is right);
- wet day (>= 1 mm): Brier score of the predicted chance (lower is better) and
  a reliability table.

Writes docs/research/img/validation.png and docs/research/validation.json; the
write-up is in docs/research/validation.md.
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
from daystats import doy365, to_matrix  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "research" / "img"
OUT_JSON = ROOT / "docs" / "research" / "validation.json"
RNG = np.random.default_rng(42)
FIRST = 1961  # 1960 lacks 1 January after the shift from UTC to local time
TARGETS = np.arange(1996, 2026)
WINDOWS = (0, 3, 7, 15)
PAST = (10, 15, 20, 30, "all")
DEFAULT = ("past", 30, 3, False)
AUTUMN = slice(int(doy365(pd.DatetimeIndex(["2001-09-01"]))[0]) - 1, int(doy365(pd.DatetimeIndex(["2001-11-30"]))[0]))
RELIABILITY_BINS = np.array([0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 1.0001])

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3, "font.size": 9})


def ensemble(train: np.ndarray, w: int) -> np.ndarray:
    """(members, 365): every training year's value on days d-w .. d+w (circular)."""
    return np.concatenate([np.roll(train, -s, axis=1) for s in range(-w, w + 1)], axis=0)


def tmax_scores(ens: np.ndarray, obs: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """CRPS of the empirical ensemble, obs minus its mean, and whether obs fell inside its 10-90% range."""
    x = np.sort(ens, axis=0)
    m = x.shape[0]
    i = np.arange(1, m + 1)[:, None]
    crps = np.mean(np.abs(x - obs), axis=0) - np.sum((2 * i - m - 1) * x, axis=0) / m**2
    lo, hi = x[int(0.1 * (m - 1))], x[int(np.ceil(0.9 * (m - 1)))]
    return crps, obs - x.mean(axis=0), (obs >= lo) & (obs <= hi)


def training_years(scheme: str, n, target: int, years: np.ndarray) -> np.ndarray:
    if scheme == "past":
        first = FIRST if n == "all" else target - n
        return (years >= first) & (years < target)
    first = 1996 if n == "1996-2025" else FIRST
    return (years >= first) & (years != target)


# ---------------------------------------------------------------------------
# load

era5 = src.grid_daily("copernicus_era5")
tmax = to_matrix(era5["tmax"], (FIRST, 2025))
wet = to_matrix(era5["wet"].astype(float), (FIRST, 2025))
years = tmax.index.to_numpy()
T, W = tmax.to_numpy(), wet.to_numpy()

configs = [("past", n, w, trend) for n in PAST for w in WINDOWS for trend in (False, True)]
configs += [("other years", n, w, trend) for n in ("1996-2025", "1961-2025") for w in WINDOWS for trend in (False, True)]

# per config: per target year, the mean score over the whole year and over Sep-Nov
per_year: dict = {}
reliability = {"p": [], "o": []}
for scheme, n, w, trend in configs:
    rows = []
    for target in TARGETS:
        sel = training_years(scheme, n, target, years)
        obs_t, obs_w = T[years == target][0], W[years == target][0]
        train_t = T[sel]
        if trend:
            annual = train_t.mean(axis=1)
            slope = np.polyfit(years[sel], annual, 1)[0]
            train_t = train_t + slope * (target - years[sel])[:, None]
        crps, bias, inside = tmax_scores(ensemble(train_t, w), obs_t)
        p_wet = ensemble(W[sel], w).mean(axis=0)
        brier = (p_wet - obs_w) ** 2
        rows.append([crps.mean(), crps[AUTUMN].mean(), bias.mean(), inside.mean(), inside[AUTUMN].mean(),
                     brier.mean(), brier[AUTUMN].mean()])
        if (scheme, n, w, trend) == DEFAULT:
            reliability["p"].append(p_wet)
            reliability["o"].append(obs_w)
    per_year[(scheme, n, w, trend)] = np.array(rows)
    print(scheme, n, w, trend, np.round(per_year[(scheme, n, w, trend)].mean(axis=0), 4))

COLUMNS = ["tmax_crps_c", "tmax_crps_autumn_c", "tmax_bias_c", "tmax_in_10_90_range", "tmax_in_10_90_range_autumn",
           "wet_brier", "wet_brier_autumn"]


def paired_diff(a: np.ndarray, b: np.ndarray) -> list[float]:
    """Mean difference a - b over target years, with a 95% bootstrap interval over years."""
    d = a - b
    reps = [d[RNG.integers(0, len(d), len(d))].mean() for _ in range(2000)]
    return [round(float(d.mean()), 4), *np.round(np.percentile(reps, [2.5, 97.5]), 4).tolist()]


table = []
for key, rows in per_year.items():
    scheme, n, w, trend = key
    entry = {"training": f"{n} years before" if scheme == "past" and n != "all" else
             (f"all years before (from {FIRST})" if scheme == "past" else f"all other years of {n}"),
             "pooling_days": w, "trend_adjusted": trend}
    entry.update({c: round(float(v), 4) for c, v in zip(COLUMNS, rows.mean(axis=0))})
    entry["vs_default"] = {c: paired_diff(rows[:, i], per_year[DEFAULT][:, i]) for i, c in enumerate(COLUMNS)
                           if c in ("tmax_crps_c", "wet_brier")}
    table.append(entry)

p = np.concatenate(reliability["p"])
o = np.concatenate(reliability["o"])
bins = np.digitize(p, RELIABILITY_BINS) - 1
rel = [{"predicted_from": float(RELIABILITY_BINS[b]), "predicted_to": float(min(RELIABILITY_BINS[b + 1], 1)),
        "days": int((bins == b).sum()), "mean_predicted": round(float(p[bins == b].mean()), 3),
        "observed": round(float(o[bins == b].mean()), 3)} for b in range(len(RELIABILITY_BINS) - 1) if (bins == b).any()]
const = np.concatenate([np.full(365, W[(years >= t - 30) & (years < t)].mean()) for t in TARGETS])
skill = 1 - np.mean((p - o) ** 2) / np.mean((const - o) ** 2)

OUT_JSON.write_text(json.dumps({
    "targets": [int(TARGETS[0]), int(TARGETS[-1])],
    "default": {"training": "30 years before", "pooling_days": 3, "trend_adjusted": False},
    "wet_brier_skill_vs_constant_chance": round(float(skill), 3),
    "reliability_default": rel,
    "configs": table,
}, indent=1))

# ---------------------------------------------------------------------------
# chart

labels = [str(n) for n in PAST[:-1]] + [f"all\nsince {FIRST}"]
xs = np.arange(len(PAST))
shades = {0: "#c6dbef", 3: "#6baed6", 7: "#2171b5", 15: "#08306b"}
fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
for w in WINDOWS:
    for trend, style in ((False, "-"), (True, "--")):
        ys = [per_year[("past", n, w, trend)][:, 0].mean() for n in PAST]
        axes[0].plot(xs, ys, style, marker="o", ms=3, color=shades[w],
                     label=f"±{w} days" + (", trend-adjusted" if trend else ""))
    axes[1].plot(xs, [per_year[("past", n, w, False)][:, COLUMNS.index("wet_brier")].mean() for n in PAST], marker="o", ms=3,
                 color=shades[w], label=f"±{w} days")
axes[0].set_title("Daily max temperature: error (CRPS)\nlower is better", fontsize=9)
axes[0].set_ylabel("°C")
axes[1].set_title("Wet day (≥ 1 mm): error (Brier score)\nlower is better", fontsize=9)
for ax in axes[:2]:
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_xlabel("training years before the target year")
fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=4, fontsize=7.5, frameon=False)
ax = axes[2]
ax.plot([0, 0.6], [0, 0.6], "k--", lw=0.8)
shown = [r for r in rel if r["days"] >= 100]  # sparser bins are in the JSON only
ax.plot([r["mean_predicted"] for r in shown], [r["observed"] for r in shown], "o-", color="#d1495b")
for r in shown:
    ax.annotate(f'{r["days"]}', (r["mean_predicted"], r["observed"]), fontsize=6, xytext=(3, -8),
                textcoords="offset points")
ax.set_xlim(0, 0.6)
ax.set_ylim(0, 0.6)
ax.set_xlabel("predicted chance of a wet day")
ax.set_ylabel("share of days that were wet")
ax.set_title("Wet-day chance, 30 years before, ±3 days:\ndoes 20% mean 20%? (numbers = days)", fontsize=9)
fig.suptitle(f"Plovdiv, ERA5: predicting each year {TARGETS[0]}-{TARGETS[-1]} from other years only", fontsize=10)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(IMG / "validation.png")
plt.close(fig)
print("done; skill vs constant", round(float(skill), 3))
