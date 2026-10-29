# Methodology

How weather-odds turns historical data into odds and colours. Signed off on 2026-10-29 (D44), with the owner's answers (#4–#7, #14) and the [cross-validation](../research/validation.md).

The research scripts are working prototypes of most of these steps:
- [`research/analyze_plovdiv.py`](../../research/analyze_plovdiv.py): sources, patterns, noise.
- [`research/validate_odds.py`](../../research/validate_odds.py): cross-validation.
- [`research/preview_scale.py`](../../research/preview_scale.py): the outdoor-weather scale.

## 1. Data for Plovdiv

For Plovdiv the tool builds one **hourly** and one **daily** table in local time:

| Field | Unit | Main source |
|---|---|---|
| temperature | °C | **The station's hourly measurements** (WMO 15625 via Meteostat/NOAA ISD, from 1997). Missing hours are filled with ERA5 corrected to the station. 1996 has no station data at all and is left out (D43, [gap plan](../development-plan.md#filling-the-data-gaps)). ERA5's ranges are too narrow against the station, and its warming trend is steeper ([all sources](../research/all-sources.md)). |
| precipitation | mm | ERA5 (≈25 km), calibrated against station wet-day frequencies (§10). ERA5 is the best grid for rain here: CERRA (5.5 km) has twice as many wet days as the station. |
| snowfall, snow depth | mm water / m | ERA5 / ERA5-Land |
| wind gusts | km/h | ERA5 |
| cloud cover | % | ERA5 |
| thunder | yes/no | airport reports (LBPD) by hour, 2012–2014 and 2019–2025; NOAA's daily thunder flag for 1997–2011, which matches the airport where both exist. Thunder is reported on 24% of June days, and ERA5's rain misses half of the thunder hours, so rain cannot stand in for it. Both sources are empty in 2015–2018. How flagged days get their hours, and what to do about 2015–2018: [gap plan](../development-plan.md#filling-the-data-gaps). |
| sunrise, sunset | time | computed from coordinates |

**Data path.** The Open-Meteo API's default ERA5 product ("ERA5 seamless") uses ERA5-Land temperatures, which are 3 °C too cold in summer at Plovdiv. The tool reads plain ERA5: from the Open-Meteo AWS bucket, or from the API with `models=era5` (to be confirmed when the API's daily limit allows).

**Elevation correction.** Gridded temperature is for the grid cell's average height. It is shifted to Plovdiv's station elevation (179 m) with a lapse rate of 0.65 °C per 100 m. In winter, valley inversions in the Plovdiv basin break this rule; the station check measures how much.

## 2. Reference period

