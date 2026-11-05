# Status

_Last updated: 2026-11-05._

## Phase: development of v1

The owner signed off the specification on 2026-10-29 ("I approve, we can start development"; D44, [#12](https://github.com/valentina98/weather-odds/issues/12) closed). v1 is built milestone by milestone following the [development plan](development-plan.md). Each milestone is an issue in the [v1 milestone](https://github.com/valentina98/weather-odds/milestone/1).

| # | Milestone | Issue | State |
|---|---|---|---|
| 1 | Project skeleton | [#15](https://github.com/valentina98/weather-odds/issues/15) | done ([PR #24](https://github.com/valentina98/weather-odds/pull/24)) |
| 2 | Data adapters and cache | [#16](https://github.com/valentina98/weather-odds/issues/16) | done ([PR #25](https://github.com/valentina98/weather-odds/pull/25), [PR #26](https://github.com/valentina98/weather-odds/pull/26)): station, airport, NOAA, NIMH and ERA5 (AWS bucket, D45) sources, cache, `weather-odds prefetch` |
| 3 | Plovdiv hourly table | [#17](https://github.com/valentina98/weather-odds/issues/17) | part 1 in review in [PR #27](https://github.com/valentina98/weather-odds/pull/27): hourly and daily tables, temperature fills, calibrated wet days, thunder days, daylight, `weather-odds build` and `check` ([table checks](research/table-checks.md)); part 2 (gap plan) next |
| 4 | Statistics engine | [#18](https://github.com/valentina98/weather-odds/issues/18) | not started |
| 5 | Validation command | [#19](https://github.com/valentina98/weather-odds/issues/19) | not started |
| 6 | Dashboard | [#20](https://github.com/valentina98/weather-odds/issues/20) | not started |
| 7 | Trend tools | [#21](https://github.com/valentina98/weather-odds/issues/21) | not started |
| 8 | Release v1.0 | [#22](https://github.com/valentina98/weather-odds/issues/22) | not started |

Keep this table current: update it in the pull request that starts or finishes a milestone.

## Waiting for the owner

- Review and squash-merge [PR #27](https://github.com/valentina98/weather-odds/pull/27) (milestone 3, part 1). Decisions D46–D50 in it are implementation choices you can object to in the PR; the main findings are in [table-checks.md](research/table-checks.md).

## Next (milestone 3, part 2)

The [gap plan](development-plan.md#filling-the-data-gaps) rows still open for milestone 3:

1. **Thunder by hour for NOAA's thunder days** (1997–2011): place each flagged day's thunder in its hours. CAPE and convective rain are not in the AWS bucket (only on the Copernicus CDS, which needs a key, against F21), so first try ERA5's rain and the hour of day; fit on 2012–2014 and 2019–2021, check on 2022–2025 against the airport's thunder hours. Then decide 2015–2018 (model signs, or leave them out of the thunder numbers).
2. **Thunder reports falling since 2022** (airport: about 50 days a year in 2019–2021, 13 in 2025; NOAA's flag even fewer): check whether this is reporting or weather.
3. **Wet-day threshold disagreement** (1973–1999 about 1.7 mm, 2022–2025 about 1.1 mm): the airport's rain days 2012–2025 as a third check; ECA&D's Chirpan and Ivailo stations (check their years and licence).
4. **Wind:** ERA5's 10 m wind against the station's mean wind by month (needs ERA5's wind components and the station's wind from Meteostat).

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
2. Check open pull requests and issues: `gh api repos/valentina98/weather-odds/pulls` and `gh api "repos/valentina98/weather-odds/issues?state=open"`. Progress notes for the running milestone are also in its issue's comments.
3. Continue the first milestone in the table above that is not done. Its issue lists the contents, the "done when" check and the research code to port; the "Next" list above says where the last session stopped.
4. `uv sync`, then `uv run weather-odds prefetch` (a few minutes) and `uv run weather-odds check` to rebuild the tables and see the checks.
5. To reproduce the research, follow [research/README.md](../research/README.md).
