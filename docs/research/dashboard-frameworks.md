# Dashboard frameworks

_Checked on 2026-10-29 for issue [#8](https://github.com/valentina98/weather-odds/issues/8). Versions and licences are from PyPI; the click-event APIs were confirmed in each package's released code._

**Recommendation: Streamlit for v1.** It needs the least code for our screens, and another developer starts it with one command. It also reports clicks on a chart, which the calendar needs to open the detail panel. If its full-page reruns or limited layout control get in the way, **Dash** is the fallback. The statistics stay in a separate package (see [architecture](../spec/architecture.md)), so switching frameworks later only means rewriting the screens.

## What the dashboard has to do

From the answers in [#10](https://github.com/valentina98/weather-odds/issues/10) and [#6](https://github.com/valentina98/weather-odds/issues/6):

- Controls: timeframe (default today + 3 months), optional time of day (default daytime), granularity (default week), and a reference-year range narrower than the configured default.
- Main view: a calendar coloured green to red by the weather-quality scale.
- Clicking a day, week or month cell opens a detail panel for that period and time of day.
- Two more tabs: Patterns and Data.
- It runs locally only, and another developer can install and start it with documented commands.

## Comparison

| Framework (version, licence) | How it works | Pros for weather-odds | Cons for weather-odds |
|---|---|---|---|
| **Streamlit** 1.66 (Apache-2.0) | A Python script that re-runs top to bottom on every interaction; results are cached. | Least code. Built-in sidebar, columns, tabs and date inputs. `st.plotly_chart` and `st.altair_chart` return clicked points (`on_select`), enough for "click a cell, show details". Large community, good docs. Built-in app testing (`AppTest`). Start: `streamlit run app.py`. | Every click re-runs the script, so heavy steps must be cached explicitly. Limited control over exact layout and styling. Click selection works on point-like marks: the calendar has to be drawn as square markers (Plotly) or `rect` marks (Altair), not as a Plotly heatmap trace. |
| **Dash** 4.4 (MIT) | Flask app; the layout is a tree of components and callbacks connect inputs to outputs. | Full control over layout (HTML/CSS, Bootstrap components). `clickData` works on any Plotly chart, heatmaps included. Only the affected outputs recompute. Mature, widely used for analytics dashboards. | More code than Streamlit for the same screens: every interaction is an explicit callback, and the wiring gets verbose as the app grows. Browser-based tests need Selenium. |
| **Panel** (HoloViz) 1.10 (BSD) | Reactive parameters; runs as a server (`panel serve`) or inside Jupyter. | Works with almost any plotting library (Bokeh, Plotly, Altair, Matplotlib). Plotly click events are available (`click_data`). Same code runs in a notebook, handy for research. | Steeper learning curve, and the documentation is spread across the HoloViz projects. Smaller community than Streamlit or Dash. Needs Python 3.12+. |
| **Shiny for Python** 1.8 (MIT) | Reactive graph, as in R Shiny: only the outputs that depend on a changed input recompute. | Efficient, predictable updates without manual caching. Clean structure for a medium-sized app. Posit supports it. | Smaller Python ecosystem. Plotly charts and their clicks go through an extra package (`shinywidgets`, a bridge to Jupyter widgets). Fewer ready-made examples. |
| **NiceGUI** 3.18 (MIT) | Event-driven UI built on Vue/Quasar; you write handlers for clicks. | App-like interfaces with fine control. Plotly and ECharts charts report point clicks. | Not made for data apps: tables, caching and layout patterns are more manual. Smaller community for analytics use. |
| **Gradio** 6.31 (Apache-2.0) | Input → function → output demos. | Very quick for a single form. | Built for machine-learning demos. A multi-tab, calendar-driven dashboard fights its model. Not recommended. |
| **Static HTML report** (Plotly or Vega-Lite exported by a CLI) | A command writes an HTML file; no server. | Nothing to run but a browser. Easy to share as a file. | Every combination of timeframe, time of day and reference years must be computed in advance, or the user regenerates the file. The detail panel needs custom JavaScript. Fails the "change it and see" use. |

## Decision needed

Pick one in [#8](https://github.com/valentina98/weather-odds/issues/8): **Streamlit** (recommended), **Dash**, or another from the table. The choice does not affect the data or statistics design.