- **Default: the last 30 complete years** (currently 1996–2025, of which 29 have station data: 1996 is left out and the label says so), set in the config ([#6](https://github.com/valentina98/weather-odds/issues/6)).
- In the dashboard the user can **narrow it to a shorter range** within the configured period, e.g. the last 10 years.
- **Trend adjustment** for temperature ([#6](https://github.com/valentina98/weather-odds/issues/6)): each reference year's temperatures are shifted by the linear warming trend fitted to the reference years, up to the current year. The trend is fitted to the data the temperatures come from: the station for Plovdiv (+0.76 °C per decade since 1996; ERA5 shows +1.20). In the cross-validation, plain 30-year statistics predicted temperatures 1.07 °C too cold on average; trend adjustment cut that to 0.32 °C and lowered the error by 0.10 °C. It uses only the historical record, not current weather.
  - The user switches it **on or off** in the dashboard; the config sets the default (shipped default: on).
  - It is always visible: a label on the calendar ("temperatures adjusted to the 2026 climate"), and in the detail panel the fitted trend (°C per decade) and the shift applied to the oldest reference year.
- Pattern detection uses the full record after removing the long-term trend.

## 3. Day-of-year statistics and pooling

- Every date is mapped to a 365-day calendar (29 February is dropped).
- A daily statistic for date *d* uses all reference years and the days *d−w … d+w* (the "pooling window" *w*).
- **Default *w* = 0 days: no pooling**, the owner's choice (2026-10-29). Each date uses only the same date in the reference years. The user can raise it to 15. The cross-validation scored ±7 days better (scale skill over a flat chance 33% vs 31%; temperature error 2.38 vs 2.44 °C), and without pooling the extreme chances are too confident (93% came true 84% of the time). Using more years instead does not make up for it ([validation](../research/validation.md#the-outdoor-weather-scale)).
- Week and month views use all days of that week or month in the reference years directly (no extra pooling).

## 4. Outdoor-weather scale

*Agreed in [#5](https://github.com/valentina98/weather-odds/issues/5).* There are no activity profiles. One scale rates how good the weather was for being outdoors. A preview for Plovdiv is in [weather-scale.md](../research/weather-scale.md).

All numbers below are **defaults**. They are set in the config, and the user can change them in the dashboard for the session: comfort range, cold and heat limits, rain thresholds and caps, gust limits, class boundaries. **Each can differ by time of day** (night 0–6, morning 6–12, afternoon 12–18, evening 18–24), for example a comfort range starting at 15 °C in the evening. By default all four bands use the same values, and changing the chosen hours never changes a threshold (settings are independent, requirement N9); each hour is scored with its band's thresholds.

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

**Calendar colour.** The user picks what the colour of a day, week or month cell shows:

| Measure | What it answers | Example |
|---|---|---|
| **Chance of good weather** (default) | "How often was it good?" The share of past days in the period that rated Good or Great (60 or more). | 7 of 10 past days were Good or Great → 70%. |
| **Average score** | "How good was it typically?" The mean of the past days' scores. | Those days scored 85, 85, 80, 75, 70, 65, 62, 50, 30, 20 → 62. |

- The two can differ when a period is mixed. A week that is always mediocre (every day 55) and a week that is half great (90) and half bad (20) both average about 55. But their chance of good weather is 0% and 50%.
- For choosing a date, the chance of good weather is the more useful default: it says how likely it is that the day will be fine. The average score is the smoother option.
- The colour scale is continuous, from red (0) through yellow (50) to green (100), for both measures.
- Day cells use the pooling window; week and month cells use all their days.
- **Absolute or relative** (default absolute): absolute colours use the fixed 0–100 range above.
  - Relative colours stretch the range over the cells in the selected timeframe: the best cell is green and the worst red. This shows the best weeks of a winter timeframe.
  - The view is labelled "relative", and hovering always shows the absolute value.
- The palette also changes in lightness, and each cell shows its number on hover, so it stays readable with red–green colour blindness.

**Notes**
- With absolute colours (the default), most winter days rate Poor or Bad, because winter weather is worse for being outdoors. Relative colours (above) show the best of a winter timeframe.
- Temperature is the air temperature. A "feels like" temperature (with humidity and wind) is a later option; ERA5 has the dew point needed.
- ERA5 has too many hours with light rain. The rain thresholds are calibrated against airport reports of rain by hour (§10) before release.

## 5. Definitions

| Term | Definition (default, configurable) |
|---|---|
| Chosen hours | the time of day the user picked; if none, one daylight window for the whole timeframe: from the latest sunrise to the earliest sunset among its dates, rounded inward to whole hours (for 29.10.2026–29.01.2027: about 08:00–16:00) |
| Wet day | ≥ 1.0 mm in the 24 hours of the local calendar day |
| Rain during the chosen hours | ≥ 0.2 mm in at least one of those hours (to be calibrated against airport rain reports) |
| Thunder | thunder in an airport report within the hour; for 1997–2011, a day with NOAA's thunder flag, placed in its hours with convective signs (to be tested, see the [gap plan](../development-plan.md#filling-the-data-gaps)) |
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

- v1, measured against the Plovdiv station and airport ([all sources](../research/all-sources.md)):
  - **temperature:** the station's own hourly measurements; ERA5 corrected to the station (monthly mean difference over the years used) only fills gaps;
  - **wet days:** an ERA5 day counts as wet from a per-month threshold that matches the station's wet-day frequency in 1973–1999: 1.4 mm in January, about 2 mm in spring and summer, 1.2 mm in October. Against NIMH 2022–2025 the thresholds come out lower (about 1.1 mm); re-check as NIMH years accumulate;
  - **hourly rain:** ERA5 at ≥ 0.2 mm already rains as often as the airport reports (9.3% vs 9.1% of hours), so the scale's 0.2 mm threshold stays;
  - **thunder:** from the airport reports.
- Show station comparisons in the Data tab.
- Later: quantile mapping, and more stations from the NIMH network. CERRA was tested and is not used ([all sources](../research/all-sources.md)).

## 11. Known limitations

- Gridded rain is an area average: it shows more frequent light rain and less intense heavy rain than a single point gets.
- Station records for Plovdiv have gaps and changes in reporting (see data sources).
- Patterns are probabilistic and shift with climate change. The tool shows how reliable each one has been, not that it will happen.
- Rain odds hardly change through the year at Plovdiv. The calendar cannot say much about which week will be wet, only how often it rains in that season ([validation](../research/validation.md)).
