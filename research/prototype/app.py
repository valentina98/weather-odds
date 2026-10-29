"""Throwaway dashboard prototype for issue #8 (phase-0 research, not the application).

Shows the calendar coloured by the outdoor-weather scale and a detail panel for
the selected day, week or month, so Streamlit can be judged on real screens.
Reads the ERA5 cache filled by `research/fetch_sources.py --sources aws`.

Run:  .venv/bin/streamlit run research/prototype/app.py
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import load_sources as src  # noqa: E402
from daystats import doy365  # noqa: E402
from scale import CLASSES, GOOD, Thresholds, class_of, daylight, hour_factors, period_scores, sun_hours_utc  # noqa: E402

# Stands in for config.yaml (requirement F18).
CONFIG = {"reference_years": 30, "trend_adjustment": True, "pooling_days": 7}
LAST_COMPLETE_YEAR = 2025
FIRST_YEAR = 1961
TODAY = dt.date.today()
MEASURES = {"Chance of good weather": "chance", "Average score": "mean"}
LIMITS = {"temperature": "temperature", "rain": "rain", "wind": "wind"}

st.set_page_config(page_title="weather-odds prototype", layout="wide")


@st.cache_data
def load_hourly() -> pd.DataFrame:
    hourly = src.era5_hourly("copernicus_era5")[["temperature_2m", "precipitation", "wind_gusts_10m"]]
    hourly = hourly.loc[str(FIRST_YEAR):str(LAST_COMPLETE_YEAR)].copy()
    hourly["daylight"] = daylight(hourly.index.tz_convert("UTC"))
    return hourly


@st.cache_data
def daily_table(years: tuple[int, int], hours: tuple[int, int] | None, trend: bool,
                th: Thresholds) -> tuple[pd.DataFrame, float]:
    """One row per past day: score and the numbers the detail panel needs, for the chosen hours."""
    hourly = load_hourly()
    hourly = hourly[(hourly.index.year >= years[0]) & (hourly.index.year <= years[1])]
    chosen = hourly["daylight"] if hours is None else (hourly.index.hour >= hours[0]) & (hourly.index.hour < hours[1])
    hourly = hourly[chosen].copy()
    slope = 0.0
    if trend:  # shift each year's temperatures by the fitted warming trend, up to this year
        annual = hourly["temperature_2m"].groupby(hourly.index.year).mean()
        slope = float(np.polyfit(annual.index, annual.to_numpy(), 1)[0])
        hourly["temperature_2m"] += slope * (TODAY.year - hourly.index.year)
    factors = hour_factors(hourly, th)
    day = hourly.index.tz_localize(None).normalize()
    temp = hourly["temperature_2m"].groupby(day)
    out = pd.DataFrame({
        "score": period_scores(hourly, th),
        "tmax": temp.max(),
        "tmin": temp.min(),
        "rain_any": (hourly["precipitation"] >= 0.2).groupby(day).any(),
        "rain_mm": hourly["precipitation"].groupby(day).sum(),
        "gust": hourly["wind_gusts_10m"].groupby(day).max(),
        **{f"lack_{k}": (1 - factors[k]).groupby(day).mean() for k in LIMITS},
    })
    out = out[~((out.index.month == 2) & (out.index.day == 29))]
    out["doy"] = doy365(out.index)
    out["good"] = out["score"] >= GOOD
    return out, slope


def cells(start: dt.date, end: dt.date, granularity: str) -> pd.DataFrame:
    """The calendar cells of the timeframe with the target dates each one covers."""
    dates = pd.date_range(start, end)
    if granularity == "Day":
        keys = dates
    elif granularity == "Week":
        keys = dates - pd.to_timedelta(dates.day_of_week, unit="D")
    else:
        keys = dates.to_period("M").to_timestamp()
    frame = pd.DataFrame({"key": keys, "date": dates})
    out = frame.groupby("key")["date"].agg(["min", "max", list]).reset_index()
    return out.rename(columns={"min": "first", "max": "last", "list": "dates"})


def past_days(daily: pd.DataFrame, dates: list, pool: int) -> pd.DataFrame:
    """Past days whose day of year matches the cell's dates (+-pool days for a single day)."""
    doys = set(doy365(pd.DatetimeIndex(dates)))
    if len(dates) == 1:
        d = next(iter(doys))
        doys = {(d - 1 + s) % 365 + 1 for s in range(-pool, pool + 1)}
    return daily[daily["doy"].isin(doys)]


def label(row) -> str:
    if row["first"] == row["last"]:
        return row["first"].strftime("%d.%m.%Y")
    return f'{row["first"]:%d.%m.}–{row["last"]:%d.%m.%Y}'


# ---------------------------------------------------------------------------
# sidebar: inputs (requirements F5-F8, F10, F17, F19, F27, F28)

