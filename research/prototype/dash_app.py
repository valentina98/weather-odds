"""Throwaway dashboard prototype in Dash for issue #8 (phase-0 research, not the application).

The same screens as the Streamlit prototype (app.py), built with Dash so the two
can be compared. Both use model.py for the data and statistics.
Reads the ERA5 cache filled by `research/fetch_sources.py --sources aws`.

Run:  .venv/bin/python research/prototype/dash_app.py   (then open http://localhost:8050)
"""

from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, no_update

from model import CONFIG, DEFAULT_YEARS, FIRST_YEAR, LAST_COMPLETE_YEAR, TODAY, calendar_grid, daily_table, details
from scale import Thresholds

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
IMG = Path(__file__).resolve().parents[2] / "docs" / "research" / "img"
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
LABEL = {"fontSize": 13, "fontWeight": 600, "margin": "14px 0 4px"}
CARD = {"flex": 1, "padding": "10px 14px", "border": "1px solid #e3e6ea", "borderRadius": 8}


def control(title: str, component, note: str | None = None) -> html.Div:
    return html.Div([html.Div(title, style=LABEL), component] + ([html.Div(note, style={"fontSize": 11, "color": "#6b7280"})] if note else []))


def inline_image(name: str) -> str:
    return "data:image/png;base64," + base64.b64encode((IMG / name).read_bytes()).decode()


sidebar = html.Div([
    html.H3("weather-odds · Plovdiv", style={"marginTop": 0}),
    control("From", dcc.DatePickerSingle(id="start", date=TODAY, display_format="DD.MM.YYYY", first_day_of_week=1)),
    control("To", dcc.DatePickerSingle(id="end", date=(TODAY + pd.DateOffset(months=3)).date(),
                                       display_format="DD.MM.YYYY", first_day_of_week=1)),
    control("Granularity", dcc.RadioItems(["Day", "Week", "Month"], "Week", id="granularity", inline=True,
                                          inputStyle={"marginRight": 4}, labelStyle={"marginRight": 12})),
    control("Time of day", dcc.Checklist([{"label": " choose hours (otherwise daylight)", "value": "on"}], [], id="pick-hours")),
    dcc.RangeSlider(0, 24, 1, value=[17, 22], id="hours", marks={h: f"{h}" for h in range(0, 25, 6)},
                    tooltip={"placement": "bottom"}, disabled=True),
    control("Colour shows", dcc.RadioItems({"chance": " Chance of good weather", "mean": " Average score"}, "chance",
                                           id="measure")),
    control("Colours", dcc.RadioItems({"abs": " Absolute", "rel": " Relative to this timeframe"}, "abs", id="colours")),
    control("Reference years", dcc.RangeSlider(FIRST_YEAR, LAST_COMPLETE_YEAR, 1, value=list(DEFAULT_YEARS), id="years",
                                               marks={y: str(y) for y in (1961, 1980, 2000, 2025)},
                                               tooltip={"placement": "bottom"})),
    dcc.Checklist([{"label": " Adjust temperatures for warming", "value": "on"}],
                  ["on"] if CONFIG["trend_adjustment"] else [], id="trend", style={"marginTop": 10}),
    control("Pooling for single days (± days)", dcc.Slider(0, 15, 1, value=CONFIG["pooling_days"], id="pool",
                                                            marks={0: "0", 7: "7", 15: "15"}, tooltip={"placement": "bottom"})),
    html.Details([
        html.Summary("Scale thresholds", style={"cursor": "pointer", "marginTop": 14}),
        control("No penalty between (°C)", dcc.RangeSlider(5, 35, 1, value=[18, 26], id="comfort", marks=None,
                                                            tooltip={"placement": "bottom", "always_visible": True})),
        control("Worst cold at (°C)", dcc.Slider(-15, 15, 1, value=0, id="cold", marks=None,
                                                 tooltip={"placement": "bottom", "always_visible": True})),
        control("Worst heat at (°C)", dcc.Slider(30, 45, 1, value=38, id="hot", marks=None,
                                                 tooltip={"placement": "bottom", "always_visible": True})),
        control("Worst gusts at (km/h)", dcc.Slider(40, 120, 5, value=75, id="gust", marks=None,
                                                    tooltip={"placement": "bottom", "always_visible": True})),
    ]),
], style={"width": 270, "padding": "24px 20px", "background": "#f4f6f8", "minHeight": "100vh", "boxSizing": "border-box"})

main = html.Div([
    html.Div(id="header", style={"marginBottom": 16}),
    dcc.Tabs([
        dcc.Tab(label="Calendar", children=[
            dcc.Graph(id="calendar", config={"displayModeBar": False}),
            html.Div(id="caption", style={"fontSize": 12, "color": "#6b7280"}),
            html.Div(id="detail", style={"marginTop": 18}),
        ]),
        dcc.Tab(label="Patterns", children=[
            html.P("Prototype: the Patterns tab will list tendencies that pass the tests in the methodology. "
                   "So far none at Plovdiv; see the research write-ups."),
            html.Img(src=inline_image("warm-spells.png"), style={"maxWidth": "100%"}),
        ]),
        dcc.Tab(label="Data", children=[dcc.Markdown(
            "- **ERA5** hourly reanalysis (25 km), read from Open-Meteo's AWS open data. "
            "Contains modified Copernicus Climate Change Service information; CC BY 4.0.\n"
            "- Temperatures shifted to the Plovdiv station's elevation (179 m).\n"
            "- Not yet: station calibration (GSOD, NIMH, airport reports), thunder, CERRA.")]),
    ]),
    dcc.Store(id="selected"),
    dcc.Store(id="cells"),  # "x|y" of each heatmap cell -> its key (heatmap clicks carry no customdata)
], style={"flex": 1, "padding": "24px 36px", "minWidth": 0})

