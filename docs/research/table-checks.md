# The Plovdiv tables checked against the measurements

_Milestone 3 ([#17](https://github.com/valentina98/weather-odds/issues/17)). Run on 05.11.2026 with `uv run weather-odds check` on the data downloaded that day; the command rebuilds the tables and prints this report._

**Short answer**
- **The table reproduces [all-sources.md](all-sources.md).** ERA5 against the station, wet days, the wet-day thresholds, rainy hours against the airport and thunder days by month all come out as in the research.
- **One difference in how days are summed.** The research added up ERA5's rain as if each value belonged to the hour starting at its time stamp; Open-Meteo stamps rain at the end of its hour. The table moves each value to its own hour, so its local days start one hour later. Summed the research's way, every number matches; the table's own numbers differ by at most 0.5 percentage points and 0.1 mm (shown next to them).
- **The station's gaps are filled** with ERA5's shape between readings (gaps up to 12 hours, and the 3-hourly years before 1997) and with ERA5 corrected to the station from nearby years (longer gaps up to 31 days). Both pass their hidden-data tests.
- **1996 stays out (D43).** Filling a whole year from ERA5 fails its test: the filled year's day-to-day range of maxima is 11% narrower than the station's, the same weakness that made the station the temperature source (D34).
- **Thunder: 2015–2018 have no thunder reports.** The airport's reports and NOAA's daily summaries exist for those years, but neither mentions thunder on any day. The research counted those years as thunder-free. The table leaves them out, so thunder is about a third more frequent than all-sources.md says (June: 33% of days, not 24%).

## How the table is built

| Column | Source | Fill |
|---|---|---|
| temperature | the station's hourly readings (Meteostat; measured values only) | gaps up to 12 hours: ERA5's shape between the readings (the station-minus-ERA5 difference interpolated across the gap); longer gaps up to 31 days: ERA5 plus the typical difference of that month and hour in the 3 years either side; longer gaps (1996, 1968–1972, before 1965) stay empty |
| precipitation, wind gusts | ERA5 | none needed |
| wet day | ERA5's daily rain, against a threshold per month that gives ERA5 the station's wet-day frequency in 1973–1999 (NOAA GSOD) | – |
| rain seen, thunder by hour | airport reports, only in years in which they report rain or thunder | – |
| thunder by day | airport reports where they report thunder, otherwise NOAA's daily flag | – |
| sunrise, sunset, daylight | computed from the coordinates (within 2 minutes of the `astral` library) | – |

Of the hours from 1960 to October 2026, 330,631 are measured, 152,498 rebuilt between readings (mostly the 3-hourly years before 1997), 2,027 filled from ERA5 corrected to the station, and 100,685 left empty (no station data nearby).

### Which years report rain and thunder

The airport's reports go back to 1965, but carry weather codes only from 2003 (and not in 2004–2009). A source's year counts for thunder only if thunder is reported on at least 1% of its days (Plovdiv: 3–15%), and for rain if rain is seen on at least 10% of its days (Plovdiv: 25–45%). That gives:

| | Years used |
|---|---|
| Thunder from the airport (days with reports in at least 16 hours) | 2003, 2011–2014, 2019–2026 |
| Thunder from NOAA's daily flag (the other days) | 1965–1967, 1973–1995, 1997–2012 |
| No thunder data | before 1965, 1968–1972, 1996, 2015–2018 |
| Rain seen at the airport | 2003, 2010–2026 |

Thunder days fall from about 50 a year in 2019–2021 to 13 in 2025 at the airport, and further in NOAA's flag (6 in 2025). This may be a change in reporting rather than in the weather; it is checked with the thunder placement in the next part of the milestone.

## Results

### Filling the station's gaps (hidden data)

| Check | Result | Expected | |
|---|---|---|---|
| Short gaps (1-12 h hidden, 7200 hours, 1997-2025) | error 1.19 °C, bias +0.04 °C | error ≤ 1.5 °C, bias within ±0.2 °C | pass |
| Longer gaps (1, 7, 31 days hidden, 1086 whole days) | error 1.40 °C, bias -0.03 °C; daily maximum bias -0.15 °C | error ≤ 1.5 °C, bias within ±0.2 °C, daily maximum within ±0.3 °C | pass |
| 3-hourly readings rebuilt (9064 days of 1997-2025 thinned to every 3 hours) | daily maximum error 0.42 °C, bias -0.04 °C; minimum bias +0.16 °C; daylight score error 1.0 points, same class 95% | maximum error ≤ 0.5 °C, bias within ±0.2 °C, score error ≤ 3 points | pass |
| Whole year without station data (1997 hidden; the option for 1996, D43) | daily maximum error 1.24 °C, bias -0.20 °C; day-to-day range 89% of the station's | error ≤ 1.3 °C, bias within ±0.3 °C, range 95%-105% | **fail**: not used |

### Against the station (all-sources.md)

| Check | Result | Expected | |
|---|---|---|---|
| ERA5 daily maximum minus the station's, 1991-2021 (10737 days) | bias -0.0 °C, difference 1.24 °C, correlation 0.987 | +0.0 °C, 1.24 °C, 0.987 | pass |
| ERA5 daily maximum minus the station's, 2017-2025 (3143 days) | bias +0.6 °C, difference 1.20 °C, correlation 0.988 | +0.6 °C, 1.20 °C, 0.988 | pass |
| Table daily maximum (hourly readings) minus the station's daily maximum, 1997-2025 (10444 days) | bias -0.15 °C, difference 0.23 °C | slightly negative: the true maximum falls between the hourly readings | info |
| Wet days (≥ 1 mm), 1985-1999, station = NOAA GSOD (5062 days) | station 16.6%, ERA5 23.0% (agrees on 84%); with the table's hours ERA5 22.9% (84%) | 16.6%, 23.0% (84%) | pass |
| Wet days (≥ 1 mm), 2022-2025, station = NIMH (1461 days) | station 20.3%, ERA5 22.2% (agrees on 81%); with the table's hours ERA5 22.5% (80%) | 20.3%, 22.0% (81%) | pass |
| Calibrated wet days in the table, 1973-1999 | 18.9%, station 18.7% (they agree on 86% of days) | near the station | pass |
| Calibrated wet days in the table, 1985-1999 | 17.7%, station 16.6% (they agree on 86% of days) | for information | info |
| Wet-day thresholds by month (mm), calibrated on NOAA GSOD 1973-1999 | 1.4 1.7 2.1 2.0 1.9 1.9 1.7 2.2 1.7 1.2 1.6 1.4; with the table's hours 1.5 1.7 2.1 1.9 1.9 1.9 1.7 2.1 1.7 1.2 1.7 1.4 | 1.4 1.7 2.1 2.0 1.9 1.9 1.7 2.2 1.7 1.2 1.6 1.4 | pass |
| The same thresholds calibrated on NIMH 2022-2025 (4 years, for information) | 0.8 2.5 1.4 1.6 1.1 1.7 0.9 0.4 0.7 1.2 1.4 1.1; with the table's hours 0.9 2.3 1.2 1.5 1.0 1.7 0.9 0.4 0.9 1.2 1.5 0.6 | 0.8 2.5 1.4 1.6 1.1 1.7 0.9 0.4 0.7 1.2 1.4 1.0 | info |
| Rainy hours, airport reports vs ERA5 ≥ 0.2 mm, 2012-2021 (83092 hours) | airport 9.1%, ERA5 9.3%; ERA5 rains in 53% of the airport's rainy hours, 48% of ERA5's rainy hours are dry at the airport | 9.1%, 9.3%; 53%, 48% | pass |
| Rainy hours, airport reports vs ERA5 ≥ 0.2 mm, 2017-2025 (78866 hours) | airport 9.2%, ERA5 8.8%; ERA5 rains in 54% of the airport's rainy hours, 43% of ERA5's rainy hours are dry at the airport | 9.2%, 8.8%; 54%, 43% | pass |
| Days with thunder by month, airport 2012-2025, every day with reports (as in all-sources.md) | 1% 1% 1% 6% 17% 24% 15% 13% 5% 2% 1% 0% | 1% 0% 1% 6% 17% 24% 14% 13% 5% 2% 1% 0% | pass |
| Days with thunder by month in the table: only years with thunder reports (2012-2014, 2019-2025) | 1% 0% 2% 9% 23% 33% 20% 18% 7% 2% 1% 0% | higher than above: 2015-2018 have no thunder reports and no longer count as thunder-free | info |

## Choosing the fills

The thresholds between the fills come from the hidden-data tests (1997–2025, gaps hidden where the station measured):

| Hidden gap | Straight line between readings | ERA5's shape between readings | ERA5 + typical difference of nearby years | ERA5 as it is |
|---|---|---|---|---|
| 1 hour | **0.65 °C** | 0.91 °C | 1.30 °C | 1.41 °C |
| 3 hours | 0.89 °C | 1.02 °C | 1.37 °C | 1.52 °C |
| 6 hours | 1.39 °C | **1.15 °C** | 1.36 °C | 1.54 °C |
| 12 hours | 2.64 °C | **1.32 °C** | 1.33 °C | 1.48 °C |
| 24 hours | 4.05 °C | 1.50 °C | **1.31 °C** | 1.49 °C |
| 7 days | – | 1.76 °C | **1.32 °C** | 1.48 °C |

_Mean absolute error of the filled hours. The station reports whole degrees since 2001, which alone gives an error of about 0.25 °C._

- **ERA5's shape** is used up to 12 hours: beyond that, ERA5 with the typical difference is as good or better.
- **A straight line** is slightly better for gaps of 1–3 hours, but it misses the afternoon peak: rebuilt from 3-hourly readings, its daily maxima are 0.37 °C too low, against 0.04 °C with ERA5's shape. One method for all short gaps keeps it simple; the difference concerns about 1% of the hours since 1997.
- **Nearby years only** (3 either side): ERA5's difference from the station drifts by more than 1 °C between the 1990s and the 2020s ([all-sources.md](all-sources.md)).

## Reproduce

```bash
uv run weather-odds prefetch
```

```bash
uv run weather-odds check
```