hourly_all = load_hourly()
with st.sidebar:
    st.header("weather-odds · Plovdiv")
    start = st.date_input("From", TODAY, format="DD.MM.YYYY")
    end = st.date_input("To", TODAY + pd.DateOffset(months=3), format="DD.MM.YYYY")
    granularity = st.radio("Granularity", ["Day", "Week", "Month"], index=1, horizontal=True)
    pick_hours = st.toggle("Choose the time of day", value=False, help="Off: daylight hours (sunrise to sunset).")
    hours = st.slider("Hours", 0, 24, (17, 22)) if pick_hours else None
    measure = MEASURES[st.radio("Colour shows", list(MEASURES), index=0)]
    relative = st.radio("Colours", ["Absolute", "Relative to this timeframe"], index=0) != "Absolute"
    years = st.slider("Reference years", FIRST_YEAR, LAST_COMPLETE_YEAR,
                      (LAST_COMPLETE_YEAR - CONFIG["reference_years"] + 1, LAST_COMPLETE_YEAR))
    trend = st.toggle("Adjust temperatures for warming", value=CONFIG["trend_adjustment"],
                      help="Shifts older years by the warming trend fitted to the reference years.")
    pool = st.slider("Pooling for single days (± days)", 0, 15, CONFIG["pooling_days"])
    with st.expander("Scale thresholds"):
        comfort = st.slider("No penalty between (°C)", 5, 35, (18, 26))
        cold_zero = st.slider("Worst cold at (°C)", -15, 15, 0)
        hot_zero = st.slider("Worst heat at (°C)", 30, 45, 38)
        gust_zero = st.slider("Worst gusts at (km/h)", 40, 120, 75)
    th = Thresholds(comfort=(float(comfort[0]), float(comfort[1])), cold_zero=float(cold_zero),
                    hot_zero=float(hot_zero), gust_zero=float(gust_zero))

if end <= start:
    st.error("The end date must be after the start date.")
    st.stop()

daily, slope = daily_table(years, hours, trend, th)
grid = cells(start, end, granularity)
values = []
for row in grid.itertuples():
    past = past_days(daily, row.dates, pool)
    values.append((past["good"].mean() * 100, past["score"].mean(), len(past)))
grid[["chance", "mean", "n"]] = values
grid["value"] = grid[measure]
grid["colour"] = grid["value"]
if relative and grid["value"].max() > grid["value"].min():
    grid["colour"] = (grid["value"] - grid["value"].min()) / (grid["value"].max() - grid["value"].min()) * 100
grid["label"] = grid.apply(label, axis=1)
grid["key"] = grid["key"].dt.strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# header

hours_text = "daylight hours" if hours is None else f"{hours[0]:02d}:00–{hours[1]:02d}:00"
st.markdown(f"**Usually good weather for being outdoors?** {start:%d.%m.%Y}–{end:%d.%m.%Y}, {hours_text}, "
            f"based on {years[0]}–{years[1]} ({years[1] - years[0] + 1} years). *Not a forecast.*")
if trend:
    st.caption(f"Temperatures adjusted to the {TODAY.year} climate: trend {slope * 10:+.2f} °C per decade, "
               f"so {years[0]} is shifted by {slope * (TODAY.year - years[0]):+.1f} °C.")
if relative:
    st.caption("Relative colours: green = best cell in this timeframe, red = worst. Hover for the absolute value.")

tab_calendar, tab_patterns, tab_data = st.tabs(["Calendar", "Patterns", "Data"])

# ---------------------------------------------------------------------------
# calendar (F10, F25, F26)

