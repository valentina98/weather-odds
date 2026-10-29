# Open questions

All open questions are GitHub issues assigned to the owner, collected in the tracking issue **[#12 Specification phase: questions and sign-off](https://github.com/valentina98/weather-odds/issues/12)**. Answers are copied into [decisions.md](decisions.md) and the spec once given.

| Issue | Question | Proposed answer | Affects |
|---|---|---|---|
| [#5](https://github.com/valentina98/weather-odds/issues/5) | What makes a "good day" for each activity (default thresholds)? | Defaults per gathering / walk / hike, all editable | Requirements F10, F16, F17 |
| [#4](https://github.com/valentina98/weather-odds/issues/4) | Which places to configure and test (venues, hiking spots)? | Plovdiv plus 1–3 hiking spots with elevation | F2, F4, acceptance |
| [#6](https://github.com/valentina98/weather-odds/issues/6) | Which years define "typical" weather? | Last 30 complete years, selectable | Methodology §2, D13 |
| [#10](https://github.com/valentina98/weather-odds/issues/10) | What does the dashboard show first? | Calendar heat map of good-day odds + best days/weeks | F5–F14 |
| [#2](https://github.com/valentina98/weather-odds/issues/2) | Code licence? | MIT | D16 |
| [#8](https://github.com/valentina98/weather-odds/issues/8) | Local-only or also hosted; dashboard framework? | Local-only v1, Streamlit | N7, architecture |
| [#3](https://github.com/valentina98/weather-odds/issues/3) | Set up a Copernicus key for CERRA? | Later; test CERRA first | Data sources, D12 |
| [#7](https://github.com/valentina98/weather-odds/issues/7) | Show a seasonal outlook? | Links only in v1 | F15 |
| [#9](https://github.com/valentina98/weather-odds/issues/9) | Interface language(s) and date format? | English first, translatable | N6 |
| [#11](https://github.com/valentina98/weather-odds/issues/11) | Other local weather patterns to test? | – | Research |

## Questions answered so far (in chat, 2026-10-28)

| Question | Answer |
|---|---|
| What is it for? | Organising outdoor events: friend gatherings, hikes, walks, outdoor activities. |
| Which cities? | Any city can be configured, but only Plovdiv is tested; data is gathered only for selected places. |
| Daily or weekly? | Daily if possible; otherwise selectable. The user selects month / week / day / time. |
| Who uses it? | Configurable, runnable by other developers, public repo, with a dashboard for analysis. |
| Commercial? | No. Nothing is paid by anyone. |
| Bulgarian vs global data? | Prefer Bulgarian precision over supporting other countries. |
| Repo name | `weather-odds` |
