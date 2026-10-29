# Dashboard prototype (throwaway)

A quick Dash prototype of the dashboard for issue [#8](https://github.com/valentina98/weather-odds/issues/8). The same screens were also built in Streamlit to compare the two; the owner chose Dash (D29). The Streamlit code is kept in the closed pull request [#13](https://github.com/valentina98/weather-odds/pull/13). This prototype shows real screens and is the starting point for milestone 6 of the [development plan](../../docs/development-plan.md). It is **not the application**, and none of it is meant to be kept as is.

What it shows, for Plovdiv, from ERA5 only:
- the calendar at day, week or month granularity, coloured by the outdoor-weather scale ([methodology §4](../../docs/spec/methodology.md#4-outdoor-weather-scale));
- inputs:
  - timeframe and optional time of day (default: daylight);
  - colour measure (chance of good weather or average score), absolute or relative colours;
  - reference years and the trend-adjustment switch;
  - pooling and the main scale thresholds;
- a detail panel when a cell is clicked.

Not included: station temperatures, thunder, a real config file, tests.

| File | What it holds |
|---|---|
| `dash_app.py` | The screens and callbacks |
| `model.py` | The data and statistics behind them |

## Run

Fill the cache once (about 25 minutes), install Dash, then start the app and open http://localhost:8050:

```bash
.venv/bin/python research/fetch_sources.py --sources aws
```

```bash
.venv/bin/pip install -r research/prototype/requirements.txt
```

```bash
cd research/prototype && ../../.venv/bin/python dash_app.py
```

The first start takes about 20 seconds, because it reads the gzipped CSV cache. After that, a change of an input takes 0.04–0.2 seconds (measured without the browser).

The evaluation is in [docs/research/dashboard-frameworks.md](../../docs/research/dashboard-frameworks.md#streamlit-and-dash-side-by-side).
