# Development plan for v1 (proposal)

_Drafted 2026-10-29 for review. Development starts after the owner closes [#12](https://github.com/valentina98/weather-odds/issues/12). Each milestone becomes a GitHub issue and is built in small pull requests into `main`._

v1 is the local dashboard for Plovdiv described in the [requirements](spec/requirements.md). The research code already does most of the computing: the [prototypes](../research/prototype/README.md), `scale.py`, `daystats.py` and the loaders. v1 turns it into a tested package.

| # | Milestone | Contents | Done when |
|---|---|---|---|
| 1 | **Project skeleton** | `pyproject.toml` (uv), `src/weather_odds/` layout, `config.example.yaml` with a typed schema, lint and tests in GitHub Actions | `uv run pytest` passes in CI on an empty test suite |
| 2 | **Data adapters and cache** | Meteostat hourly (station temperature), ERA5 from the Open-Meteo AWS bucket (and the API with plain ERA5), airport reports, NOAA GSOD and NIMH (rain calibration). Parquet cache and a `prefetch` command | One command downloads Plovdiv in under 5 minutes; adapters are tested on small recorded files, without network |
| 3 | **Plovdiv hourly table** | Station temperature with ERA5 gap-filling corrected to the station, ERA5 rain and gusts with the calibrated thresholds, airport thunder, daylight hours ([methodology §1, §10](spec/methodology.md#1-data-for-plovdiv)) | The table's checks against the station match [all-sources.md](research/all-sources.md) |
| 4 | **Statistics engine** | Pooling, trend adjustment (fitted to the station), the outdoor-weather scale with configurable thresholds, calendar values (chance or average; absolute or relative), detail-panel numbers, intervals | Unit tests cover every function; numbers match the research scripts |
| 5 | **Validation command** | The cross-validation as a command (`weather-odds validate`), with a small fixture run in CI | It reproduces [validation.md](research/validation.md) |
| 6 | **Dashboard** | In Dash ([#8](https://github.com/valentina98/weather-odds/issues/8)), starting from the [Dash prototype](../research/prototype/README.md): inputs, calendar, detail panel, Patterns and Data tabs; dd.mm.yyyy dates; "not a forecast"; trend-adjustment label; colour-blind-safe palette | The acceptance list in [requirements §6](spec/requirements.md#6-acceptance-for-v1-plovdiv) passes |
| 7 | **Release** | README with two-command install, short user guide, data attribution, v1.0 tag | A fresh clone runs on Linux, macOS and Windows |

**Checks to schedule inside the milestones**
- **Open-Meteo API (milestone 2):** confirm that `models=era5` returns plain ERA5 and not ERA5-Land.
- **Thunder (milestone 3):** test a model stand-in for the years before 2012 (ERA5 convective rain or CAPE, IFS lightning).
- **Rain calibration (milestone 3):** re-check the wet-day thresholds as NIMH years accumulate (2022–2025 suggests lower thresholds than 1973–1999).
- **Scale (milestone 5):** re-run the scale validation with station temperatures and thunder included.
