# Methodology (draft)

How weather-odds turns historical data into odds and colours. Updated 2026-10-29 with the owner's answers (#4–#7) and the [cross-validation](../research/validation.md).

The research scripts are working prototypes of most of these steps:
- [`research/analyze_plovdiv.py`](../../research/analyze_plovdiv.py): sources, patterns, noise.
- [`research/validate_odds.py`](../../research/validate_odds.py): cross-validation.
- [`research/preview_scale.py`](../../research/preview_scale.py): the outdoor-weather scale.

## 1. Data for Plovdiv

For Plovdiv the tool builds one **hourly** and one **daily** table in local time:

| Field | Unit | Main source |
|---|---|---|
| temperature | °C | ERA5 (≈25 km), corrected for elevation. At Plovdiv it matches the station within 0.1 °C on average. ERA5-Land (≈9 km) runs 2–3 °C too cool in summer there, so finer grids are used only after a station check. ECMWF IFS (≈9 km, from 2017) is a second check for recent years. |
| precipitation | mm | ERA5 (≈25 km), calibrated against station wet-day frequencies. At Plovdiv ERA5 has 39% more wet days than the station in 1973–1999 and 8% more in 2022–2025. CERRA (5.5 km) still to be evaluated. |
| snowfall, snow depth | mm water / m | ERA5 / ERA5-Land |
| wind gusts | km/h | ERA5 |
| cloud cover | % | ERA5 |
| thunder | yes/no | airport reports (LBPD, from 2012); a model proxy to be tested (see §5) |
| sunrise, sunset | time | computed from coordinates |

**Elevation correction.** Gridded temperature is for the grid cell's average height. It is shifted to Plovdiv's station elevation (179 m) with a lapse rate of 0.65 °C per 100 m. In winter, valley inversions in the Plovdiv basin break this rule; the station check measures how much.

## 2. Reference period

