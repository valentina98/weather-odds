# Early October: does it warm up, then get colder again?

_Run on 2026-10-29 with [`research/analyze_ranges.py`](../../research/analyze_ranges.py) and [`research/analyze_warm_spells.py`](../../research/analyze_warm_spells.py) for issue [#3](https://github.com/valentina98/weather-odds/issues/3). Numbers are in [early-october.json](early-october.json) and [warm-spells.json](warm-spells.json)._

**Short answer: not in early October.** In every source and every range of years, 1–10 October is about 2–3 °C cooler than 21–30 September. In the last 10 years, it was cooler in all 10 years. What the recent data does show is a **pause in the autumn cooling around 15–25 October** in the last 10–15 years. It appears in all three gridded sources, but it is not statistically significant. It comes from a few very warm late Octobers (2017–2019, 2022, 2023), and it was found by looking at the chart. It is a hint to re-check with station data, not a pattern the tool should report yet.

**Could a warm-up at a different date each year average out?** Yes, in principle, so it was tested by finding the events in each year first ([below](#does-the-timing-vary-from-year-to-year)). A warm-up followed by colder weather happens in about **half of all years in early October, but equally often in every other 10-day window of autumn**. It is a common autumn swing, not an early-October feature. In the last 10 years, 7 of 10 years had one in early October (other windows: 5 of 10 on average). With 10 years that difference is not significant, and 21–31 October had 8 of 10.

![Early October by range of years](img/early-october.png)

_Top: mean daily maximum, averaged over ±3 days, for different ranges of years. Bottom: each year since 2006, red where it was warmer than the 1996–2025 seasonal curve. The dashed lines mark 1–10 Oct and 15–25 Oct._

## What was tested

Daily maximum temperature, from every source reachable from this session, for six ranges of years:

| Source | Grid | Years |
|---|---|---|
| ERA5 | 25 km | 1960–2025 |
| ERA5-Land | 9 km | 1960–2025 |
| ECMWF IFS (operational model archive) | 9 km | 2017–2025 |
| Station (NOAA GSOD + Meteostat) | point | not reachable from this session yet; re-run when it is |

Two windows, each against the ten days before and after it:

- **1–10 October**, as described in [#3](https://github.com/valentina98/weather-odds/issues/3): compared with 21–30 Sep and 11–20 Oct.
- **15–25 October**, chosen after seeing the chart: compared with 5–14 Oct and 26 Oct – 4 Nov.

Two numbers per window, with 95% intervals from resampling whole years:

- **Change:** the window's mean minus the mean of the ten days before. Positive means it warms up into the window. Normal autumn cooling is about −2 to −3 °C per ten days.
- **Hump:** how far the window sits above the smooth seasonal curve, compared with the days before and after. Positive means "warmer, then colder again".

## Results

**1–10 October** (ERA5; ERA5-Land and IFS agree within 0.5 °C)

| Years | Change from 21–30 Sep | Hump | Years warmer than 21–30 Sep |
|---|---|---|---|
| Last 10 (2016–2025) | −2.8 °C (−4.4 to −1.4) | −0.8 °C (−2.1 to +0.4) | 0 of 10 |
| Last 15 (2011–2025) | −3.0 °C (−4.3 to −1.8) | −0.9 °C (−2.1 to +0.2) | 0 of 15 |
| Last 20 (2006–2025) | −2.5 °C (−3.9 to −1.1) | −0.4 °C (−1.6 to +0.8) | 3 of 20 |
| Last 30 (1996–2025) | −2.2 °C (−3.2 to −1.1) | 0.0 °C (−0.9 to +0.9) | 5 of 30 |
| 1960–1995 | −2.2 °C (−3.2 to −1.3) | −0.3 °C (−1.1 to +0.5) | 9 of 36 |
| All (1960–2025) | −2.2 °C (−2.9 to −1.5) | −0.1 °C (−0.7 to +0.4) | 14 of 66 |

ECMWF IFS, 2017–2025: −3.0 °C (−4.6 to −1.7), hump −1.0 °C (−2.1 to +0.05), 0 of 9 years warmer.

**Verdict:** early October cools at the normal rate. Recent years are no exception: in the last 10 and 15 years it cooled, if anything, slightly faster, and not a single year was warmer than late September.

**15–25 October** (chosen after seeing the chart)

| Years | Change from 5–14 Oct | Hump | Years warmer than 5–14 Oct |
|---|---|---|---|
| Last 10 (2016–2025) | −0.5 °C (−1.8 to +0.9) | +0.7 °C (−0.6 to +2.1) | 5 of 10 |
| Last 15 (2011–2025) | −0.8 °C (−2.0 to +0.3) | +0.7 °C (−0.4 to +1.9) | 7 of 15 |
| Last 20 (2006–2025) | −1.2 °C (−2.3 to −0.1) | +0.5 °C (−0.4 to +1.5) | 8 of 20 |
| Last 30 (1996–2025) | −1.9 °C (−2.9 to −0.8) | 0.0 °C (−0.7 to +0.9) | 11 of 30 |
| 1960–1995 | −3.1 °C (−4.0 to −2.3) | −0.3 °C (−1.2 to +0.6) | 3 of 36 |

ERA5-Land and IFS give the same picture: hump +0.5 and +0.6 °C for the last 10 years, intervals including zero.

**Verdict:** in recent years the temperature drop pauses in the second half of October, and roughly every second year that period was warmer than the ten days before. It was rare before 1996. The intervals include zero and the window was picked after looking, so this is **not established**. It matches the "warmer, then colder again" experience, but about two weeks later than described.

## Does the timing vary from year to year?

Averaging by calendar date can hide a warm-up that comes on a different day each year: a +4 °C spell on 3 October one year and 9 October the next adds only a little to the average of each date. So the events were found in each year first, and only then counted per 10-day window ([`analyze_warm_spells.py`](../../research/analyze_warm_spells.py), ERA5 daily maximum):

- **Warm-up** ("warmer, then colder again"): the 3-day mean rises by at least 3 °C within a week, peaks, and falls by at least 3 °C within a week. Counted at its peak.
- **Warm spell:** at least 3 days in a row at least 3 °C above the seasonal curve. Counted at its first day.

![Warm spells and warm-ups by 10-day window](img/warm-spells.png)

| Years | Warm-up peak in 1–10 Oct | Other autumn windows (mean) | Difference (95% interval) | Warm spell starting in 1–10 Oct | Other windows | Difference |
|---|---|---|---|---|---|---|
| All, 1961–2025 | 51% of years | 51% | 0 points (−14 to +14) | 32% | 30% | +2.5 points (−9 to +14) |
| Last 30, 1996–2025 | 53% | 51% | +2 points (−18 to +23) | 27% | 27% | 0 points (−16 to +17) |
| Last 10, 2016–2025 | 7 of 10 years | 48% | +22.5 points (−16 to +55) | 1 of 10 | 28% | −17.5 points (−34 to +6) |

**Verdict:**
- **The experience is real, but it is not specific to early October.** In about half of all years a warm-up followed by colder weather peaks in early October.
- The same happens just as often in the other autumn 10-day windows. Late September is even a bit more frequent: 63% of all years.
- Autumn weather in Plovdiv swings warm and cool every week or two. The warm-up that people remember in early October is one of these swings. It happens in most years, but on no fixed date.
- The last 10 years lean towards early October (7 of 10 years), but late October leans even more (8 of 10), and 10 years are too few to tell these apart from chance.

## What this means for the tool

- Early October is not a recurring warm spell, neither by calendar date nor as an event at varying dates. The [phase-0 check](plovdiv-data-check.md) reached the same conclusion with 30–66 years; this check adds the last 10–20 years, two more sources and the event count.
- The Patterns tab can still show useful event facts, e.g. "a warm-up followed by colder weather in about half of all years, in every 10-day window of autumn".
- The odds already show the effect of recent warm late Octobers when the reference years are narrowed to the last 10–15 (requirement F19).
- Re-run this check with station data once the network allows it, and again each year. The late-October pause becomes a "slight tendency" in the Patterns tab only if it passes the pattern tests in the [methodology](../spec/methodology.md#8-recurring-patterns).

## Reproduce

See [research/README.md](../../research/README.md).
