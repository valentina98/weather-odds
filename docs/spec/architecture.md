# Architecture (proposal)

Status: **proposal, not decided.** Nothing here is implemented. Updated 2026-10-29: local only, Plovdiv only, one outdoor-weather scale instead of activity profiles. Choices that need the owner's input are linked to issues.

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
           │              │  weather-scale scores and odds,
           └──────┬───────┘  intervals, patterns, cross-validation
                  ▼
           ┌──────────────┐
           │  dashboard   │  calendar (month / week / day) coloured
           └──────────────┘  by the scale, detail panel, patterns, data
```

## Components

| Component | Responsibility | Notes |
|---|---|---|
| **Config** | Load and validate `config.yaml` (location, scale thresholds, reference period, default time of day, pooling, source priority). | YAML + a typed schema (e.g. pydantic). Secrets only from environment variables. |
| **Data adapters** | One adapter per source, all returning the same tidy schema (hourly and daily, local time, units fixed). | Open-Meteo API, Open-Meteo AWS (ERA5, ERA5-Land, ECMWF IFS), NIMH open data, NOAA GSOD, airport reports (IEM), Copernicus CDS (optional). The research loaders in `research/load_sources.py` are the prototype. |
| **Cache** | Store downloads per location and source; refresh on request. | Parquet files under a cache folder; git-ignored. |
| **Blending** | Combine sources for a location: gridded backbone, station data for checking and correcting where available. | v1 can start with gridded data plus station-based checks; correction methods come later. |
| **Stats engine** | Day-of-year statistics, pooling, trend adjustment, the outdoor-weather scale, percentiles, bootstrap intervals, pattern detection. | No I/O, fully unit-tested. |
| **Validation** | Cross-validation of the odds (predict each year from other years). | Prototype: `research/validate_odds.py`. Run in CI on a small fixture; full run on demand. |
| **Dashboard** | Calendar, detail panel, Patterns and Data tabs; runs locally only. | See the tool choice below. |
| **CLI** | `prefetch` data for the configured location; export tables as CSV; run the validation. | Lets people pre-download before using the dashboard. |

## Technology (proposed)

| Area | Proposal | Alternatives |
|---|---|---|
| Language | Python 3.12+ | – |
| Data | pandas (or polars), NumPy | xarray only if gridded maps are added |
| Open-Meteo `.om` files | `omfiles` + `s3fs` | – |
| Dashboard | **Streamlit**: one command to start, easy for other developers; reports clicks on chart marks for the calendar ([comparison](../research/dashboard-frameworks.md), open: [#8](https://github.com/valentina98/weather-odds/issues/8)) | Dash (more layout control), Panel, Shiny for Python |
| Charts | Altair or Plotly; the calendar is drawn as clickable marks (Altair `rect` or Plotly square markers) | – |
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
| Open-Meteo free API daily limit (especially from shared networks) | Cache aggressively; AWS open-data fallback; document the limit. |
| `.om` file layout on AWS changes | Pin `omfiles`; keep the API adapter as the primary path. |
| NIMH open data is experimental | Treat it as optional; validate before use. |
| Users read odds as forecasts | Wording, intervals and an explicit "this is not a forecast" note in every view. |
| Red–green colours are hard to tell apart for colour-blind users | Palette that also changes in lightness; values on hover; optional colour-blind palette. |
