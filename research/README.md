# Research scripts (phase 0)

Throwaway-quality scripts that produced the evidence in [`docs/research/`](../docs/research/). They are **not** the application; they are kept so every number and chart can be reproduced.

| Script | What it does |
|---|---|
| `fetch_sources.py` | Downloads raw data for Plovdiv from every no-key source into `.cache/plovdiv/` (git-ignored). Re-runs only fetch what is missing. `--sources aws` fetches only ERA5, ERA5-Land and ECMWF IFS from the AWS bucket. |
| `load_sources.py` | Turns the raw files into tidy daily/hourly pandas tables. |
| `daystats.py` | Shared day-of-year helpers (365-day calendar, pooling, smooth seasonal curve). |
| `scale.py` | The outdoor-weather scale (methodology §4), shared by `preview_scale.py` and the prototype. |
| `analyze_plovdiv.py` | Runs the phase-0 data check → [plovdiv-data-check.md](../docs/research/plovdiv-data-check.md). Needs all sources. |
| `analyze_ranges.py` | Early October by source and range of years → [early-october.md](../docs/research/early-october.md). Needs `aws`; adds station data when cached. |
| `analyze_warm_spells.py` | Warm spells and warm-ups counted per year and 10-day window → [early-october.md](../docs/research/early-october.md#does-the-timing-vary-from-year-to-year). Needs `aws`. |
| `validate_odds.py` | Cross-validation of the odds → [validation.md](../docs/research/validation.md). Needs `aws`. |
| `preview_scale.py` | Preview of the outdoor-weather scale → [weather-scale.md](../docs/research/weather-scale.md). Needs `aws`. |
| `prototype/` | Throwaway Streamlit prototype of the dashboard for #8 → [prototype/README.md](prototype/README.md). Not the application. |

## Run

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r research/requirements.txt
```

```bash
.venv/bin/python research/fetch_sources.py
```

```bash
.venv/bin/python research/analyze_plovdiv.py
```

The later checks need only the AWS data (`--sources aws`, about 25 minutes):

```bash
.venv/bin/python research/analyze_ranges.py
```

```bash
.venv/bin/python research/analyze_warm_spells.py
```

```bash
.venv/bin/python research/validate_odds.py
```

```bash
.venv/bin/python research/preview_scale.py
```

Fetching takes about 15 minutes (most of it is reading 66 years of hourly ERA5 from AWS). The Open-Meteo API step is optional and is skipped when the free daily limit is exceeded; the analysis does not depend on it.

Behind a TLS-intercepting proxy (as in Claude Code cloud sessions), point Python at the proxy's CA bundle, for example `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE` and `AWS_CA_BUNDLE`.
