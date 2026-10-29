"""Phase-0 data check for Plovdiv: are the recurring autumn patterns real, and how
do the data sources compare?

Reads the cache filled by fetch_sources.py, writes charts to docs/research/img/
and key numbers to docs/research/plovdiv-data-check.json. The write-up is in
docs/research/plovdiv-data-check.md.

Method (see docs/spec/methodology.md for the reasoning):
- Day-of-year statistics on a 365-day calendar (29 Feb dropped).
- "Pooling" = averaging each date with its +-w neighbouring days in all years.
- Uncertainty = 95% bootstrap interval from resampling whole years (keeps the
  day-to-day correlation within a year intact).
- Seasonal baseline = least-squares fit of 3 annual harmonics. A "pattern" is a
  departure of the pooled value from this smooth baseline.
- Split-sample check: a pattern must point the same way in both halves of the record.
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
OUT_JSON = ROOT / "docs" / "research" / "plovdiv-data-check.json"
RNG = np.random.default_rng(42)
N_BOOT = 500
REF = (1996, 2025)  # last 30 complete years
results: dict = {}

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3, "font.size": 9})
COLORS = {"station": "#1b6ca8", "era5": "#d1495b", "nimh": "#2e933c", "power": "#8e6c8a", "metar": "#edae49"}

# ---------------------------------------------------------------------------
# helpers


def bootstrap(matrix: np.ndarray, w: int, n: int = N_BOOT) -> tuple[np.ndarray, np.ndarray]:
    reps = np.empty((n, 365))
    rows = matrix.shape[0]
    for i in range(n):
        reps[i] = pooled(matrix[RNG.integers(0, rows, rows)], w)
    return np.nanpercentile(reps, 2.5, axis=0), np.nanpercentile(reps, 97.5, axis=0)


def boot_window_diff(matrix: np.ndarray, window: tuple[str, str]) -> tuple[float, float, float]:
    """Bootstrap the departure of a window's mean from the harmonic baseline."""
    def stat(m: np.ndarray) -> float:
        curve = pooled(m, 0)
        return window_mean(curve - harmonic_baseline(curve), *window)

    value = stat(matrix)
    rows = matrix.shape[0]
    reps = [stat(matrix[RNG.integers(0, rows, rows)]) for _ in range(N_BOOT)]
    return value, float(np.percentile(reps, 2.5)), float(np.percentile(reps, 97.5))


def detrend(series: pd.Series) -> pd.Series:
    """Remove the linear trend of annual means (keeps the series' overall mean)."""
    annual = series.groupby(series.index.year).mean()
    annual = annual[series.groupby(series.index.year).count() > 300]
    slope, intercept = np.polyfit(annual.index, annual.to_numpy(), 1)
    years = series.index.year.to_numpy()
    return series - slope * (years - annual.index.to_numpy().mean())


DATE_TICKS = ["09-01", "09-15", "10-01", "10-15", "11-01", "11-15", "11-30"]


def date_axis(ax, first="09-01", last="11-30"):
    a, b = (doy365(pd.DatetimeIndex([f"2001-{d}"]))[0] for d in (first, last))
    ax.set_xlim(a, b)
    ticks = [d for d in DATE_TICKS if first <= d <= last]
    ax.set_xticks([doy365(pd.DatetimeIndex([f"2001-{d}"]))[0] for d in ticks])
    ax.set_xticklabels([pd.Timestamp(f"2001-{d}").strftime("%d %b") for d in ticks])


def shade_hypotheses(ax):
    spans = [("09-20", "09-30", "late-Sep rain?"), ("10-01", "10-14", "early-Oct warm?"),
             ("10-20", "10-31", "late-Oct cold?"), ("10-26", "11-20", "Dimitrovden warm?")]
    for i, (a, b, label) in enumerate(spans):
        x0, x1 = (doy365(pd.DatetimeIndex([f"2001-{d}"]))[0] for d in (a, b))
        ax.axvspan(x0, x1, color="0.85", alpha=0.35 if i % 2 == 0 else 0.2, lw=0)
        ax.text((x0 + x1) / 2, 1.0 + 0.07 * (i % 2), label, transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=7)


