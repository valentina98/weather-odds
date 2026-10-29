# Status

_Last updated: 2026-10-29._

## Phase: development of v1

The owner signed off the specification on 2026-10-29 ("I approve, we can start development"; D44, [#12](https://github.com/valentina98/weather-odds/issues/12) closed). v1 is built milestone by milestone following the [development plan](development-plan.md). Each milestone is an issue in the [v1 milestone](https://github.com/valentina98/weather-odds/milestone/1).

| # | Milestone | Issue | State |
|---|---|---|---|
| 1 | Project skeleton | [#15](https://github.com/valentina98/weather-odds/issues/15) | in progress |
| 2 | Data adapters and cache | [#16](https://github.com/valentina98/weather-odds/issues/16) | not started |
| 3 | Plovdiv hourly table | [#17](https://github.com/valentina98/weather-odds/issues/17) | not started |
| 4 | Statistics engine | [#18](https://github.com/valentina98/weather-odds/issues/18) | not started |
| 5 | Validation command | [#19](https://github.com/valentina98/weather-odds/issues/19) | not started |
| 6 | Dashboard | [#20](https://github.com/valentina98/weather-odds/issues/20) | not started |
| 7 | Trend tools | [#21](https://github.com/valentina98/weather-odds/issues/21) | not started |
| 8 | Release v1.0 | [#22](https://github.com/valentina98/weather-odds/issues/22) | not started |

Keep this table current: update it in the pull request that starts or finishes a milestone.

## Waiting for the owner

- Review and merge the open pull requests (`gh api repos/valentina98/weather-odds/pulls`).

## Specification phase (done, 2026-10-28/29)

- **Research** on data sources, seasonal forecast providers, recurring weather patterns and licensing (see [docs/README.md](README.md)); PR [#1](https://github.com/valentina98/weather-odds/pull/1).
- **Owner's answers** in issues #2–#11 and #14 and in chat, all recorded in [decisions.md](decisions.md) (D1–D44) and [open-questions.md](open-questions.md). In short:
  - Plovdiv only, local only, English with dd.mm.yyyy dates, MIT licence, no forecasts, no paid data;
  - one outdoor-weather scale (green to red) with defaults the user can change, also per time of day;
  - default reference period: the last 30 complete years, with a switchable trend adjustment; no pooling by default; 1996 left out (no station data);
  - default time of day: one daylight window (latest sunrise to earliest sunset) for the whole timeframe;
  - settings independent of each other;
  - trend tools to investigate patterns like the early-October warm-up;
  - Dash for the dashboard.
- **Data design** ([all sources](research/all-sources.md)): temperature from the station's hourly measurements, rain and gusts from ERA5 with a calibrated threshold, thunder from the airport reports. CERRA and Open-Meteo's "ERA5 seamless" are not used. Gaps are filled per the [gap plan](development-plan.md#filling-the-data-gaps).
- **Findings**: [early October](research/early-october.md) has no warm-up specific to it; [validation](research/validation.md) of the odds and of the scale; [scale preview](research/weather-scale.md).
- **Prototypes**: the [Dash prototype](../research/prototype/README.md) is the starting point for milestone 6; the Streamlit one is in the closed PR [#13](https://github.com/valentina98/weather-odds/pull/13).

## How to resume in a new session

1. Read [CLAUDE.md](../CLAUDE.md), this file and [decisions.md](decisions.md).
2. Check open pull requests and issues: `gh api repos/valentina98/weather-odds/pulls` and `gh api "repos/valentina98/weather-odds/issues?state=open"`.
3. Continue the first milestone in the table above that is not done. Its issue lists the contents, the "done when" check and the research code to port.
4. To reproduce the research, follow [research/README.md](../research/README.md).
