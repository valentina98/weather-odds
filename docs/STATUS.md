# Status

_Last updated: 2026-10-28._

## Phase: specification (no implementation yet)

The owner asked for research, planning and documentation first. Development starts only after the owner has answered the open questions and closed the specification tracking issue.

## Done

- **Research** on data sources, seasonal forecast providers, recurring weather patterns and licensing (see [docs/README.md](README.md)).
- **Phase-0 data check for Plovdiv** using only no-key sources: NOAA GSOD, Meteostat, airport reports (IEM), NIMH open data, NASA POWER, and ERA5 / ERA5-Land read from Open-Meteo's AWS open data. Results: [research/plovdiv-data-check.md](research/plovdiv-data-check.md).
- **Draft spec**: [requirements](spec/requirements.md), [methodology](spec/methodology.md), [architecture proposal](spec/architecture.md).
- **Decision log** and **open questions** as GitHub issues assigned to the owner.

## Waiting for the owner

See [open-questions.md](open-questions.md). The most important ones for starting development: code licence, default "good day" thresholds, places to test, reference period.

## Next steps (after the answers)

1. Update the spec with the answers; mark decisions as accepted.
2. Owner closes the specification tracking issue.
3. Development plan: create issues for v1 milestones (data adapters → stats engine → dashboard), then implement in small PRs.

## How to resume in a new session

1. Read this file and [decisions.md](decisions.md).
2. Check open PRs and issues: `gh api repos/valentina98/weather-odds/pulls` and `gh api "repos/valentina98/weather-odds/issues?state=open"`.
3. To reproduce the research, follow [research/README.md](../research/README.md).