# ---------------------------------------------------------------------------
# load

print("loading ...")
gsod = src.gsod()
meteostat = src.meteostat_daily()
nimh = src.nimh()
power = src.nasa_power()
metar_h = src.metar_hourly()
metar_d = src.metar_daily()
era5 = src.era5_daily()
era5_h = src.era5_hourly("copernicus_era5")

# Station temperature: GSOD, with Meteostat filling GSOD gaps from 1997.
station_tmax = gsod["tmax"].combine_first(meteostat["tmax"])
station_tmin = gsod["tmin"].combine_first(meteostat["tmin"])
# Measured station rain: GSOD 1973-1999 + NIMH from 2022.
station_wet = pd.concat([gsod["wet"].dropna().loc["1973":"1999"], nimh["wet"]]).astype(float)

# ---------------------------------------------------------------------------
# 1. coverage

def coverage(series: pd.Series) -> pd.Series:
    s = series.dropna()
    return s.groupby(s.index.year).size() / 365.25

cov = pd.DataFrame({
    "Station temperature (GSOD + Meteostat)": coverage(station_tmax),
    "Station rain amounts (GSOD)": coverage(gsod["prcp"].loc["1973":"1999"]),
    "Station rain amounts (NIMH)": coverage(nimh["prcp"]),
    "Airport rain/thunder codes (METAR)": coverage(metar_d["rain_seen"].loc["2011":]),
    "NASA POWER (grid)": coverage(power["tmax"]),
    "ERA5 (grid)": coverage(era5["prcp"]),
}).reindex(range(1959, 2027)).fillna(0).clip(upper=1)

fig, ax = plt.subplots(figsize=(9, 2.8))
for i, col in enumerate(cov.columns):
    ax.scatter(cov.index, [i] * len(cov), s=cov[col] * 40, color="0.25", marker="s")