app = Dash(__name__, title="weather-odds prototype")
app.layout = html.Div([sidebar, main], style={"display": "flex", "fontFamily": FONT, "color": "#1f2937"})

INPUTS = [Input(i, p) for i, p in [("start", "date"), ("end", "date"), ("granularity", "value"), ("pick-hours", "value"),
                                     ("hours", "value"), ("measure", "value"), ("colours", "value"), ("years", "value"),
                                     ("trend", "value"), ("pool", "value"), ("comfort", "value"), ("cold", "value"),
                                     ("hot", "value"), ("gust", "value")]]


def compute(start, end, granularity, pick_hours, hours, measure, colours, years, trend, pool, comfort, cold, hot, gust):
    th = Thresholds(comfort=(float(comfort[0]), float(comfort[1])), cold_zero=float(cold), hot_zero=float(hot),
                    gust_zero=float(gust))
    chosen = tuple(hours) if pick_hours else None
    daily, slope = daily_table(tuple(years), chosen, bool(trend), th)
    grid = calendar_grid(daily, pd.Timestamp(start).date(), pd.Timestamp(end).date(), granularity, pool, measure,
                         colours == "rel")
    return th, chosen, daily, slope, grid


@app.callback(Output("hours", "disabled"), Input("pick-hours", "value"))
def toggle_hours(pick_hours):
    return not pick_hours


@app.callback(Output("calendar", "figure"), Output("header", "children"), Output("caption", "children"),
              Output("cells", "data"), *INPUTS, Input("selected", "data"))
def update_calendar(start, end, granularity, pick_hours, hours, measure, colours, years, trend, pool, comfort, cold,
                    hot, gust, selected):
    th, chosen, daily, slope, grid = compute(start, end, granularity, pick_hours, hours, measure, colours, years,
                                             trend, pool, comfort, cold, hot, gust)
    starts = pd.to_datetime(grid["key"])
    hover = ("%{customdata[1]}<br>Chance of good weather: %{customdata[2]:.0f}%<br>"
             "Average score: %{customdata[3]:.0f}<br>Past days: %{customdata[4]}<extra></extra>")
    custom = grid[["key", "label", "chance", "mean", "n"]].to_numpy()
    if granularity == "Day":
        weeks = (starts - pd.to_timedelta(starts.dt.day_of_week, unit="D")).dt.strftime("%d.%m.")
        rows = list(dict.fromkeys(weeks))
        z = pd.DataFrame(index=rows, columns=WEEKDAYS, dtype=float)
        text = pd.DataFrame("", index=rows, columns=WEEKDAYS)
        data = pd.DataFrame(index=rows, columns=WEEKDAYS, dtype=object)
        for w, day, colour, label, c in zip(weeks, starts, grid["colour"], grid["label"], custom):
            z.loc[w, WEEKDAYS[day.day_of_week]] = colour
            text.loc[w, WEEKDAYS[day.day_of_week]] = f"{day:%d}"
            data.loc[w, WEEKDAYS[day.day_of_week]] = list(c)
        heat = go.Heatmap(z=z.to_numpy(), x=WEEKDAYS, y=rows, text=text.to_numpy(), texttemplate="%{text}",
                          customdata=[[v if isinstance(v, list) else ["", "", 0, 0, 0] for v in r] for r in data.to_numpy()],
                          hovertemplate=hover)
        height, xs, ys = 34 * len(rows) + 50, WEEKDAYS, rows
        cell_of = {c[0]: (WEEKDAYS[d.day_of_week], w) for c, d, w in zip(custom, starts, weeks)}
    else:
        short = starts.dt.strftime("%d.%m.") if granularity == "Week" else starts.dt.strftime("%b %Y")
        heat = go.Heatmap(z=[grid["colour"].tolist()], x=list(short), y=[""], text=[grid["value"].round().astype(int).tolist()],
                          texttemplate="%{text}", customdata=[custom.tolist()], hovertemplate=hover)
        height, xs, ys = 110, list(short), [""]
        cell_of = {c[0]: (s, "") for c, s in zip(custom, short)}
    heat.update(colorscale="RdYlGn", zmin=0, zmax=100, xgap=3, ygap=3, showscale=False)
    fig = go.Figure(heat)
    if selected in cell_of:  # outline the selected cell
        x, y = cell_of[selected]
        xi, yi = xs.index(x), ys.index(y)
        fig.add_shape(type="rect", x0=xi - 0.5, x1=xi + 0.5, y0=yi - 0.5, y1=yi + 0.5, line={"color": "#111827", "width": 3})
    fig.update_layout(height=height, margin={"l": 60, "r": 10, "t": 30 if granularity == "Day" else 10, "b": 30},
                      plot_bgcolor="white", font={"family": FONT, "size": 13},
                      xaxis={"side": "top" if granularity == "Day" else "bottom", "fixedrange": True, "type": "category"},
                      yaxis={"autorange": "reversed", "fixedrange": True, "type": "category",
                             "title": "Week starting" if granularity == "Day" else None})
    if granularity != "Day":
        fig.update_layout(width=max(420, (66 if granularity == "Week" else 150) * len(grid)))

    hours_text = "daylight hours" if chosen is None else f"{chosen[0]:02d}:00–{chosen[1]:02d}:00"
    header = [html.Div([html.B("Usually good weather for being outdoors? "),
                        f"{pd.Timestamp(start):%d.%m.%Y}–{pd.Timestamp(end):%d.%m.%Y}, {hours_text}, based on "
                        f"{years[0]}–{years[1]} ({years[1] - years[0] + 1} years). ", html.I("Not a forecast.")])]
    if trend:
        header.append(html.Div(f"Temperatures adjusted to the {TODAY.year} climate: trend {slope * 10:+.2f} °C per decade, "
                               f"so {years[0]} is shifted by {slope * (TODAY.year - years[0]):+.1f} °C.",
                               style={"fontSize": 12, "color": "#6b7280", "marginTop": 6}))
    legend = "% of past days Good or Great" if measure == "chance" else "average score"
    scale_text = "relative to this timeframe" if colours == "rel" else "red 0 → yellow 50 → green 100"
    cells = {f"{x}|{y}": key for key, (x, y) in cell_of.items()}
    return fig, header, f"Colour: {legend}, {scale_text}. Numbers are absolute. Click a cell for details.", cells


