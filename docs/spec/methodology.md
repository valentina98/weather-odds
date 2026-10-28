# Methodology (draft)

How weather-odds turns historical data into odds. The phase-0 analysis in [`research/analyze_plovdiv.py`](../../research/analyze_plovdiv.py) is a working prototype of most of these steps; its results are in [the Plovdiv data check](../research/plovdiv-data-check.md).

## 1. Data per location

For each location the tool builds one **hourly** and one **daily** table in local time:

| Field | Unit | Main source |
|---|---|---|
| temperature | °C | ERA5 (≈25 km), corrected for elevation. At Plovdiv it matches the station within 0.1 °C on average; ERA5-Land (≈9 km) runs 2–3 °C too cool in summer there, so finer grids are used only after a station check. |
| precipitation | mm | ERA5 (≈25 km), calibrated against station wet-day frequencies (at Plovdiv ERA5 has 39% more wet days than the station in 1973–1999 and 8% more in 2022–2025); CERRA (5.5 km) to be evaluated |
| snowfall, snow depth | mm water / m | ERA5 / ERA5-Land |
| wind gusts | km/h | ERA5 |
| cloud cover / sunshine | % / h | ERA5 |
| sunrise, sunset | time | computed from coordinates |

**Elevation correction.** Gridded temperature is for the grid cell's average height. It is shifted to the location's elevation with a lapse rate of 0.65 °C per 100 m (the standard atmosphere; Open-Meteo applies a similar correction). In winter, valley inversions (common in the Plovdiv basin) break this rule; the station check measures how much.

## 2. Reference period

Default: **the last 30 complete years** (currently 1996–2025), configurable. The full record is used only for pattern detection, after removing the long-term trend.

Reason: Plovdiv's daily maximum temperature has risen noticeably since the 1980s (see the data check). Using 1961–1990 or the full record would make "typical" temperatures too cold.

## 3. Day-of-year statistics and pooling

- Every date is mapped to a 365-day calendar (29 February is dropped).
- A daily statistic for date *d* uses all reference years and the days *d−w … d+w* ("pooling window" *w*). Default *w* = 3 days (a week centred on the date). The user can change it: 0 for raw single days, 7 or 15 for smoother curves.
- Week, month and hour views aggregate the same historical days directly (no extra smoothing).

## 4. Definitions

| Term | Definition (default, configurable) |
|---|---|
| Wet day | ≥ 1.0 mm in the 24 hours of the local calendar day |
| Rain during the event | ≥ 0.2 mm in at least one hour inside the event window (to be calibrated against airport rain reports) |
| Thunder | ERA5 has no thunder variable; use airport reports where available, otherwise convective precipitation as a proxy (to be evaluated) |
| Frost | daily minimum < 0 °C |
| Heat | maximum during the event window ≥ 32 °C (profile-dependent) |
| Strong wind | gust ≥ 50 km/h during the event window (profile-dependent) |

## 5. Odds and joint conditions

- A **chance** is the share of historical days (or hours) in the pooled set that met a condition.
- A **"good day" chance** is the share of historical days that met **all** of the profile's conditions at once. Multiplying separate chances would be wrong because rain, temperature and wind are linked.
- **Percentiles** (10th, 50th, 90th) describe the range of temperatures.

## 6. Uncertainty

- Intervals are 95% **bootstrap intervals over years**: whole years are resampled, which keeps the day-to-day correlation inside a year.
- Every view shows the number of years behind it.
- Measured at Plovdiv with 30 years of data, the typical 95% half-width of a wet-day chance is ±15 points for a single date, ±7 with ±3-day pooling, ±5 with ±7 days and ±3 with ±15 days (temperature: ±1.6 / ±1.1 / ±0.9 / ±0.7 °C). The dashboard uses this to warn when a daily view is mostly noise.

## 7. Recurring patterns

A pattern is reported only if all of these hold:

1. **Baseline:** the pooled curve departs from a smooth seasonal baseline (least-squares fit of 3 annual harmonics).
2. **Significance:** the 95% bootstrap interval of the departure excludes zero for at least 5 consecutive days.
3. **Stability:** the departure points the same way in both halves of the record (split-sample check).
4. **Trend removed:** temperature patterns use detrended data so warming does not create false patterns.

Patterns are shown as frequencies ("a warm spell in this fortnight in X% of years"), with the dates they usually occur.

At Plovdiv this test found no strong calendar patterns: the autumn patterns from local experience did not pass, and the few candidates (e.g. a cooler 3–8 September) are about 1 °C or 5 percentage points. Patterns are therefore a secondary feature, labelled as "slight tendencies" with their evidence.

## 8. Combining sources (later)

- v1: gridded data with a simple station-based calibration where station data exists:
  - temperature: monthly mean bias correction against the station (ERA5 at Plovdiv: +0.6 °C in winter, −0.4 °C in July);
  - rain: per-month wet-day threshold chosen so ERA5's wet-day frequency matches the station's (GSOD 1973–1999, NIMH from 2022);
  - hourly rain: threshold chosen so the share of rainy hours matches airport reports.
- Show station comparisons in a "data quality" panel.
- Later: quantile mapping, CERRA, and more stations from the NIMH network.

## 9. Known limitations

- Gridded rain is an area average: it shows more frequent light rain and less intense heavy rain than a single point gets.
- Station records for Plovdiv have gaps and changes in reporting (see data sources).
- Patterns are probabilistic and shift with climate change; the tool shows how reliable each one has been, not that it will happen.
