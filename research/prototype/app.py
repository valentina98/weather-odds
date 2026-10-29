"""Throwaway dashboard prototype in Streamlit for issue #8 (phase-0 research, not the application).

Shows the calendar coloured by the outdoor-weather scale and a detail panel for
the selected day, week or month, so Streamlit can be judged on real screens.
The Dash version with the same screens is dash_app.py; both use model.py.
Reads the ERA5 cache filled by `research/fetch_sources.py --sources aws`.

Run:  .venv/bin/streamlit run research/prototype/app.py
"""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from model import CONFIG, DEFAULT_YEARS, FIRST_YEAR, LAST_COMPLETE_YEAR, TODAY, calendar_grid, daily_table, details
from scale import Thresholds

MEASURES = {"Chance of good weather": "chance", "Average score": "mean"}

st.set_page_config(page_title="weather-odds prototype", layout="wide")

# ---------------------------------------------------------------------------
# sidebar: inputs (requirements F5-F8, F10, F17, F19, F27, F28)

with st.sidebar:
    st.header("weather-odds · Plovdiv")
    start = st.date_input("From", TODAY, format="DD.MM.YYYY")
    end = st.date_input("To", TODAY + pd.DateOffset(months=3), format="DD.MM.YYYY")
    granularity = st.radio("Granularity", ["Day", "Week", "Month"], index=1, horizontal=True)
    pick_hours = st.toggle("Choose the time of day", value=False, help="Off: daylight hours (sunrise to sunset).")
    hours = st.slider("Hours", 0, 24, (17, 22)) if pick_hours else None
    measure = MEASURES[st.radio("Colour shows", list(MEASURES), index=0)]
    relative = st.radio("Colours", ["Absolute", "Relative to this timeframe"], index=0) != "Absolute"
    years = st.slider("Reference years", FIRST_YEAR, LAST_COMPLETE_YEAR, DEFAULT_YEARS)
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

daily, slope = daily_table(tuple(years), tuple(hours) if hours else None, trend, th)
grid = calendar_grid(daily, start, end, granularity, pool, measure, relative)

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
    starts = pd.to_datetime(grid["key"])
    if granularity == "Day":
        grid["weekday"] = starts.dt.strftime("%a")
        grid["week"] = (starts - pd.to_timedelta(starts.dt.day_of_week, unit="D")).dt.strftime("%d.%m.")
        grid["text"] = starts.dt.strftime("%d")
        position = {
            "x": alt.X("weekday:N", sort=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], title=None,
                       axis=alt.Axis(orient="top", labelAngle=0)),
            "y": alt.Y("week:N", sort=None, title="Week starting"),
        }
        size = {"width": 420, "height": 26 * grid["week"].nunique()}
    else:  # one row of week or month cells, each showing its value
        grid["text"] = grid["value"].round().astype(int).astype(str)
        grid["short"] = starts.dt.strftime("%d.%m.") if granularity == "Week" else starts.dt.strftime("%b %Y")
        grid["row"] = granularity  # a non-empty constant: one row
        position = {"x": alt.X("short:N", sort=None, title="Week starting" if granularity == "Week" else None,
                               axis=alt.Axis(labelAngle=0)),
                    "y": alt.Y("row:N", title=None, axis=None)}
        size = {"width": (62 if granularity == "Week" else 150) * len(grid), "height": 130}  # includes the axis
    base = alt.Chart(grid.drop(columns=["first", "last", "dates"])).encode(**position)
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
        d = details(daily, row["dates"], pool, th)
        st.subheader(row["label"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Chance of good weather", f'{d["chance"]:.0f}%')
        c2.metric("Average score", f'{d["mean"]:.0f}', help=d["class"])
        c3.metric("Max temperature (median)", f'{d["tmax_median"]:.0f} °C',
                  help=f'10–90%: {d["tmax_p10"]:.0f}–{d["tmax_p90"]:.0f} °C')
        c4.metric("Rain during the hours", f'{d["rain_any"]:.0f}%', help="≥ 0.2 mm in at least one hour")

        left, right = st.columns([1, 1])
        with left:
            classes = pd.DataFrame(d["classes"], columns=["class", "hex", "share"])
            st.altair_chart(alt.Chart(classes).mark_bar().encode(
                x=alt.X("share:Q", title="% of past days"), y=alt.Y("class:N", sort=None, title=None),
                color=alt.Color("hex:N", scale=None)).properties(height=230, title="How past days rated"))
        with right:
            if d["spoiled"]:
                st.markdown(f'**What spoiled the other days:** mostly **{d["spoiled"]}**.')
            st.markdown(
                f'- Heat (≥ 32 °C): {d["heat"]:.0f}% · below 0 °C: {d["frost"]:.0f}%\n'
                f'- Strong gusts (≥ 50 km/h): {d["gusts"]:.0f}% · ≥ 1 mm rain: {d["rain_1mm"]:.0f}%\n'
                f'- Sunrise {d["sunrise"]}, sunset {d["sunset"]}\n'
                f'- Based on {d["days"]} past days, {years[0]}–{years[1]}'
                + (f" (±{pool} days around the date)" if d["pooled"] else ""))
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
