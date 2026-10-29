# Open questions

Questions for the owner are GitHub issues assigned to them, collected in the tracking issue **[#12 Specification phase: questions and sign-off](https://github.com/valentina98/weather-odds/issues/12)**. Answers are copied into [decisions.md](decisions.md) and the spec. Issues are closed once their answer is recorded.

## Still open (as of 2026-10-29)

| Issue | Question | State |
|---|---|---|
| [#8](https://github.com/valentina98/weather-odds/issues/8) | Streamlit or Dash, after seeing the same screens built in both? | [Side by side](research/dashboard-frameworks.md#streamlit-and-dash-side-by-side); the owner's rule: keep Streamlit unless Dash is better or looks better. |

## Answered

| Issue | Question | Answer (2026-10-28/29) | Recorded as |
|---|---|---|---|
| [#2](https://github.com/valentina98/weather-odds/issues/2) | Code licence? | MIT, as proposed. | D16, `LICENSE` |
| [#3](https://github.com/valentina98/weather-odds/issues/3) | Copernicus key for CERRA? | Test all databases and several year ranges (e.g. the last 10 years) before implementing; expected early-October warming. The owner added the key and opened the network. Could a warm-up at varying dates average out? (Tested: no early-October-specific warm-up.) All sources tested; CERRA not used. | D24, D33–D38, [all-sources.md](research/all-sources.md), [early-october.md](research/early-october.md) |
| [#4](https://github.com/valentina98/weather-odds/issues/4) | Which places? | Only Plovdiv for now; precision over other cities; Sofia and Varna possibly later. | D17 |
| [#5](https://github.com/valentina98/weather-odds/issues/5) | "Good day" per activity? | No activities. One outdoor-weather scale from green to red; extreme heat is bad. Defaults set by us, changeable in the dashboard. Relative colours as an option, absolute by default. | D18–D20, D31, D32 |
| [#6](https://github.com/valentina98/weather-odds/issues/6) | Which years are "typical"? | Configurable; default the last 30 complete years; narrowable in the dashboard. Trend adjustment agreed, with an on/off switch, clearly shown, default from the config. | D13, D27 |
| [#7](https://github.com/valentina98/weather-odds/issues/7) | Seasonal outlook? | No: only statistics for that month/week/day/time, never current weather. Validate with leave-one-year-out cross-validation. | D23, D25, [validation.md](research/validation.md) |
| [#8](https://github.com/valentina98/weather-odds/issues/8) | Local or hosted? Which framework? | Local only. Pick one, show first results, then re-evaluate; keep Streamlit unless Dash is better or looks better; build the Dash screens to compare. | D22, D29 |
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