@app.callback(Output("selected", "data"), Input("calendar", "clickData"), State("cells", "data"), prevent_initial_call=True)
def select(click, cells):
    if not click:
        return no_update
    point = click["points"][0]
    return (cells or {}).get(f'{point["x"]}|{point["y"]}', no_update)


@app.callback(Output("detail", "children"), Input("selected", "data"), *INPUTS)
def update_detail(selected, *args):
    th, chosen, daily, slope, grid = compute(*args)
    pool, years = args[9], args[7]
    matches = grid[grid["key"] == selected]
    if not len(matches):
        return html.Div("Click a day, week or month in the calendar to see the details.",
                        style={"padding": 14, "background": "#eef4fb", "borderRadius": 8, "color": "#1d4f91"})
    row = matches.iloc[0]
    d = details(daily, row["dates"], pool, th)
    cards = [("Chance of good weather", f'{d["chance"]:.0f}%'), ("Average score", f'{d["mean"]:.0f} ({d["class"]})'),
             ("Max temperature (median)", f'{d["tmax_median"]:.0f} °C'), ("Rain during the hours", f'{d["rain_any"]:.0f}%')]
    bars = go.Figure(go.Bar(x=[s for _, _, s in d["classes"]], y=[n for n, _, _ in d["classes"]], orientation="h",
                            marker_color=[c for _, c, _ in d["classes"]], hovertemplate="%{y}: %{x:.0f}%<extra></extra>"))
    bars.update_layout(height=220, margin={"l": 60, "r": 10, "t": 30, "b": 40}, title={"text": "How past days rated", "font": {"size": 14}},
                       xaxis={"title": "% of past days"}, yaxis={"autorange": "reversed"}, plot_bgcolor="white",
                       font={"family": FONT})
    facts = [f'Heat (≥ 32 °C): {d["heat"]:.0f}% · below 0 °C: {d["frost"]:.0f}%',
             f'Strong gusts (≥ 50 km/h): {d["gusts"]:.0f}% · ≥ 1 mm rain: {d["rain_1mm"]:.0f}%',
             f'Sunrise {d["sunrise"]}, sunset {d["sunset"]}',
             f'Based on {d["days"]} past days, {years[0]}–{years[1]}' + (f" (±{pool} days around the date)" if d["pooled"] else ""),
             f'Max temperature 10–90%: {d["tmax_p10"]:.0f}–{d["tmax_p90"]:.0f} °C']
    return [
        html.H2(row["label"], style={"margin": "0 0 12px"}),
        html.Div([html.Div([html.Div(t, style={"fontSize": 13, "color": "#4b5563"}), html.Div(v, style={"fontSize": 30})],
                           style=CARD) for t, v in cards], style={"display": "flex", "gap": 12}),
        html.Div([
            html.Div(dcc.Graph(figure=bars, config={"displayModeBar": False}), style={"flex": 1}),
            html.Div([html.P([html.B("What spoiled the other days: "), f'mostly {d["spoiled"]}.']) if d["spoiled"] else None,
                      html.Ul([html.Li(f) for f in facts])], style={"flex": 1, "paddingTop": 20}),
        ], style={"display": "flex", "gap": 24, "marginTop": 12}),
    ]


if __name__ == "__main__":
    app.run(debug=False, port=8050)
