# Dashboard prototypes (throwaway)

Two quick prototypes of the same screens for issue [#8](https://github.com/valentina98/weather-odds/issues/8): `app.py` in Streamlit and `dash_app.py` in Dash. Both use `model.py` for the data and statistics, so only the screens differ. They show real screens so the framework can be judged; they are **not the application**, and none of it is meant to be kept as is.

What it shows, for Plovdiv, from ERA5 only:
- the calendar at day, week or month granularity, coloured by the outdoor-weather scale ([methodology §4](../../docs/spec/methodology.md#4-outdoor-weather-scale));
- inputs:
  - timeframe and optional time of day (default: daylight);
  - colour measure (chance of good weather or average score), absolute or relative colours;
  - reference years and the trend-adjustment switch;
  - pooling and the main scale thresholds;
- a detail panel when a cell is clicked.

Not included: station calibration, thunder, a real config file, tests.

## Run

Fill the cache once (about 25 minutes), install Streamlit and Dash, then start one of the apps:

```bash
.venv/bin/python research/fetch_sources.py --sources aws
```

```bash
.venv/bin/pip install -r research/prototype/requirements.txt
```

```bash
.venv/bin/streamlit run research/prototype/app.py
```

The Dash version (open http://localhost:8050 after starting it):

```bash
cd research/prototype && ../../.venv/bin/python dash_app.py
```

The first start takes about 20 seconds, because it reads the gzipped CSV cache. After that, a change of an input takes 0.1–0.3 seconds in Streamlit and 0.04–0.2 seconds in Dash (measured without the browser).

Results and the evaluation are in [docs/research/dashboard-frameworks.md](../../docs/research/dashboard-frameworks.md#first-results-streamlit-prototype).
