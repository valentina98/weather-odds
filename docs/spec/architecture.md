# Architecture

Status: **signed off on 2026-10-29** (D44): local only, Plovdiv only, one outdoor-weather scale instead of activity profiles. Implementation follows the [development plan](../development-plan.md); details may change in pull requests and are then recorded in the [decision log](../decisions.md).

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
| **Data adapters** | One adapter per source, all returning the same tidy schema (hourly and daily, local time, units fixed). | Meteostat hourly (station temperature), ERA5 from the Open-Meteo AWS bucket (plain ERA5; never "ERA5 seamless"; D45), airport reports (IEM, thunder), NOAA GSOD and NIMH (rain calibration). The research loaders in `research/load_sources.py` are the prototype ([all sources](../research/all-sources.md)). |
| **Cache** | Store downloads per location and source; refresh on request. | Parquet files under a cache folder; git-ignored. |
| **Blending** | Build the Plovdiv hourly table: station temperature (ERA5 corrected to the station fills gaps), ERA5 rain and gusts with the calibrated thresholds, airport thunder. | Methodology §1 and §10. |
| **Stats engine** | Day-of-year statistics, pooling, trend adjustment, the outdoor-weather scale, percentiles, bootstrap intervals, pattern detection. | No I/O, fully unit-tested. |
| **Validation** | Cross-validation of the odds (predict each year from other years). | Prototype: `research/validate_odds.py`. Run in CI on a small fixture; full run on demand. |
| **Dashboard** | Calendar, detail panel, Patterns and Data tabs; runs locally only. | See the tool choice below. |
| **CLI** | `prefetch` data for the configured location; export tables as CSV; run the validation. | Lets people pre-download before using the dashboard. |

## Technology

| Area | Choice | Alternatives |
|---|---|---|
| Language | Python 3.12+ | – |
| Data | pandas (or polars), NumPy | xarray only if gridded maps are added |
| Open-Meteo `.om` files | `omfiles` + `s3fs` | – |
| Dashboard | **Dash** (decided in [#8](https://github.com/valentina98/weather-odds/issues/8), D29): callbacks update only what changed; full layout control | – |
| Charts | Plotly. The calendar is a heatmap; a click is mapped to its period by the cell's position (heatmap clicks carry no custom data) | – |
| Packaging | `uv` / `pyproject.toml`; optional Docker image | pip + venv |
| Tests | pytest with small recorded fixtures | – |
| CI | GitHub Actions: lint + tests | – |

## Repository layout

```
weather-odds/
├── docs/                 research, spec, decisions
├── research/             phase-0 scripts (kept for reproducibility)
├── src/weather_odds/     application package (from milestone 1)
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
| `.om` file layout on AWS changes | Pin `omfiles`; the Open-Meteo API with `models=era5` is the fallback to add if the bucket changes (D45). |
| NIMH open data is experimental | Treat it as optional; validate before use. |
| Users read odds as forecasts | Wording, intervals and an explicit "this is not a forecast" note in every view. |
| Red–green colours are hard to tell apart for colour-blind users | Palette that also changes in lightness; values on hover; optional colour-blind palette. |
