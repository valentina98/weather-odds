# Open questions

Questions for the owner are GitHub issues assigned to them, collected in the tracking issue **[#12 Specification phase: questions and sign-off](https://github.com/valentina98/weather-odds/issues/12)**. Answers are copied into [decisions.md](decisions.md) and the spec.

## Still open (as of 2026-10-29)

| Issue | Question | Proposed answer |
|---|---|---|
| [#5](https://github.com/valentina98/weather-odds/issues/5) | Confirm the outdoor-weather scale: comfort range 18–26 °C; heat bad from 38 °C; rain rule (1 mm caps a day at Fair); calendar colour = chance of a Good or Great day; absolute rather than season-relative. | As in [methodology §4](spec/methodology.md#4-outdoor-weather-scale); preview in [weather-scale.md](research/weather-scale.md). |
| [#6](https://github.com/valentina98/weather-odds/issues/6) | Turn on trend adjustment for temperature by default? | Yes: without it, 30-year odds were about 1 °C too cold in the [cross-validation](research/validation.md). |
| [#8](https://github.com/valentina98/weather-odds/issues/8) | Which dashboard framework? | Streamlit, Dash as the fallback ([comparison](research/dashboard-frameworks.md)). |
| [#3](https://github.com/valentina98/weather-odds/issues/3) | Environment: allow the data hosts and make the CDS key reachable, so station data and CERRA can be tested. | Owner action; see the issue. |

## Answered

| Issue | Question | Answer (2026-10-28/29) | Recorded as |
|---|---|---|---|
| [#2](https://github.com/valentina98/weather-odds/issues/2) | Code licence? | MIT, as proposed. | D16, `LICENSE` |
| [#3](https://github.com/valentina98/weather-odds/issues/3) | Copernicus key for CERRA? | Test all databases and several year ranges (e.g. the last 10 years) before implementing; expected early-October warming. The owner adds the key. | D24, [early-october.md](research/early-october.md) |
| [#4](https://github.com/valentina98/weather-odds/issues/4) | Which places? | Only Plovdiv for now; precision over other cities; Sofia and Varna possibly later. | D17 |
| [#5](https://github.com/valentina98/weather-odds/issues/5) | "Good day" per activity? | No activities. One outdoor-weather scale from green (good) to red (bad); extreme heat is bad. | D18, D19 |
| [#6](https://github.com/valentina98/weather-odds/issues/6) | Which years are "typical"? | Configurable; default the last 30 complete years; the user can pick a smaller range in the dashboard. | D13 |
| [#7](https://github.com/valentina98/weather-odds/issues/7) | Seasonal outlook? | No: only statistics for that month/week/day/time, never current weather. Validate with leave-one-year-out cross-validation. | D23, D25, [validation.md](research/validation.md) |
| [#8](https://github.com/valentina98/weather-odds/issues/8) | Local or hosted? | Local only; compare dashboard frameworks. | D22, [dashboard-frameworks.md](research/dashboard-frameworks.md) |
| [#9](https://github.com/valentina98/weather-odds/issues/9) | Language and dates? | English only, dd.mm.yyyy. | D28 |
| [#10](https://github.com/valentina98/weather-odds/issues/10) | First screen? | No activity selection. Timeframe (default ok), optional time (default: during the day), default granularity week. No best-days list; colours are enough. Selecting a day/week/month opens a detail panel. Patterns and Data tabs: yes. | D21 |
| [#11](https://github.com/valentina98/weather-odds/issues/11) | Other local patterns? | None known. | D30 |

## Questions answered in chat (2026-10-28)

| Question | Answer |
|---|---|
| What is it for? | Organising outdoor events: friend gatherings, hikes, walks, outdoor activities. |
| Which cities? | First answer: any city configurable, only Plovdiv tested. Narrowed in #4 to Plovdiv only. |
| Daily or weekly? | Daily if possible; otherwise selectable. The user selects month / week / day / time. |
| Who uses it? | Configurable, runnable by other developers, public repo, with a dashboard for analysis. |
| Commercial? | No. Nothing is paid by anyone. |
| Bulgarian vs global data? | Prefer Bulgarian precision over supporting other countries. |
| Repo name | `weather-odds` |
