# Architecture (proposal)

Status: **proposal, not decided.** Nothing here is implemented. Choices that need the owner's input are linked to issues.

## Overview

```
config.yaml ──► CLI / dashboard
                  │
                  ▼
           ┌──────────────┐     ┌──────────────────────────────┐
           │  data layer  │────►│ local cache (.cache/, Parquet)│
           │  (adapters)  │     └──────────────────────────────┘
           └──────┬───────┘
                  │ tidy hourly + daily tables per location
                  ▼
           ┌──────────────┐
           │ stats engine │  pure functions: pooling, percentiles,
           │              │  joint "good day" odds, intervals,
           └──────┬───────┘  pattern detection
                  ▼
           ┌──────────────┐
           │  dashboard   │  views: month / week / day / hour,
           └──────────────┘  best-date ranking, patterns, sources
```

## Components

| Component | Responsibility | Notes |
|---|---|---|
| **Config** | Load and validate `config.yaml` (places, profiles, reference period, source priority). | YAML + a typed schema (e.g. pydantic). Secrets only from environment variables. |
| **Data adapters** | One adapter per source, all returning the same tidy schema (hourly and daily, local time, units fixed). | Open-Meteo API, Open-Meteo AWS (ERA5/ERA5-Land), NIMH open data, NOAA GSOD, airport reports (IEM), Copernicus CDS (optional). The research loaders in `research/load_sources.py` are the prototype. |
| **Cache** | Store downloads per location and source; refresh on request. | Parquet files under a cache folder; git-ignored. |
| **Blending** | Combine sources for a location: gridded backbone, station data for checking and correcting where available. | v1 can start with gridded data plus station-based checks; correction methods come later. |
| **Stats engine** | Day-of-year statistics, pooling, percentiles, joint conditions, bootstrap intervals, pattern detection. | No I/O, fully unit-tested. |
| **Dashboard** | Interactive views. | See the tool choice below. |
| **CLI** | `prefetch` data for configured places; export tables as CSV. | Lets people pre-download before using the dashboard. |

## Technology (proposed)

| Area | Proposal | Alternatives |
|---|---|---|
| Language | Python 3.12+ | – |
| Data | pandas (or polars), NumPy | xarray only if gridded maps are added |
| Open-Meteo `.om` files | `omfiles` + `s3fs` | – |
| Dashboard | **Streamlit**: one command to start, easy for other developers | Dash or Panel (more layout control), Shiny for Python |
| Charts | Plotly (interactive, works in Streamlit) | Altair |
| Packaging | `uv` / `pyproject.toml`; optional Docker image | pip + venv |
| Tests | pytest with small recorded fixtures | – |
| CI | GitHub Actions: lint + tests | – |

## Repository layout (proposed)

```
weather-odds/
├── docs/                 research, spec, decisions
├── research/             phase-0 scripts (kept for reproducibility)
├── src/weather_odds/     application package (not created yet)
│   ├── config.py
│   ├── sources/          one module per adapter
│   ├── cache.py
│   ├── stats/            pooling, odds, intervals, patterns
│   ├── cli.py
│   └── dashboard/
├── tests/
├── config.example.yaml
└── pyproject.toml
```

## Risks

| Risk | Mitigation |
|---|---|
| Open-Meteo free API daily limit (especially from shared networks or a hosted instance) | Cache aggressively; AWS open-data fallback; document the limit. |
| `.om` file layout on AWS changes | Pin `omfiles`; keep the API adapter as the primary path. |
| NIMH open data is experimental | Treat it as optional; validate before use. |
| Users read odds as forecasts | Wording, intervals and an explicit "this is not a forecast" note in every view. |
