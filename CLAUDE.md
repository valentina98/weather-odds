# CLAUDE.md

Guidance for Claude sessions working in this repository.

## Project phase: specification (no implementation yet)

The owner (GitHub: valentina98) has asked for planning and documentation **before any implementation**.
Until the owner says the specification step is done:

- Do not write application code (no `src/`, no dashboard, no package).
- Research scripts are allowed under `research/` when they produce evidence for the docs. Keep them small, reproducible, and clearly separate from the future application.
- Record every finding, decision, and open question in the repo. The owner may start a new session at any time, so nothing important should live only in chat.

## Where things are

- `docs/` holds the research, draft spec, and decision log. Start with `docs/README.md` and `docs/STATUS.md`.
- Open questions for the owner are GitHub issues labelled `decision-needed`, assigned to valentina98, and collected in a tracking issue.
- Work happens on branches with pull requests into `main`. Check open PRs first: `gh api repos/valentina98/weather-odds/pulls`.
- GitHub GraphQL is unavailable from Claude Code sessions; use the REST API (`gh api ...`).

## Data and licences

- Never commit downloaded weather data. Scripts cache downloads in `.cache/` (git-ignored).
- The owner's use is non-commercial (friend gatherings, hikes, walks; nothing paid).
- Prefer Bulgarian precision over global coverage when the two conflict.

## Environment notes (cloud sessions)

- The free Open-Meteo API is often over its daily limit from cloud sessions (shared outgoing address). Sources that work without keys: NOAA GSOD, Meteostat bulk data, Iowa Environmental Mesonet (airport reports), NIMH open data (info.meteo.bg/openData), NASA POWER, Open-Meteo's AWS open-data bucket.
- Copernicus CDS needs a personal API key. If the owner adds one, it is read from the environment variable `CDSAPI_KEY` (URL `https://cds.climate.copernicus.eu/api`). Never ask for keys in chat.
