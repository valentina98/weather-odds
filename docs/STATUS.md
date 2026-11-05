# Status

_Last updated: 2026-11-05._

## Phase: development of v1

The owner signed off the specification on 2026-10-29 ("I approve, we can start development"; D44, [#12](https://github.com/valentina98/weather-odds/issues/12) closed). v1 is built milestone by milestone following the [development plan](development-plan.md). Each milestone is an issue in the [v1 milestone](https://github.com/valentina98/weather-odds/milestone/1).

| # | Milestone | Issue | State |
|---|---|---|---|
| 1 | Project skeleton | [#15](https://github.com/valentina98/weather-odds/issues/15) | done ([PR #24](https://github.com/valentina98/weather-odds/pull/24)) |
| 2 | Data adapters and cache | [#16](https://github.com/valentina98/weather-odds/issues/16) | done ([PR #25](https://github.com/valentina98/weather-odds/pull/25), [PR #26](https://github.com/valentina98/weather-odds/pull/26)): station, airport, NOAA, NIMH and ERA5 (AWS bucket, D45) sources, cache, `weather-odds prefetch` |
| 3 | Plovdiv hourly table | [#17](https://github.com/valentina98/weather-odds/issues/17) | in review: part 1 in [PR #27](https://github.com/valentina98/weather-odds/pull/27) (temperature gap fills, D46); part 2 in [PR #28](https://github.com/valentina98/weather-odds/pull/28), built on #27 (hourly and daily tables, calibrated wet days, thunder days, daylight, `weather-odds build`, comparison with the station: [table checks](research/table-checks.md)); part 3 (the rest of the gap plan) next |
| 4 | Statistics engine | [#18](https://github.com/valentina98/weather-odds/issues/18) | not started |
| 5 | Validation command | [#19](https://github.com/valentina98/weather-odds/issues/19) | not started |
| 6 | Dashboard | [#20](https://github.com/valentina98/weather-odds/issues/20) | not started |
| 7 | Trend tools | [#21](https://github.com/valentina98/weather-odds/issues/21) | not started |
| 8 | Release v1.0 | [#22](https://github.com/valentina98/weather-odds/issues/22) | not started |

Keep this table current: update it in the pull request that starts or finishes a milestone.

## Waiting for the owner

1. Squash-merge [PR #27](https://github.com/valentina98/weather-odds/pull/27) (milestone 3, part 1), then [PR #28](https://github.com/valentina98/weather-odds/pull/28) (part 2), which builds on it. After #27 is merged, #28 is updated from `main` (merge, no force push) so its diff shows only part 2. D47–D51 in #28 are implementation choices and findings you can object to in the PR.
2. Answer [#29](https://github.com/valentina98/weather-odds/issues/29): thunder by hour and strong wind, two choices with a recommendation each.

## Next (milestone 3, part 3, after #29)

1. Build the answers to #29: thunder by hour for NOAA's thunder days (1997–2011) and what counts for 2022 onward; strong wind (ERA5's gusts against the airport's). The analysis is in [table-checks.md](research/table-checks.md#thunder-the-reports-changed-in-2022) and `research/check_wind_thunder.py`.
2. Then milestone 3 is done: close #17, update this table, start milestone 4 (#18).

Notes for milestone 4:
- A tested port of the outdoor-weather scale (hour factors per time band, day scores with the rain caps) was written on 05.11.2026 and left out of #28 to keep it to milestone 3. It is in PR #28's history: `git show 9e52b2e:src/weather_odds/stats/scale.py` and `git show 9e52b2e:tests/test_scale.py` (`git fetch origin pull/28/head` first).
- D50: frost from the hourly minimum may miss some nights; compare with NOAA's daily minimum.
- Hours with no thunder data (1996, 2015–2018) need a rule in the scale; #29 decides the rest.

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
