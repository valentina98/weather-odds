"""Compare every data source with the Plovdiv measurements (phase-0 research, issue #3).

The owner asked to test all databases before anything is implemented. This
script compares each gridded source with the Plovdiv station (daily maximum
temperature, wet days) and the airport reports (rain by hour, thunder), and
derives the rain calibration that methodology section 10 needs.

Sources: ERA5 and ERA5-Land and ECMWF IFS (Open-Meteo AWS bucket), ERA5 and
CERRA through the Open-Meteo API, NASA POWER; measurements: NOAA GSOD +
Meteostat (temperature), GSOD 1973-1999 and NIMH 2022- (rain amounts), airport
reports LBPD (rain and thunder by hour, 2012-).

Writes docs/research/img/all-sources.png and docs/research/all-sources.json; the
write-up is in docs/research/all-sources.md.
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
from scale import daylight  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "research" / "img"
OUT_JSON = ROOT / "docs" / "research" / "all-sources.json"
RAIN_HOUR_MM = 0.2
COMMON = ("1991-01-01", "2021-06-30")  # all sources except ECMWF IFS (2017-) overlap here; CERRA ends June 2021
RECENT = ("2017-01-01", "2025-12-31")
COLORS = {"ERA5": "#d1495b", "ERA5 (Open-Meteo API)": "#f29e4c", "ERA5-Land": "#8e6c8a", "CERRA": "#2e933c",
          "ECMWF IFS": "#1b6ca8", "NASA POWER": "#9aa5b1", "Station": "#111827"}

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3, "font.size": 9})
results: dict = {}

# ---------------------------------------------------------------------------
# load

gsod = src.gsod()
station_tmax = gsod["tmax"].combine_first(src.meteostat_daily()["tmax"])
nimh = src.nimh()
daily = {
    "ERA5": src.grid_daily("copernicus_era5"),
    "ERA5 (Open-Meteo API)": src.open_meteo_daily("era5_seamless_daily"),
    "ERA5-Land": src.grid_daily("copernicus_era5_land"),
    "CERRA": src.open_meteo_daily("cerra_daily"),
    "ECMWF IFS": src.grid_daily("ecmwf_ifs"),
    "NASA POWER": src.nasa_power(),
}
# Precipitation of the hour before the time stamp; shift so each row is the hour that starts at its stamp,
# like the airport reports.
hourly = {
    "ERA5": src.era5_hourly("copernicus_era5")["precipitation"].shift(-1),
    "ERA5 (Open-Meteo API)": src.open_meteo_hourly("era5_seamless_hourly")["precipitation"].shift(-1),
    "CERRA": src.open_meteo_hourly("cerra_hourly")["precipitation"].shift(-1),
    "ECMWF IFS": src.era5_hourly("ecmwf_ifs")["precipitation"].shift(-1),
}
metar = src.metar_hourly().loc["2012":"2025"]

# ---------------------------------------------------------------------------
# 1. daily maximum temperature vs the station


def tmax_stats(period: tuple[str, str], names: list[str]) -> dict:
    out = {}
    for name in names:
        j = pd.concat([station_tmax.rename("st"), daily[name]["tmax"].rename("x")], axis=1).dropna().loc[period[0]:period[1]]
        diff = j["x"] - j["st"]
        month = diff.groupby(diff.index.month).mean()
        out[name] = {"days": int(len(j)), "bias_c": round(float(diff.mean()), 2),
                     "mean_abs_diff_c": round(float(diff.abs().mean()), 2), "corr": round(float(j.corr().iloc[0, 1]), 3),
                     "bias_jun_aug_c": round(float(month.loc[6:8].mean()), 2),
                     "bias_dec_feb_c": round(float(month.loc[[12, 1, 2]].mean()), 2),
                     "bias_by_month_c": {int(m): round(float(v), 2) for m, v in month.items()}}
    return out


results["tmax_vs_station"] = {
    f"{COMMON[0][:4]}-{COMMON[1][:4]}": tmax_stats(COMMON, ["ERA5", "ERA5 (Open-Meteo API)", "ERA5-Land", "CERRA", "NASA POWER"]),
    f"{RECENT[0][:4]}-{RECENT[1][:4]}": tmax_stats(RECENT, ["ERA5", "ERA5 (Open-Meteo API)", "ECMWF IFS", "NASA POWER"]),
}

# ---------------------------------------------------------------------------
# 2. wet days (>= 1 mm) vs the station


def wet_stats(station: pd.Series, names: list[str]) -> dict:
    out = {"Station": {"wet_day_share": round(float(station.mean()), 3), "days": int(len(station))}}
    for name in names:
        j = pd.concat([station.rename("st"), daily[name]["wet"].astype(float).rename("x")], axis=1).dropna()
        out[name] = {"wet_day_share": round(float(j["x"].mean()), 3), "agreement": round(float((j["x"] == j["st"]).mean()), 3),
                     "days": int(len(j)),
                     "by_month": {int(m): round(float(v), 3) for m, v in j["x"].groupby(j.index.month).mean().items()}}
    out["Station"]["by_month"] = {int(m): round(float(v), 3) for m, v in station.groupby(station.index.month).mean().items()}
    return out


gsod_wet = gsod["wet"].dropna().astype(float)
results["wet_days_vs_station"] = {
    "1985-1999 (GSOD)": wet_stats(gsod_wet.loc["1985":"1999"], ["ERA5", "ERA5 (Open-Meteo API)", "CERRA", "NASA POWER"]),
    "2022-2025 (NIMH)": wet_stats(nimh["wet"].astype(float).loc["2022":"2025"], ["ERA5", "ERA5 (Open-Meteo API)", "ECMWF IFS", "NASA POWER"]),
}

# ---------------------------------------------------------------------------
# 3. rain by hour vs the airport reports


def hourly_rain_stats(name: str, period: tuple[str, str]) -> dict:
    model = hourly[name].loc[period[0]:period[1]]
    obs = metar["rain"].loc[period[0]:period[1]]
    j = pd.concat([obs.astype(float).rename("obs"), (model >= RAIN_HOUR_MM).astype(float).rename("x")], axis=1).dropna()
    rain_obs, rain_x = j["obs"] == 1, j["x"] == 1
    return {"hours": int(len(j)), "airport_rain_share": round(float(rain_obs.mean()), 3),
            "model_rain_share": round(float(rain_x.mean()), 3),
            "hit_rate": round(float(rain_x[rain_obs].mean()), 3),  # model rains when the airport reports rain
            "false_alarm_ratio": round(float((~rain_obs)[rain_x].mean()), 3)}  # model rains, airport reports none


results["hourly_rain_vs_airport"] = {
    f"{COMMON[0][:4]}-{COMMON[1][:4]} ({'2012'}-{COMMON[1][:4]})": {
        n: hourly_rain_stats(n, ("2012-01-01", COMMON[1])) for n in ["ERA5", "ERA5 (Open-Meteo API)", "CERRA"]},
    "2017-2025": {n: hourly_rain_stats(n, RECENT) for n in ["ERA5", "ERA5 (Open-Meteo API)", "ECMWF IFS"]},
}

# ---------------------------------------------------------------------------
# 4. rain calibration for ERA5 (methodology section 10)


def wet_thresholds(model: pd.Series, station: pd.Series) -> dict:
    """Per month: the daily ERA5 amount whose exceedance frequency equals the station's wet-day frequency."""
    j = pd.concat([station.rename("st"), model.rename("x")], axis=1).dropna()
    return {int(m): round(float(g["x"].quantile(1 - g["st"].mean())), 1) for m, g in j.groupby(j.index.month)}


