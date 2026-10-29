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
| 7 | **Trend tools** | The Patterns and trends tab: investigate a window against another and across ranges of years, event counts per 10-day window, year-by-day anomalies (requirements F29–F31). Ports `analyze_ranges.py` and `analyze_warm_spells.py` | The [early-October results](research/early-october.md) can be reproduced in the dashboard |
| 8 | **Release** | README with two-command install, short user guide, data attribution, v1.0 tag | A fresh clone runs on Linux, macOS and Windows |

## Filling the data gaps

Checked on 2026-10-29 which sources could fill each gap. Every fill is tested by hiding data the tool has and filling it the same way; a fill is used only if that test passes.

| Gap | What exists | Plan | Test | Milestone |
|---|---|---|---|---|
| **1996: no station temperatures** | Nothing for 1996 at NOAA (hourly or daily), Meteostat or the airport archive | Default: leave 1996 out, so the 30-year period has 29 station years, labelled as such. Option in the config: fill 1996 from ERA5 corrected to the station, using 1993–1999 for the correction | Hide 1997, fill it the same way, compare with the measurements | 3 |
| **Before 1997 the station has only 3-hourly temperatures** | 8 readings a day from 1980 (NOAA ISD) | Only matters if the user picks years before 1997. Fill the hours in between with ERA5's daily shape, fitted to the 3-hourly readings | Thin 1997–2025 to 3-hourly, rebuild the hours, compare daily maxima and the scale | 3 |
| **Thunder** | Hourly airport reports 2012–2014 and 2019–2025. NOAA's daily thunder flag 1990–2014 matches the airport where both exist (2012–2014: 30/24/43 vs 29/29/47 days). Both are empty in 2015–2018. NOAA's flag undercounts from 2022 | Thunder days: the NOAA flag 1997–2011 plus the airport reports, so 25 of the 29 years. For the hourly scale, place a flagged day's thunder in its hours with convective signs: ERA5 CAPE and convective rain from Copernicus (a small area around Plovdiv; your key and licence work), else its rainy afternoon hours. 2015–2018: the same model signs, or leave those years out of the thunder numbers | Fit on 2012–2014 and 2019–2021, check on 2022–2025 against the airport's thunder hours | 3 |
| **Station rain amounts 2000–2021** | None at NOAA after 1999, nothing in the hourly NOAA files after 2000, NIMH only from 2022. ECA&D has no Plovdiv, but has Chirpan (50 km east, same plain) and Ivailo (35 km west) | Rain amounts come from ERA5 anyway; station rain only calibrates ERA5. Check the years ECA&D holds for Chirpan and Ivailo, and whether its licence (non-commercial research and education) fits. Only if that fails: ask NIMH for Plovdiv 2000–2021 (may cost; usable for calibration, not publishable) | Calibrate on one station, check on the other | 3 |
| **Wet-day threshold disagrees** (1973–1999: about 1.7 mm; 2022–2025: about 1.1 mm) | GSOD, NIMH, and airport rain reports 2012–2025 (rain seen, no amounts) | Use the airport's rain days as a third, independent check for 2012–2025. If ERA5 really changed, use a threshold per period | Pick the threshold on some years, check its wet-day frequency on the others | 3 |
| **Open-Meteo API: plain ERA5** | The free daily limit was used up on 2026-10-29 | Request `models=era5` for one month and compare with the AWS ERA5. If it differs, the tool reads only the AWS bucket | Same days, same point: must match the AWS ERA5 | 2 |
| **Wind gusts not measured** | The station's hourly mean wind is measured (NOAA ISD); gusts are model fill-ins | Keep ERA5 gusts (they rarely lower the score: under 2% on average). Check ERA5 wind against the station's mean wind for a bias | ERA5 10 m wind vs station wind, by month | 3 |

**Other checks inside the milestones**
- **Scale (milestone 5):** re-run the scale validation with station temperatures, thunder and time-of-day thresholds included.
