# Requirements (draft)

Status: **draft for review.** Items marked *(open: #N)* depend on a question in GitHub issue #N (all collected in [#12](https://github.com/valentina98/weather-odds/issues/12)).
Requirement IDs are stable so issues and PRs can refer to them.

## 1. Scope

weather-odds shows historical weather odds for planning outdoor activities 1–3 months ahead. It is a local tool with a dashboard, configured by a file, runnable by any developer from the public repo. The first and reference location is **Plovdiv, Bulgaria**.

## 2. Users and use cases

| ID | Use case |
|---|---|
| U1 | "I want to organise a gathering in the park sometime in the next 6 weeks, in the evening. Which weeks have the best odds of a dry, mild evening?" |
| U2 | "We plan a hike in the Rhodopes on a Saturday in mid-October. What temperatures should we expect up there, and how often does it rain on that kind of day?" |
| U3 | "Is the early-October warm spell real? How often does it happen, and when does it usually start?" |
| U4 | "Show me the whole of November by week: temperature range, rain chance, first frost." |

## 3. Functional requirements

### Location

| ID | Requirement |
|---|---|
| F1 | The user selects a location by place name (search), by coordinates, or from saved places in the config. |
| F2 | A location has an elevation. For hiking spots the elevation can be set by the user (e.g. a hut or peak), and temperatures are adjusted for it. |
| F3 | Bulgarian locations use Bulgarian station data where it improves precision (see methodology). Other locations work with gridded data only. |
| F4 | Saved places can be given a name and a default activity profile. *(open: #4)* |

### Time selection

| ID | Requirement |
|---|---|
| F5 | The user picks a start date and a horizon of up to 3 months (default: today + 3 months). *(open: #10)* |
| F6 | The user picks the granularity: **month, week, day or hour**. |
| F7 | The user picks an **event time window** (e.g. 17:00–22:00). Rain, wind and temperature statistics for "the event" use only those hours. Default: whole day. |
| F8 | The user can choose how many neighbouring days are pooled for daily statistics (e.g. ±0, ±3, ±7) and sees the effect on uncertainty. |

### Outputs

| ID | Requirement |
|---|---|
| F9 | For each period (month / week / day / hour) show: typical temperature range during the event window (10th–90th percentile and median), chance of rain during the event window, chance of a wet day, chance of thunder, chance of strong wind, chance of heat and of frost, snow on the ground or snowfall where relevant. |
| F10 | Show a **"good day" chance** per day, computed from historical days that met *all* the activity profile's conditions at once (joint frequency, not a product of separate chances). |
| F11 | Rank the best days and weeks in the selected horizon by the good-day chance. |
| F12 | Show **recurring patterns** (e.g. "warm spell 1–14 Oct in 6 of 10 years") only when they pass the statistical checks in the methodology. |
| F13 | Every number shows its basis: data source, years used, and an uncertainty band or interval. |
| F14 | Show sunrise, sunset and daylight for the selected dates (useful for evening events and hikes). |
| F15 | *(open: #7)* Optionally show the current seasonal outlook (tercile probabilities) for the selected months, clearly separated from the historical odds. |

### Activity profiles

| ID | Requirement |
|---|---|
| F16 | Activity profiles define what a "good day" means: maximum rain in the event window, comfortable temperature range, maximum wind gust, no thunder, etc. |
| F17 | Default profiles: **gathering**, **walk**, **hike**. All thresholds are editable in the config. *(open: #5)* |

### Configuration

| ID | Requirement |
|---|---|
| F18 | One YAML config file holds: places, activity profiles, reference period, pooling default, data-source priority, cache location, optional API keys (read from environment variables, never stored in the file). |
| F19 | The dashboard can override config values for the session without editing the file. |

### Data

| ID | Requirement |
|---|---|
| F20 | Data is downloaded on demand for the selected locations only and cached locally; the cache can be refreshed. |
| F21 | Works with **no API key** by default (Open-Meteo API, with the Open-Meteo AWS open data as a fallback when the API limit is hit). |
| F22 | Optional sources with keys (Copernicus CDS for CERRA and seasonal forecasts) are enabled by setting an environment variable. |
| F23 | Shows attribution for every data source used in a view. |

## 4. Non-functional requirements

| ID | Requirement |
|---|---|
| N1 | Another developer can install and start the dashboard with documented commands (target: two commands) on Linux, macOS and Windows. |
| N2 | First load of a new location completes in under 5 minutes; cached views render in under 2 seconds. |
| N3 | The statistics code is separate from the dashboard and covered by automated tests with small recorded data fixtures (no network in tests). |
| N4 | No downloaded weather data is committed to the repo. |
| N5 | Non-commercial data terms are documented; commercial users are pointed to paid keys. |
| N6 | *(open: #9)* Interface language(s). |
| N7 | *(open: #8)* Local-only or also a hosted instance. |

## 5. Out of scope for v1

- Day-specific forecasts beyond ~2 weeks; our own forecast model.
- Live weather and short-range forecasts (link out to existing services instead).
- Accounts, sharing, notifications.

## 6. Acceptance for v1 (Plovdiv)

1. For Plovdiv and a 3-month horizon, the dashboard shows month, week, day and hour views with the outputs in F9–F14.
2. The early-October and late-September statements in [the Plovdiv data check](../research/plovdiv-data-check.md) can be reproduced from the dashboard.
3. A second Bulgarian location (a hiking spot chosen by the owner) works with elevation-adjusted temperatures.
4. A fresh clone runs with no API key.
