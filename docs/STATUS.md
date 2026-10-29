# Status

_Last updated: 2026-10-29._

## Phase: specification (no implementation yet)

The owner asked for research, planning and documentation first. Development starts only after the owner closes the specification tracking issue [#12](https://github.com/valentina98/weather-odds/issues/12).

## Done

- **Research** on data sources, seasonal forecast providers, recurring weather patterns and licensing (see [docs/README.md](README.md)). PR [#1](https://github.com/valentina98/weather-odds/pull/1).
- **Phase-0 data check for Plovdiv** with all no-key sources: [plovdiv-data-check.md](research/plovdiv-data-check.md).
- **Owner's answers to #2–#11** (2026-10-28/29), recorded in [decisions.md](decisions.md) and the spec:
  - Plovdiv only;
  - one outdoor-weather scale instead of activities;
  - default reference period of 30 years, narrowable in the dashboard;
  - no forecasts;
  - local only;
  - English with dd.mm.yyyy dates;
  - MIT licence.
- **Follow-up research** on the answers:
  - [early October by source and range of years](research/early-october.md) (#3);
  - [cross-validation of the odds](research/validation.md) (#7);
  - [preview of the outdoor-weather scale](research/weather-scale.md) (#5);
  - [dashboard framework comparison](research/dashboard-frameworks.md) and a throwaway Streamlit prototype (#8);
  - warm-ups counted per year, to check whether a warm-up at varying dates averages out (#3).
- **Second round of answers** (2026-10-29): scale thresholds are defaults changeable in the dashboard; colour measure and relative colours as options (#5); trend adjustment with an on/off switch (#6). Issues #2, #4–#7 and #9–#11 are closed.
- **All data sources tested** (#3, with full network access): [all-sources.md](research/all-sources.md).
  - Temperature from the station's hourly measurements; rain and gusts from ERA5 with a calibrated threshold; thunder from the airport reports.
  - CERRA is not more precise; Open-Meteo's "ERA5 seamless" is ERA5-Land and 3 °C too cold in summer.
  - Early October re-checked with the station: no warm-up specific to it.
- **Validation** against the station and of the scale's calendar colour: [validation.md](research/validation.md).
- **Dash prototype** with the same screens as the Streamlit one, compared in [dashboard-frameworks.md](research/dashboard-frameworks.md#streamlit-and-dash-side-by-side). **The owner chose Dash** (#8); the Streamlit code was moved to the closed pull request [#13](https://github.com/valentina98/weather-odds/pull/13).
- **Owner's chat answers (2026-10-29)** recorded: station temperature, editable scale with time-of-day thresholds, transparent trend adjustment, one daylight window per timeframe, trend tools (D39), and a [gap plan](development-plan.md#filling-the-data-gaps).
- **Spec updated**: [requirements](spec/requirements.md), [methodology](spec/methodology.md), [architecture](spec/architecture.md), [vision](vision.md); **[development plan](development-plan.md)** drafted.

## Waiting for the owner

1. Answer the five short questions in [#14](https://github.com/valentina98/weather-odds/issues/14) (each has a proposed answer).
2. Review the branch `docs/spec-answers` (on top of PR #1), including the proposed data design (D34–D38) and the [development plan](development-plan.md).
3. Close #12 when the spec is done. Then the development plan becomes GitHub issues and implementation starts.

## Next steps (after the sign-off)

1. Create the v1 milestone issues from the [development plan](development-plan.md).
2. Implement in small PRs, starting with the project skeleton and the data adapters.

## How to resume in a new session

1. Read this file and [decisions.md](decisions.md).
2. Check open PRs and issues: `gh api repos/valentina98/weather-odds/pulls` and `gh api "repos/valentina98/weather-odds/issues?state=open"`.
3. To reproduce the research, follow [research/README.md](../research/README.md).
