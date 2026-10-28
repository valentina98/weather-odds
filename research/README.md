# Research scripts (phase 0)

Throwaway-quality scripts that produced the evidence in [`docs/research/`](../docs/research/). They are **not** the application; they are kept so every number and chart can be reproduced.

| Script | What it does |
|---|---|
| `fetch_sources.py` | Downloads raw data for Plovdiv from every no-key source into `.cache/plovdiv/` (git-ignored). Re-runs only fetch what is missing. |
| `load_sources.py` | Turns the raw files into tidy daily/hourly pandas tables. |
| `analyze_plovdiv.py` | Runs the data check; writes charts to `docs/research/img/` and numbers to `docs/research/plovdiv-data-check.json`. |

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

Fetching takes about 15 minutes (most of it is reading 66 years of hourly ERA5 from AWS). The Open-Meteo API step is optional and is skipped when the free daily limit is exceeded; the analysis does not depend on it.

Behind a TLS-intercepting proxy (as in Claude Code cloud sessions), point Python at the proxy's CA bundle, for example `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE` and `AWS_CA_BUNDLE`.