era5_prcp = daily["ERA5"]["prcp"]
era5_hour = hourly["ERA5"].loc["2012":"2025"]
obs_share = metar["rain"].mean()
results["calibration"] = {
    "era5_daily_wet_threshold_mm_vs_gsod_1973_1999": wet_thresholds(era5_prcp, gsod_wet.loc["1973":"1999"]),
    "era5_daily_wet_threshold_mm_vs_nimh_2022_2025": wet_thresholds(era5_prcp, nimh["wet"].astype(float).loc["2022":"2025"]),
    "airport_rainy_hour_share_2012_2025": round(float(obs_share), 4),
    "era5_hourly_threshold_mm_matching_airport": round(float(era5_hour.dropna().quantile(1 - obs_share)), 2),
}

# ---------------------------------------------------------------------------
# 5. thunder from the airport reports

day_of = metar.index.tz_localize(None).normalize()
thunder_day = metar["thunder"].groupby(day_of).any()
light = daylight(metar.index.tz_convert("UTC"))
results["thunder_airport_2012_2025"] = {
    "days_with_thunder_by_month": {int(m): round(float(v), 3) for m, v in thunder_day.groupby(thunder_day.index.month).mean().items()},
    "daylight_hours_with_thunder_by_month": {int(m): round(float(v), 4) for m, v in
                                             metar["thunder"][light].groupby(metar.index[light].month).mean().items()},
    "days": int(len(thunder_day)),
}

OUT_JSON.write_text(json.dumps(results, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in results.items() if k != "calibration"}, indent=1, ensure_ascii=False)[:6000])
print(json.dumps(results["calibration"], indent=1))

# ---------------------------------------------------------------------------
# chart

months = np.arange(1, 13)
fig, axes = plt.subplots(1, 3, figsize=(13, 3.9))
ax = axes[0]
for name, s in results["tmax_vs_station"][f"{COMMON[0][:4]}-{COMMON[1][:4]}"].items():
    ax.plot(months, [s["bias_by_month_c"][m] for m in months], marker="o", ms=3, color=COLORS[name], label=name)
ax.axhline(0, color="k", lw=0.8)
ax.set_title("Daily max: source minus station, 1991–2021", fontsize=9)
ax.set_ylabel("°C")
ax.legend(fontsize=7)
ax = axes[1]
wet = results["wet_days_vs_station"]["1985-1999 (GSOD)"]
for name, s in wet.items():
    ax.plot(months, [s["by_month"][m] * 100 for m in months], marker="o", ms=3, color=COLORS[name],
            lw=2.2 if name == "Station" else 1.2, label=name)
ax.set_title("Days with ≥ 1 mm rain, 1985–1999", fontsize=9)
ax.set_ylabel("% of days")
for a in axes[:2]:
    a.set_xticks(months)
    a.set_xlabel("month")
ax.legend(fontsize=7)
ax = axes[2]
summer = metar.index.month.isin([5, 6, 7])
hours = np.arange(24)
ax.plot(hours, metar["rain"][summer].groupby(metar.index[summer].hour).mean().reindex(hours) * 100, color=COLORS["Station"],
        lw=2.2, label="airport reports")
for name in ["ERA5", "CERRA"]:
    model = hourly[name].loc["2012-01-01":COMMON[1]]
    m = model[model.index.month.isin([5, 6, 7])] >= RAIN_HOUR_MM
    ax.plot(hours, m.groupby(m.index.hour).mean().reindex(hours) * 100, color=COLORS[name], label=f"{name} (≥ {RAIN_HOUR_MM} mm)")
ax.set_title("Rain by hour of day, May–July 2012–2021", fontsize=9)
ax.set_xlabel("local hour")
ax.set_ylabel("% of hours")
ax.set_xticks(range(0, 24, 3))
ax.legend(fontsize=7)
fig.tight_layout()
fig.savefig(IMG / "all-sources.png")
plt.close(fig)
print("done")
