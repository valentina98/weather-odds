# Open questions

Questions for the owner are GitHub issues assigned to them, collected in the tracking issue **[#12 Specification phase: questions and sign-off](https://github.com/valentina98/weather-odds/issues/12)**. Answers are copied into [decisions.md](decisions.md) and the spec. Issues are closed once their answer is recorded.

## Still open (as of 2026-10-29)

| Issue | Questions | Proposed answers |
|---|---|---|
| [#14](https://github.com/valentina98/weather-odds/issues/14) | (1) different scale defaults by time of day? (2) daylight window for a whole timeframe: latest sunrise to earliest sunset, or the average? (3) which questions the trend tools should answer; (4) leave out 1996 or fill it from ERA5? (5) a written request to NIMH for station rain 2000–2021, if free neighbours fail? | (1) same for all bands; (2) latest sunrise to earliest sunset; (3) warm-ups, warm spells, cold snaps, rainy spells, heat waves, first/last frost, warming by season; (4) leave it out; (5) try ECA&D's Chirpan and Ivailo first |

Then the sign-off: review the spec and close [#12](https://github.com/valentina98/weather-odds/issues/12).

## Answered

| Issue | Question | Answer (2026-10-28/29) | Recorded as |
|---|---|---|---|
| [#2](https://github.com/valentina98/weather-odds/issues/2) | Code licence? | MIT, as proposed. | D16, `LICENSE` |
| [#3](https://github.com/valentina98/weather-odds/issues/3) | Copernicus key for CERRA? | Test all databases and several year ranges (e.g. the last 10 years) before implementing; expected early-October warming. The owner added the key and opened the network. Could a warm-up at varying dates average out? (Tested: no early-October-specific warm-up.) All sources tested; CERRA not used. | D24, D33–D38, [all-sources.md](research/all-sources.md), [early-october.md](research/early-october.md) |
| [#4](https://github.com/valentina98/weather-odds/issues/4) | Which places? | Only Plovdiv for now; precision over other cities; Sofia and Varna possibly later. | D17 |
| [#5](https://github.com/valentina98/weather-odds/issues/5) | "Good day" per activity? | No activities. One outdoor-weather scale from green to red; extreme heat is bad. Defaults set by us, changeable in the dashboard. Relative colours as an option, absolute by default. | D18–D20, D31, D32 |
| [#6](https://github.com/valentina98/weather-odds/issues/6) | Which years are "typical"? | Configurable; default the last 30 complete years; narrowable in the dashboard. Trend adjustment agreed, with an on/off switch, clearly shown, default from the config. | D13, D27 |
| [#7](https://github.com/valentina98/weather-odds/issues/7) | Seasonal outlook? | No: only statistics for that month/week/day/time, never current weather. Validate with leave-one-year-out cross-validation. | D23, D25, [validation.md](research/validation.md) |
| [#8](https://github.com/valentina98/weather-odds/issues/8) | Local or hosted? Which framework? | Local only. Pick one, show first results, then re-evaluate; both were built. **Dash**, for scalability. | D22, D29 |
| [#9](https://github.com/valentina98/weather-odds/issues/9) | Language and dates? | English only, dd.mm.yyyy. | D28 |
| [#10](https://github.com/valentina98/weather-odds/issues/10) | First screen? | No activity selection. Timeframe (default ok), optional time (default: during the day), default granularity week. No best-days list; colours are enough. Selecting a day/week/month opens a detail panel. Patterns and Data tabs: yes. | D21 |
| [#11](https://github.com/valentina98/weather-odds/issues/11) | Other local patterns? | None known. | D30 |

## Answered in chat (2026-10-29)

| Topic | Answer | Recorded as |
|---|---|---|
| Temperature from the Plovdiv station | ok | D34 |
| Scale defaults | ok, as long as the user can change them; penalties may differ by time of day | D20, F17 |
| Trend adjustment | ok; transparent and switchable | D27, F27 |
| Default time of day | daylight, as one window for the whole selected period | D21, F7 |
| Investigating trends like the warm-up | wanted in the tool | D39, F29–F31 |
| Data gaps | make a plan | D40, [gap plan](development-plan.md#filling-the-data-gaps) |

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
