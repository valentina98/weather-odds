# Requirements (draft)

Status: **draft for review, updated 2026-10-29 with the owner's answers in issues #2–#11.** Items marked *(open: #N)* still wait for an answer; all are collected in [#12](https://github.com/valentina98/weather-odds/issues/12).
Requirement IDs are stable so issues and PRs can refer to them. Removed requirements keep their number and say why.

## 1. Scope

weather-odds shows how good the weather has usually been for being outdoors, to help plan 1–3 months ahead. It rates past weather on **one outdoor-weather scale, shown as colours from green (good) to red (bad)**. It does not match weather to particular activities. It is a local tool with a dashboard, configured by a file, runnable by any developer from the public repo.

v1 covers **Plovdiv, Bulgaria only**, and precision for Plovdiv comes before support for other places. Sofia and Varna may follow later ([#4](https://github.com/valentina98/weather-odds/issues/4)).

## 2. Users and use cases

| ID | Use case |
|---|---|
| U1 | "I want to organise a gathering sometime in the next 6 weeks. Which weeks usually have good weather?" |
| U2 | "We want to be outside on a Saturday afternoon in mid-October. How often was that afternoon good, and when it wasn't, what spoiled it: rain, cold or wind?" |
| U3 | "Is the early-October warm spell real? How often does it happen?" |
| U4 | "Show me November by week: how good the weather usually is, the temperature range, the chance of rain, the first frost." |

## 3. Functional requirements

### Location

| ID | Requirement |
|---|---|
| F1 | v1 has one location: Plovdiv (station WMO 15625 and the matching grid cells). It is set in the config; the dashboard has no place picker. |
| F2 | Gridded temperatures are corrected to the location's elevation. *(Removed for v1: hiking spots with their own elevation, [#4](https://github.com/valentina98/weather-odds/issues/4).)* |
| F3 | Plovdiv uses its station's measurements wherever they improve precision: hourly temperatures from 1997, airport reports for thunder, station rain to calibrate ERA5 ([methodology §1, §10](methodology.md#1-data-for-plovdiv)). |
| F4 | *Removed ([#4](https://github.com/valentina98/weather-odds/issues/4)): saved places with activity profiles.* The code keeps the location in the config so other cities can be added later, but v1 does not need to work for them. |

### Time selection

| ID | Requirement |
|---|---|
| F5 | The user picks a timeframe. Default: today to today + 3 months. |
| F6 | The user picks the granularity: **month, week or day**. Default: **week**. |
| F7 | The user can optionally pick a time of day (e.g. 17:00–22:00). If none is picked, the default is **one daylight window for the whole timeframe**: from the latest sunrise to the earliest sunset among its dates, rounded inward to whole hours, so every date is judged on the same hours and every hour is in daylight. The window is shown and can be changed. All statistics for a period use only these hours. |
| F8 | The user can choose how many neighbouring days are pooled for daily statistics (e.g. ±0, ±3, ±7) and sees the effect on uncertainty. The default comes from the [cross-validation](../research/validation.md). |

### Main view: calendar

| ID | Requirement |
|---|---|
| F10 | The main view is a calendar of the timeframe at the selected granularity. Each cell (day, week or month) is coloured on the outdoor-weather scale for the selected time of day, from green (good) to red (bad). The user picks the measure: the **chance of good weather** (default: share of past days rated Good or Great) or the **average score** ([methodology §4](methodology.md#4-outdoor-weather-scale)). |
| F28 | Colours are **absolute** by default (fixed 0–100 range). The user can switch to **relative** colours, stretched over the cells of the selected timeframe; the view is then labelled "relative" ([#5](https://github.com/valentina98/weather-odds/issues/5)). |
| F11 | There is no separate list of best days or weeks; the colours show them at the selected granularity ([#10](https://github.com/valentina98/weather-odds/issues/10)). |
| F25 | Selecting a day, week or month in the calendar opens the detail panel for that period and time of day. |
| F26 | The colours stay readable for colour-blind users: the palette also changes in lightness, and every cell shows its value on hover. |

### Detail panel

| ID | Requirement |
|---|---|
| F9 | For the selected period and time of day, show: the share of past days in each class of the scale; the typical temperature range (10th–90th percentile and median); the chance of rain during those hours and of a wet day; the chance of thunder, strong wind, heat and frost; snow where relevant; and which factor most often lowered the rating. |
| F13 | Every number shows its basis: data source, years used, and an uncertainty band or interval. |
| F14 | Show sunrise, sunset and daylight for the selected dates. |

### Outdoor-weather scale

| ID | Requirement |
|---|---|
| F16 | One outdoor-weather scale rates every past hour from 0 (bad) to 100 (great), from temperature, rain, wind gusts and, where data allows, thunder. Both cold and heat lower the rating; extreme heat counts as bad weather. A day's rating is the mean over the selected hours. Five classes: **Great, Good, Fair, Poor, Bad**, coloured dark green to red. Definition: [methodology §4](methodology.md#4-outdoor-weather-scale). |
| F17 | All thresholds of the scale are defaults in the config, and the user can change them in the dashboard for the session ([#5](https://github.com/valentina98/weather-odds/issues/5)). **Thresholds can differ by time of day** (night, morning, afternoon, evening; e.g. a lower comfortable temperature for evenings); by default all bands use the same values. *(Removed: the activity profiles gathering, walk and hike.)* |

### Other tabs

| ID | Requirement |
|---|---|
| F12 | **Patterns and trends** tab: recurring patterns that pass the statistical checks in the methodology, as frequencies ("a warm spell in this fortnight in 6 of 10 years"), plus the trend tools in F29–F31. |
| F29 | **Investigate a window**: the user picks a date window (e.g. 1–10 Oct), optionally a window to compare with (e.g. 21–30 Sep), and a range of years. The tool shows each year's value (mean daily maximum, rain days, score) with the long-term trend, the per-year difference between the windows ("warmer than late September in 9 of 10 years") and the averages with 95% intervals. |
| F30 | **Events**: warm-ups ("warmer, then colder again"), warm spells, cold snaps, rainy spells and heat waves are found in each year first, then counted per 10-day window and range of years, so events at varying dates are not averaged away. The event definitions are editable. |
| F31 | **Year by day**: a year × day chart of how far each day was above or below normal, for any window and range of years. Every trend view warns that searching many windows finds some patterns by chance. |
| F23 | **Data** tab: sources, years used, station-vs-grid checks and attribution for every source used. |
| F15 | *Removed ([#7](https://github.com/valentina98/weather-odds/issues/7)): no seasonal outlook.* The odds come only from historical statistics for the month, week, day and time of day, never from current weather or forecasts. |

### Configuration

| ID | Requirement |
|---|---|
| F18 | One YAML config file holds: the location, the reference period (default: **the last 30 complete years**), trend adjustment on/off, the scale thresholds, the colour measure and absolute/relative default, the default time of day, the pooling default, data-source priority, and the cache location. Optional API keys come from environment variables and are never stored in the file. |
| F19 | The dashboard can override config values for the session without editing the file. In particular, the user can **narrow the reference years** to a shorter range within the configured period ([#6](https://github.com/valentina98/weather-odds/issues/6)). |
| F27 | **Trend adjustment** of temperatures can be switched on and off in the dashboard; the config sets the default (shipped: on). When it is on, the calendar says so, and the detail panel shows the fitted trend and the shift applied ([#6](https://github.com/valentina98/weather-odds/issues/6), [methodology §2](methodology.md#2-reference-period)). |

### Data

| ID | Requirement |
|---|---|
| F20 | Data is downloaded on demand and cached locally; the cache can be refreshed. |
| F21 | Works with **no API key** by default (Open-Meteo API, with the Open-Meteo AWS open data as a fallback when the API limit is hit). |
| F22 | *Removed: optional Copernicus CDS sources. CERRA was tested and is not more precise at Plovdiv ([all sources](../research/all-sources.md)); no key is needed.* |

### Validation

| ID | Requirement |
|---|---|
| F24 | The repo contains a cross-validation that predicts each past year from the other years only and reports the error of the odds ([#7](https://github.com/valentina98/weather-odds/issues/7)). Defaults that affect the odds (reference years, pooling, trend adjustment) are chosen from its results. |

## 4. Non-functional requirements

| ID | Requirement |
|---|---|
| N1 | Another developer can install and start the dashboard with documented commands (target: two commands) on Linux, macOS and Windows. |
| N2 | The first download for Plovdiv completes in under 5 minutes; cached views render in under 2 seconds. |
| N3 | The statistics code is separate from the dashboard and covered by automated tests with small recorded data fixtures (no network in tests). |
| N4 | No downloaded weather data is committed to the repo. |
| N5 | Non-commercial data terms are documented; commercial users are pointed to paid keys. |
| N6 | The interface is in **English only**. Dates are shown as **dd.mm.yyyy** (e.g. 28.10.2026). Units: °C, km/h, mm ([#9](https://github.com/valentina98/weather-odds/issues/9)). |
| N7 | **Local only**: each person runs the dashboard on their own computer; there is no hosted instance ([#8](https://github.com/valentina98/weather-odds/issues/8)). |
| N8 | Dashboard framework: **Dash** ([#8](https://github.com/valentina98/weather-odds/issues/8), D29); see the [comparison](../research/dashboard-frameworks.md). |

## 5. Out of scope for v1

- Forecasts of any kind: seasonal outlooks, short-range forecasts and current weather ([#7](https://github.com/valentina98/weather-odds/issues/7)).
- Places other than Plovdiv, including hiking spots ([#4](https://github.com/valentina98/weather-odds/issues/4)).
- Ratings per activity ([#5](https://github.com/valentina98/weather-odds/issues/5)).
- A hosted instance, accounts, sharing, notifications ([#8](https://github.com/valentina98/weather-odds/issues/8)).
- Other interface languages ([#9](https://github.com/valentina98/weather-odds/issues/9)).

## 6. Acceptance for v1 (Plovdiv)

1. For any timeframe, the dashboard shows the calendar at month, week and day granularity, coloured by the outdoor-weather scale, and selecting a cell opens the detail panel (F9, F13, F14).
2. Changing the time of day or narrowing the reference years updates the calendar and the detail panel.
3. The statements in [the Plovdiv data check](../research/plovdiv-data-check.md) and [the early-October check](../research/early-october.md) can be reproduced from the dashboard.
4. The cross-validation (F24) runs from the repo and reproduces the numbers in [validation.md](../research/validation.md).
5. A fresh clone runs with no API key.