with tab_calendar:
    pick = alt.selection_point(fields=["key"], name="cell")
    colour = alt.Color("colour:Q", scale=alt.Scale(scheme="redyellowgreen", domain=[0, 100]), legend=None)
    tooltip = [alt.Tooltip("label:N", title="Period"), alt.Tooltip("chance:Q", title="Chance of good weather (%)", format=".0f"),
               alt.Tooltip("mean:Q", title="Average score", format=".0f"), alt.Tooltip("n:Q", title="Past days")]
    if granularity == "Day":
        grid["weekday"] = pd.to_datetime(grid["key"]).dt.strftime("%a")
        grid["week"] = (pd.to_datetime(grid["key"]) - pd.to_timedelta(pd.to_datetime(grid["key"]).dt.day_of_week, unit="D")).dt.strftime("%d.%m.")
        grid["text"] = pd.to_datetime(grid["key"]).dt.strftime("%d")
        position = {
            "x": alt.X("weekday:N", sort=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], title=None,
                       axis=alt.Axis(orient="top", labelAngle=0)),
            "y": alt.Y("week:N", sort=None, title="Week starting"),
        }
        size = {"width": 420, "height": 26 * grid["week"].nunique()}
    else:  # one row of week or month cells, each showing its value
        grid["text"] = grid["value"].round().astype(int).astype(str)
        starts = pd.to_datetime(grid["key"])
        grid["short"] = starts.dt.strftime("%d.%m.") if granularity == "Week" else starts.dt.strftime("%b %Y")
        grid["row"] = granularity  # a non-empty constant: one row
        position = {"x": alt.X("short:N", sort=None, title="Week starting" if granularity == "Week" else None,
                               axis=alt.Axis(labelAngle=0)),
                    "y": alt.Y("row:N", title=None, axis=None)}
        size = {"width": (62 if granularity == "Week" else 150) * len(grid), "height": 130}  # includes the axis
    base = alt.Chart(grid).encode(**position)
    rect = base.mark_rect(stroke="white", strokeWidth=2, cursor="pointer").encode(
        color=colour, tooltip=tooltip, opacity=alt.condition(pick, alt.value(1), alt.value(0.75))).add_params(pick)
    text = base.mark_text(fontSize=12).encode(text="text:N", tooltip=tooltip)
    event = st.altair_chart((rect + text).properties(**size), on_select="rerun", key="calendar", width="content")

    legend_label = "% of past days Good or Great" if measure == "chance" else "average score"
    scale_text = "relative to this timeframe" if relative else "red 0 → yellow 50 → green 100"
    st.caption(f"Colour: {legend_label}, {scale_text}. Numbers are absolute. Click a cell for details.")

    selected = event.selection.get("cell", []) if event and event.selection else []
    # A selection made at another granularity does not match any cell here.
    matches = grid[grid["key"] == selected[0]["key"]] if selected else grid.iloc[:0]
    if len(matches):
        row = matches.iloc[0]
        past = past_days(daily, row["dates"], pool)
        st.subheader(row["label"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Chance of good weather", f'{past["good"].mean():.0%}')
        c2.metric("Average score", f'{past["score"].mean():.0f}', help=class_of(past["score"].mean()))
        c3.metric("Max temperature (median)", f'{past["tmax"].median():.0f} °C',
                  help=f'10–90%: {past["tmax"].quantile(.1):.0f}–{past["tmax"].quantile(.9):.0f} °C')
        c4.metric("Rain during the hours", f'{past["rain_any"].mean():.0%}', help="≥ 0.2 mm in at least one hour")

        left, right = st.columns([1, 1])
        with left:
            classes = pd.DataFrame([(name, colour_hex, ((past["score"] >= low) & (past["score"] < high)).mean() * 100)
                                    for (low, name, colour_hex), high in zip(CLASSES, [101, 80, 60, 40, 20])],
                                   columns=["class", "hex", "share"])
            st.altair_chart(alt.Chart(classes).mark_bar().encode(
                x=alt.X("share:Q", title="% of past days"), y=alt.Y("class:N", sort=None, title=None),
                color=alt.Color("hex:N", scale=None)).properties(height=230, title="How past days rated"))
        with right:
            not_good = past[~past["good"]]
            if len(not_good):
                lack = {k: not_good[f"lack_{k}"].mean() for k in LIMITS}
                worst = max(lack, key=lack.get)
                too = "cold" if worst == "temperature" and not_good["tmax"].median() < th.comfort[0] else (
                    "heat" if worst == "temperature" else worst)
                st.markdown(f"**What spoiled the other days:** mostly **{too}**.")
            doys = doy365(pd.DatetimeIndex(row["dates"]))
            rise, set_ = sun_hours_utc(doys)
            local = pd.Timestamp(row["dates"][0]).tz_localize("Europe/Sofia").utcoffset().total_seconds() / 3600
            fmt = lambda h: f"{int(h + local):02d}:{int(round((h + local) % 1 * 60)) % 60:02d}"  # noqa: E731
            st.markdown(
                f"- Heat (≥ 32 °C): {(past['tmax'] >= 32).mean():.0%} · below 0 °C: {(past['tmin'] < 0).mean():.0%}\n"
                f"- Strong gusts (≥ 50 km/h): {(past['gust'] >= 50).mean():.0%} · ≥ 1 mm rain: {(past['rain_mm'] >= 1).mean():.0%}\n"
                f"- Sunrise {fmt(rise.min())}–{fmt(rise.max())}, sunset {fmt(set_.min())}–{fmt(set_.max())}\n"
                f"- Based on {len(past)} past days, {years[0]}–{years[1]}"
                + (f" (±{pool} days around the date)" if len(row['dates']) == 1 else ""))
    else:
        st.info("Click a day, week or month in the calendar to see the details.")

with tab_patterns:
    st.markdown("Prototype: the Patterns tab will list tendencies that pass the tests in the methodology. "
                "So far none at Plovdiv; see the research write-ups.")
    st.image(str(Path(__file__).resolve().parents[2] / "docs" / "research" / "img" / "warm-spells.png"))

with tab_data:
    st.markdown(
        f"- **ERA5** hourly reanalysis (25 km), {years[0]}–{years[1]}, read from Open-Meteo's AWS open data. "
        "Contains modified Copernicus Climate Change Service information; CC BY 4.0.\n"
        "- Temperatures shifted to the Plovdiv station's elevation (179 m).\n"
        "- Not yet: station calibration (GSOD, NIMH, airport reports), thunder, CERRA.")
