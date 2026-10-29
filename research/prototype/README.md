# Dashboard prototype (throwaway)

A quick Streamlit prototype for issue [#8](https://github.com/valentina98/weather-odds/issues/8): "pick one, show first results, then we re-evaluate". It shows real screens so the framework can be judged; it is **not the application**, and none of it is meant to be kept as is.

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

Fill the cache once (about 25 minutes), install Streamlit, then start the app:

```bash
.venv/bin/python research/fetch_sources.py --sources aws
```

```bash
.venv/bin/pip install -r research/prototype/requirements.txt
```

```bash
.venv/bin/streamlit run research/prototype/app.py
```

The first start takes about 18 seconds, because it reads the gzipped CSV cache. After that, each change of an input re-runs the script in 0.1–0.3 seconds (measured with Streamlit's test runner, `AppTest`).

Results and the evaluation are in [docs/research/dashboard-frameworks.md](../../docs/research/dashboard-frameworks.md#first-results-streamlit-prototype).
