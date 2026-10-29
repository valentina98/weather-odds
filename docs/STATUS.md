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
  - [dashboard framework comparison](research/dashboard-frameworks.md) (#8).
- **Spec updated**: [requirements](spec/requirements.md), [methodology](spec/methodology.md), [architecture](spec/architecture.md), [vision](vision.md).

## Waiting for the owner

See [open-questions.md](open-questions.md). In short:

1. **#5:** confirm the outdoor-weather scale (thresholds, rain rule, calendar colour).
2. **#6:** turn on trend adjustment for temperature by default?
3. **#8:** pick the dashboard framework (Streamlit proposed).
4. **#3:** the `weather-odds` cloud environment needs:
   - network access to the station-data hosts and Copernicus;
   - the CDS key available to a new session.

   Then the station sources and CERRA can be compared, as the owner asked.
5. Review and merge PR #1 and the follow-up PR; close #12 when the spec is done.

## Next steps (after the answers)

1. With network access: re-run all checks with station data (GSOD, Meteostat, NIMH, airport reports), test CERRA via the CDS, and calibrate ERA5 rain.
2. Validate the confirmed scale with the cross-validation.
3. Development plan: create issues for v1 milestones (data adapters → stats engine → dashboard), then implement in small PRs.

## How to resume in a new session

1. Read this file and [decisions.md](decisions.md).
2. Check open PRs and issues: `gh api repos/valentina98/weather-odds/pulls` and `gh api "repos/valentina98/weather-odds/issues?state=open"`.
3. To reproduce the research, follow [research/README.md](../research/README.md).