- **Default: the last 30 complete years** (currently 1996–2025), set in the config ([#6](https://github.com/valentina98/weather-odds/issues/6)).
- In the dashboard the user can **narrow it to a shorter range** within the configured period, e.g. the last 10 years.
- **Trend adjustment** for temperature *(proposed default, needs the owner's confirmation)*: each reference year's temperatures are shifted by the linear warming trend fitted to the reference years, up to the current year. In the cross-validation, plain 30-year statistics predicted temperatures 1.07 °C too cold on average, and trend adjustment cut that to 0.32 °C and lowered the error by 0.10 °C. It uses only the historical record, not current weather.
- Pattern detection uses the full record after removing the long-term trend.

## 3. Day-of-year statistics and pooling

- Every date is mapped to a 365-day calendar (29 February is dropped).
- A daily statistic for date *d* uses all reference years and the days *d−w … d+w* (the "pooling window" *w*).
- **Default *w* = 7 days** (two weeks centred on the date). The cross-validation scored ±7 better than ±3 for both temperature and rain. The user can change it: 0 for raw single days, up to 15 for smoother curves.
- Week and month views use all days of that week or month in the reference years directly (no extra pooling).

## 4. Outdoor-weather scale

*Proposed for [#5](https://github.com/valentina98/weather-odds/issues/5); thresholds are config defaults.* There are no activity profiles. One scale rates how good the weather was for being outdoors. A preview for Plovdiv is in [weather-scale.md](../research/weather-scale.md).

**Each hour** gets a score from 0 to 100:

> hour score = 100 × temperature factor × rain factor × wind factor × thunder factor

Each factor runs from 1 (no problem) to 0. Multiplying means one bad factor makes the hour bad, however good the others are.

| Factor | 1 (no penalty) | In between | Lowest |
|---|---|---|---|
| Temperature (air, °C) | 18–26 °C | falls linearly below 18 °C and above 26 °C | 0 at 0 °C or colder, and at 38 °C or hotter (extreme heat is bad weather) |
| Rain in the hour | less than 0.2 mm | 0.5 for 0.2–1 mm | 0.2 for 1 mm or more |
| Wind gusts | up to 30 km/h | falls linearly | 0 at 75 km/h |
| Thunder | none | – | 0.2 when thunder is reported or likely *(data source to be tested)* |

**A period's score** (one day and the chosen hours, by default sunrise to sunset) is the mean of its hour scores, with two caps for rain over the chosen hours:
- 1 mm or more: at most 59 (Fair);
- 5 mm or more: at most 39 (Poor).

Without the caps, a day with a few hours of rain could still rate Good, because the dry hours outweigh the wet ones. In the preview, 55% of days with 1–5 mm of daylight rain did.

**Classes and colours**

| Score | Class | Colour |
|---|---|---|
| 80–100 | Great | dark green |
| 60–79 | Good | light green |
| 40–59 | Fair | yellow |
| 20–39 | Poor | orange |
| 0–19 | Bad | red |

**Calendar colour.** A day, week or month cell is coloured by the **chance of good weather**: the share of past days in that period that rated Good or Great. This is the default *(proposed)*; the mean score is an alternative.
- The colour scale is continuous: red at 0%, yellow at 50%, green at 100%.
- Day cells use the pooling window; week and month cells use all their days.
- The palette also changes in lightness, and each cell shows its number on hover, so it stays readable with red–green colour blindness.

**Notes**
- The scale is **absolute**: most winter days rate Poor or Bad, because winter weather is worse for being outdoors. A season-relative colouring ("good for January") could be added later.
- Temperature is the air temperature. A "feels like" temperature (with humidity and wind) is a later option; ERA5 has the dew point needed.
- ERA5 has too many hours with light rain. The rain thresholds are calibrated against airport reports of rain by hour (§10) before release.

## 5. Definitions

| Term | Definition (default, configurable) |
|---|---|
| Chosen hours | the time of day the user picked; if none, the daylight hours of each date (sunrise to sunset) |
| Wet day | ≥ 1.0 mm in the 24 hours of the local calendar day |
| Rain during the chosen hours | ≥ 0.2 mm in at least one of those hours (to be calibrated against airport rain reports) |
| Thunder | ERA5 has no thunder variable. Use airport reports where available; otherwise a model proxy (ECMWF IFS lightning density from 2017, or convective precipitation) to be evaluated |
| Frost | daily minimum < 0 °C |
| Heat | maximum during the chosen hours ≥ 32 °C |
| Strong wind | gust ≥ 50 km/h during the chosen hours |

## 6. Odds

- A **chance** is the share of historical days (or hours) in the pooled set that met a condition.
- The **chance of good weather** (§4) is the share of historical days whose score for the chosen hours was Good or Great. Each day is scored as a whole, so the links between temperature, rain and wind are kept. Multiplying separate chances would be wrong because they are linked.
- **Percentiles** (10th, 50th, 90th) describe the range of temperatures.
- The detail panel also shows which factor most often lowered the score in the selected period (e.g. "cold in 70% of the Poor days").

## 7. Uncertainty

- Intervals are 95% **bootstrap intervals over years**: whole years are resampled, which keeps the day-to-day correlation inside a year.
- Every view shows the number of years behind it.
- With 30 years of data at Plovdiv, the typical 95% half-width of a wet-day chance is:
  - ±15 points for a single date;
  - ±7 points with ±3-day pooling, ±5 with ±7 days, ±3 with ±15 days.
- For temperature the same half-widths are ±1.6, ±1.1, ±0.9 and ±0.7 °C.
- The dashboard uses this to warn when a daily view is mostly noise.

## 8. Recurring patterns

A pattern is reported only if all of these hold:

1. **Baseline:** the pooled curve departs from a smooth seasonal baseline (least-squares fit of 3 annual harmonics).
2. **Significance:** the 95% bootstrap interval of the departure excludes zero for at least 5 consecutive days.
3. **Stability:** the departure points the same way in both halves of the record (split-sample check).
4. **Trend removed:** temperature patterns use detrended data, so warming does not create false patterns.

Patterns are shown as frequencies ("a warm spell in this fortnight in X% of years"), with the dates they usually occur.

At Plovdiv this test found no strong calendar patterns. The autumn patterns from local experience did not pass ([phase-0 check](../research/plovdiv-data-check.md), [early October by range of years](../research/early-october.md)). The few candidates are small, about 1 °C or 5 percentage points: a cooler 3–8 September, and in recent years a pause in the cooling around 15–25 October. Patterns are therefore a secondary feature, labelled as "slight tendencies" with their evidence.

## 9. Validation

The odds are checked by **cross-validation** ([#7](https://github.com/valentina98/weather-odds/issues/7)):
1. Each year is predicted only from the reference years before it, and scored against what happened.
2. A second variant also uses later years, as the owner suggested; it scores slightly better because later years share the target's climate.

Defaults that change the odds are chosen from the results:
- reference years;
- pooling window;
- trend adjustment;
- later, the scale's thresholds.

Results so far: [validation.md](../research/validation.md). The script is part of the repo and is re-run when data sources or defaults change.

## 10. Combining sources

- v1: gridded data with a simple station-based calibration:
  - temperature: monthly mean bias correction against the station (ERA5 at Plovdiv: +0.6 °C in winter, −0.4 °C in July);
  - rain: a per-month wet-day threshold chosen so ERA5's wet-day frequency matches the station's (GSOD 1973–1999, NIMH from 2022);
  - hourly rain: a threshold chosen so the share of rainy hours matches airport reports.
- Show station comparisons in the Data tab.
- Later: quantile mapping, CERRA, and more stations from the NIMH network.

## 11. Known limitations

- Gridded rain is an area average: it shows more frequent light rain and less intense heavy rain than a single point gets.
- Station records for Plovdiv have gaps and changes in reporting (see data sources).
- Patterns are probabilistic and shift with climate change. The tool shows how reliable each one has been, not that it will happen.
- Rain odds hardly change through the year at Plovdiv. The calendar cannot say much about which week will be wet, only how often it rains in that season ([validation](../research/validation.md)).