ax.set_yticks(range(len(cov.columns)))
ax.set_yticklabels(cov.columns)
ax.invert_yaxis()
ax.set_title("Which Plovdiv data exists for which year (square size = share of days)")
fig.tight_layout()
fig.savefig(IMG / "coverage.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. source agreement

overlap = {}
for name, other in [("ERA5 (height-corrected)", era5["tmax"]), ("ERA5-Land (height-corrected)", era5["tmax_land"]),
                    ("NASA POWER", power["tmax"])]:
    j = pd.concat([station_tmax.rename("st"), other.rename("x")], axis=1).dropna().loc["1991":"2025"]
    diff = j["x"] - j["st"]
    overlap[name] = {
        "days": int(len(j)),
        "mean_bias_c": round(float(diff.mean()), 2),
        "mean_abs_diff_c": round(float(diff.abs().mean()), 2),
        "corr": round(float(j.corr().iloc[0, 1]), 3),
        "bias_by_month_c": {int(m): round(float(v), 1) for m, v in diff.groupby(diff.index.month).mean().items()},
    }
results["tmax_vs_station"] = overlap

wet_compare = {}
for label, years, station in [("1973-1999", ("1973", "1999"), gsod["wet"].dropna().loc["1973":"1999"]),
                              ("2022-2025", ("2022", "2025"), nimh["wet"].loc["2022":"2025"])]:
    row = {"station": station.astype(float)}
    row["ERA5"] = era5["wet"].astype(float).reindex(station.index)
    row["NASA POWER"] = power["wet"].astype(float).reindex(station.index)
    frame = pd.DataFrame(row).dropna()
    wet_compare[label] = {
        "days": int(len(frame)),
        "wet_day_share": {k: round(float(v), 3) for k, v in frame.mean().items()},
        "by_month": {k: {int(m): round(float(x), 3) for m, x in frame[k].groupby(frame.index.month).mean().items()}
                     for k in frame.columns},
        "agreement_era5": round(float((frame["ERA5"] == frame["station"]).mean()), 3),
    }
results["wet_days_vs_station"] = wet_compare

fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
months = np.arange(1, 13)
for ax, label in zip(axes[:2], ["1973-1999", "2022-2025"]):
    bm = wet_compare[label]["by_month"]
    for k, c in [("station", COLORS["station"]), ("ERA5", COLORS["era5"]), ("NASA POWER", COLORS["power"])]:
        ax.plot(months, [bm[k][m] * 100 for m in months], marker="o", ms=3, color=c,
                label="station (GSOD)" if k == "station" and label == "1973-1999" else
                ("station (NIMH)" if k == "station" else k))
    ax.set_title(f"Share of days with >= 1 mm rain, {label}")
    ax.set_xticks(months)
    ax.set_ylabel("%")
    ax.legend(fontsize=7)
ax = axes[2]
for name, c in [("ERA5 (height-corrected)", COLORS["era5"]), ("ERA5-Land (height-corrected)", "#f29e4c"),
                ("NASA POWER", COLORS["power"])]:
    b = overlap[name]["bias_by_month_c"]
    ax.plot(months, [b[m] for m in months], marker="o", ms=3, color=c, label=name)
ax.axhline(0, color="k", lw=0.8)
ax.set_title("Max temperature: grid minus station, 1991-2025", fontsize=9)
ax.set_ylabel("deg C")
ax.set_xticks(months)
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(IMG / "sources-compared.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# 3. warming trend

annual = pd.DataFrame({
    "station": station_tmax.groupby(station_tmax.index.year).agg(["mean", "count"]).query("count > 330")["mean"],
    "era5": era5["tmax"].groupby(era5.index.year).mean(),
}).loc[1960:2025]
trend = {}
for col in annual:
    s = annual[col].dropna()
    slope = np.polyfit(s.index, s.to_numpy(), 1)[0]
    s80 = s.loc[1980:]
    trend[col] = {"per_decade_since_1960_c": round(slope * 10, 2),
                  "per_decade_since_1980_c": round(np.polyfit(s80.index, s80.to_numpy(), 1)[0] * 10, 2)}
ref = era5["tmax"]
trend["era5_mean_tmax_1961_1990_vs_1996_2025_c"] = round(
    float(ref.loc["1996":"2025"].mean() - ref.loc["1961":"1990"].mean()), 2)
results["warming"] = trend

fig, ax = plt.subplots(figsize=(8, 2.8))
ax.plot(annual.index, annual["station"], "o-", ms=3, color=COLORS["station"], label="station (GSOD/Meteostat)")
ax.plot(annual.index, annual["era5"], "-", color=COLORS["era5"], label="ERA5, height-corrected")
ax.set_title("Plovdiv: annual mean of daily maximum temperature")
ax.set_ylabel("deg C")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(IMG / "warming.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# 4. autumn patterns

W = 3
st_tmax_dt = detrend(station_tmax.dropna())
mat_t_all = to_matrix(st_tmax_dt, (1959, 2025)).to_numpy()
mat_t_ref = to_matrix(station_tmax, REF).to_numpy()
mat_wet_era5 = to_matrix(era5["wet"].astype(float), REF).to_numpy()
mat_wet_era5_long = to_matrix(era5["wet"].astype(float), (1960, 2025)).to_numpy()
mat_wet_station = to_matrix(gsod["wet"].dropna().loc["1973":"1999"].astype(float), (1973, 1999)).to_numpy()
mat_wet_era5_7399 = to_matrix(era5["wet"].astype(float), (1973, 1999)).to_numpy()

fig, axes = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True)
ax = axes[0]
curve = pooled(mat_t_ref, W)
lo, hi = bootstrap(mat_t_ref, W)
base = harmonic_baseline(pooled(mat_t_ref, 0))
x = np.arange(1, 366)
ax.fill_between(x, lo, hi, color=COLORS["station"], alpha=0.2, lw=0, label="95% interval")
ax.plot(x, curve, color=COLORS["station"], label=f"station, {REF[0]}-{REF[1]}, pooled +-{W} days")
ax.plot(x, base, "k--", lw=1, label="smooth seasonal baseline")
ax.set_ylabel("mean daily max, deg C")
ax.set_ylim(5, 30)
ax.legend(fontsize=7, loc="lower left")
shade_hypotheses(ax)
ax = axes[1]
lo, hi = bootstrap(mat_wet_era5, W)
ax.fill_between(x, lo * 100, hi * 100, color=COLORS["era5"], alpha=0.15, lw=0)
ax.plot(x, pooled(mat_wet_era5, W) * 100, color=COLORS["era5"], label=f"ERA5, {REF[0]}-{REF[1]}")
ax.plot(x, pooled(mat_wet_era5_7399, W) * 100, "--", color=COLORS["era5"], label="ERA5, 1973-1999")
ax.plot(x, pooled(mat_wet_station, W) * 100, color=COLORS["station"], label="station (GSOD), 1973-1999")
ax.set_ylabel("chance of a day with >= 1 mm, %")
ax.legend(fontsize=7, loc="upper left")
date_axis(ax)
fig.suptitle("Plovdiv, September-November: daily max temperature and wet-day chance")
fig.tight_layout()
fig.savefig(IMG / "autumn-patterns.png")
plt.close(fig)

hyp = {}
hyp["early_oct_warm_tmax_vs_baseline_all_years"] = boot_window_diff(mat_t_all, ("10-01", "10-14"))
hyp["early_oct_warm_tmax_vs_baseline_ref"] = boot_window_diff(mat_t_ref, ("10-01", "10-14"))
hyp["late_oct_cold_tmax_vs_baseline_all_years"] = boot_window_diff(mat_t_all, ("10-20", "10-31"))
hyp["late_oct_cold_tmax_vs_baseline_ref"] = boot_window_diff(mat_t_ref, ("10-20", "10-31"))
hyp["dimitrovden_warm_tmax_vs_baseline_all_years"] = boot_window_diff(mat_t_all, ("10-26", "11-20"))
hyp["late_sep_wet_vs_baseline_era5_ref"] = boot_window_diff(mat_wet_era5, ("09-20", "09-30"))
hyp["late_sep_wet_vs_baseline_era5_1960_2025"] = boot_window_diff(mat_wet_era5_long, ("09-20", "09-30"))
hyp["late_sep_wet_vs_baseline_station_1973_1999"] = boot_window_diff(mat_wet_station, ("09-20", "09-30"))
results["autumn_hypotheses"] = {k: {"value": round(v[0], 3), "ci95": [round(v[1], 3), round(v[2], 3)]}
                                for k, v in hyp.items()}

# Raw window averages (easier to read than departures from a baseline).
def window_stats(mat: np.ndarray, windows: list[tuple[str, str]], scale: float = 1.0) -> dict:
    curve = pooled(mat, 0)
    return {f"{a}..{b}": round(window_mean(curve, a, b) * scale, 1) for a, b in windows}

wins = [("09-01", "09-14"), ("09-15", "09-30"), ("10-01", "10-14"), ("10-15", "10-31"), ("11-01", "11-14"), ("11-15", "11-30")]
results["autumn_window_means"] = {
    "station_tmax_ref_c": window_stats(mat_t_ref, wins),
    "era5_wet_day_pct_ref": window_stats(mat_wet_era5, wins, 100),
    "station_wet_day_pct_1973_1999": window_stats(mat_wet_station, wins, 100),
}

# Warm-spell frequency: share of years with >= 3 consecutive days at least 3 C
# above the smooth baseline, inside each 14-day window.
def spell_share(mat: np.ndarray, start: str, threshold: float = 3.0, run: int = 3, length: int = 14) -> tuple[float, int]:
    base = harmonic_baseline(pooled(mat, 0))
    a = doy365(pd.DatetimeIndex([f"2001-{start}"]))[0] - 1
    hits = []
    for row in mat:
        seg = row[a:a + length] - base[a:a + length]
        if np.isnan(seg).sum() > 3:
            continue
        flags = np.nan_to_num(seg, nan=-99) >= threshold
        best = max((len(g) for g in "".join("1" if f else "0" for f in flags).split("0")), default=0)
        hits.append(best >= run)
    return float(np.mean(hits)), len(hits)

spells = {}
for start in ["09-01", "09-15", "10-01", "10-15", "11-01", "11-15"]:
    share, n = spell_share(mat_t_all, start)
    spells[start] = {"share_of_years": round(share, 2), "years": n}
results["warm_spell_share_by_fortnight"] = spells

# ---------------------------------------------------------------------------
# 5. whole-year scan with split-sample check

def scan(mat: np.ndarray, w: int, scale: float, k: int = 3) -> dict:
    curve = pooled(mat, w)
    base = harmonic_baseline(pooled(mat, 0), k)
    lo, hi = bootstrap(mat, w)
    half = mat.shape[0] // 2
    first = pooled(mat[:half], w) - harmonic_baseline(pooled(mat[:half], 0), k)
    second = pooled(mat[half:], w) - harmonic_baseline(pooled(mat[half:], 0), k)
    return {"resid": (curve - base) * scale, "lo": (lo - base) * scale, "hi": (hi - base) * scale,
            "first": first * scale, "second": second * scale}


def top_departures(s: dict, n: int = 8, min_gap: int = 10) -> list[dict]:
    """Largest departures from the baseline, at least min_gap days apart, flagged or not."""
    order = np.argsort(-np.abs(np.nan_to_num(s["resid"])))
    picked: list[int] = []
    for i in order:
        if all(min(abs(i - j), 365 - abs(i - j)) >= min_gap for j in picked):
            picked.append(int(i))
        if len(picked) == n:
            break
    out = []
    for i in sorted(picked):
        out.append({
            "date": (pd.Timestamp("2001-01-01") + pd.Timedelta(days=i)).strftime("%d %b"),
            "departure": round(float(s["resid"][i]), 2),
            "ci95": [round(float(s["lo"][i]), 2), round(float(s["hi"][i]), 2)],
            "both_halves_agree": bool(np.sign(s["first"][i]) == np.sign(s["second"][i])),
        })
    return out


def flagged_runs(s: dict, min_len: int = 5) -> list[dict]:
    sig = (s["lo"] > 0) | (s["hi"] < 0)
    same = np.sign(s["first"]) == np.sign(s["second"])
    keep = sig & same
    runs, start = [], None
    for i in range(366):
        on = i < 365 and keep[i]
        if on and start is None:
            start = i
        elif not on and start is not None:
            if i - start >= min_len:
                d0 = pd.Timestamp("2001-01-01") + pd.Timedelta(days=start)
                d1 = pd.Timestamp("2001-01-01") + pd.Timedelta(days=i - 1)
                runs.append({"from": d0.strftime("%d %b"), "to": d1.strftime("%d %b"),
                             "mean_departure": round(float(np.mean(s["resid"][start:i])), 2)})
            start = None
    return runs

scan_t = scan(mat_t_all, W, 1.0)
scan_w = scan(mat_wet_era5_long, W, 100.0)
results["year_scan"] = {
    "tmax_station_detrended_1959_2025": flagged_runs(scan_t),
    "wet_day_era5_1960_2025": flagged_runs(scan_w),
    "tmax_top_departures": top_departures(scan_t),
    "wet_top_departures": top_departures(scan_w),
    # Does the result depend on how flexible the smooth baseline is?
    "sensitivity_harmonics": {
        f"k={k}": {"tmax": flagged_runs(scan(mat_t_all, W, 1.0, k)),
                   "wet": flagged_runs(scan(mat_wet_era5_long, W, 100.0, k))}
        for k in (2, 4)
    },
}

fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
for ax, s, title, unit in [(axes[0], scan_t, "Daily max temperature vs smooth baseline (station, 1959-2025, detrended)", "deg C"),
                           (axes[1], scan_w, "Chance of a wet day vs smooth baseline (ERA5, 1960-2025)", "percentage points")]:
    ax.fill_between(x, s["lo"], s["hi"], color="0.6", alpha=0.3, lw=0, label="95% interval (all years)")
    ax.plot(x, s["resid"], color="k", lw=1, label="all years")
    ax.plot(x, s["first"], color=COLORS["station"], lw=0.8, alpha=0.8, label="first half of years")
    ax.plot(x, s["second"], color=COLORS["era5"], lw=0.8, alpha=0.8, label="second half of years")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_title(title, fontsize=9)
    ax.set_ylabel(unit)
    ax.legend(fontsize=7, ncol=4, loc="lower left")
months_start = [doy365(pd.DatetimeIndex([f"2001-{m:02d}-01"]))[0] for m in range(1, 13)]
axes[1].set_xticks(months_start)
axes[1].set_xticklabels([pd.Timestamp(2001, m, 1).strftime("%b") for m in range(1, 13)])
axes[1].set_xlim(1, 365)
fig.tight_layout()
fig.savefig(IMG / "year-scan.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# 6. how noisy is a single day? interval width vs pooling window

noise = {}
for w in [0, 3, 7, 15]:
    lo, hi = bootstrap(mat_wet_era5, w, n=300)
    tlo, thi = bootstrap(mat_t_ref, w, n=300)
    noise[f"+-{w} days"] = {
        "wet_day_pct_halfwidth": round(float(np.nanmedian(hi - lo)) * 50, 1),
        "tmax_c_halfwidth": round(float(np.nanmedian(thi - tlo)) / 2, 2),
    }
results["noise_vs_pooling_30_years"] = noise

# ---------------------------------------------------------------------------
# 7. rain by hour of day

def hour_month_share(flags: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame({"m": flags.index.month, "h": flags.index.hour, "v": flags.to_numpy(dtype=float)})
    return frame.pivot_table(index="h", columns="m", values="v", aggfunc="mean") * 100

metar_share = hour_month_share(metar_h["rain"].loc["2012":"2025"])
era5_flags = (era5_h["precipitation"] >= 0.1).loc["2012":"2025"]
era5_share = hour_month_share(era5_flags)
results["hourly_rain_pct"] = {
    "metar_2012_2025_jun": {int(h): round(float(v), 1) for h, v in metar_share[6].items()},
    "metar_2012_2025_oct": {int(h): round(float(v), 1) for h, v in metar_share[10].items()},
    "era5_2012_2025_jun": {int(h): round(float(v), 1) for h, v in era5_share[6].items()},
    "metar_overall": round(float(metar_h["rain"].loc["2012":"2025"].mean() * 100), 1),
    "era5_overall": round(float(era5_flags.mean() * 100), 1),
}

fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
vmax = max(np.nanmax(metar_share.to_numpy()), np.nanmax(era5_share.to_numpy()))
for ax, share, title in [(axes[0], metar_share, "Airport reports (METAR): rain/thunder reported"),
                         (axes[1], era5_share, "ERA5: >= 0.1 mm in the hour")]:
    im = ax.imshow(share.to_numpy(), aspect="auto", origin="lower", cmap="Blues", vmin=0, vmax=vmax,
                   extent=[0.5, 12.5, -0.5, 23.5])
    ax.set_title(f"{title}, 2012-2025", fontsize=8)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([pd.Timestamp(2001, m, 1).strftime("%b")[0] for m in range(1, 13)])
    ax.set_xlabel("month")
axes[0].set_ylabel("hour of day (local time)")
fig.colorbar(im, ax=axes, label="% of hours")
fig.savefig(IMG / "rain-by-hour.png", bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# 8. an event-planning view: chance of a "nice" day, Sep-Nov

nice = (era5["tmax"] >= 18) & (era5["prcp"] < 1.0)
mat_nice = to_matrix(nice.astype(float), REF).to_numpy()
fig, ax = plt.subplots(figsize=(9, 3))
for w, alpha, label in [(0, 0.35, "single day"), (3, 1.0, "pooled +-3 days")]:
    ax.plot(x, pooled(mat_nice, w) * 100, color=COLORS["era5"], alpha=alpha, label=label)
lo, hi = bootstrap(mat_nice, 3)
ax.fill_between(x, lo * 100, hi * 100, color=COLORS["era5"], alpha=0.15, lw=0, label="95% interval")
ax.set_ylabel("%")
ax.set_title(f"Chance of a dry day (< 1 mm) with max >= 18 C, Plovdiv, ERA5 {REF[0]}-{REF[1]}")
ax.legend(fontsize=7)
date_axis(ax)
fig.tight_layout()
fig.savefig(IMG / "nice-day-autumn.png")
plt.close(fig)
results["nice_day_pct_ref"] = window_stats(mat_nice, wins, 100)

# ---------------------------------------------------------------------------
# 9. first autumn frost (station minimum < 0 C)

frost_dates = {}
for year in range(REF[0], REF[1] + 1):
    season = station_tmin.loc[f"{year}-08-01":f"{year}-12-31"].dropna()
    if len(season) < 140:
        continue
    frosty = season[season < 0]
    frost_dates[year] = int(doy365(pd.DatetimeIndex([frosty.index[0]]))[0]) if len(frosty) else 366
if frost_dates:
    days = np.array(list(frost_dates.values()))

    def as_date(d: float) -> str:
        return (pd.Timestamp("2001-01-01") + pd.Timedelta(days=int(round(d)) - 1)).strftime("%d %b")

    results["first_autumn_frost_station"] = {
        "years": len(days),
        "median": as_date(np.median(days)),
        "earliest": as_date(days.min()),
        "latest": as_date(days[days <= 365].max()) if (days <= 365).any() else None,
        "share_before_01_nov": round(float((days < doy365(pd.DatetimeIndex(["2001-11-01"]))[0]).mean()), 2),
        "share_before_15_nov": round(float((days < doy365(pd.DatetimeIndex(["2001-11-15"]))[0]).mean()), 2),
    }

# ---------------------------------------------------------------------------
# 10. the sequence version of the folk pattern: is early October warmer
#     after a wet late September?

seq = []
st_anom = station_tmax - pd.Series(
    harmonic_baseline(pooled(mat_t_ref, 0))[doy365(station_tmax.index) - 1], index=station_tmax.index)
for year in range(1960, 2026):
    late_sep = era5["wet"].loc[f"{year}-09-20":f"{year}-09-30"]
    early_oct = st_anom.loc[f"{year}-10-01":f"{year}-10-14"].dropna()
    if len(late_sep) == 11 and len(early_oct) >= 10:
        seq.append({"year": year, "wet_days_late_sep": int(late_sep.sum()), "early_oct_anom": float(early_oct.mean())})
seq = pd.DataFrame(seq)
wet_late = seq["wet_days_late_sep"] >= 3
results["wet_late_sep_then_warm_early_oct"] = {
    "years": int(len(seq)),
    "years_with_3plus_wet_days_late_sep": int(wet_late.sum()),
    "early_oct_tmax_anom_after_wet_late_sep_c": round(float(seq.loc[wet_late, "early_oct_anom"].mean()), 2),
    "early_oct_tmax_anom_after_dry_late_sep_c": round(float(seq.loc[~wet_late, "early_oct_anom"].mean()), 2),
    "share_warm_early_oct_after_wet": round(float((seq.loc[wet_late, "early_oct_anom"] > 0).mean()), 2),
    "share_warm_early_oct_after_dry": round(float((seq.loc[~wet_late, "early_oct_anom"] > 0).mean()), 2),
    "correlation_wet_days_vs_anom": round(float(seq[["wet_days_late_sep", "early_oct_anom"]].corr().iloc[0, 1]), 2),
}

OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(json.dumps(results, indent=2, ensure_ascii=False))
