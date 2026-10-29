# weather-odds

Historical weather odds for planning outdoor activities (gatherings, hikes, walks) 1–3 months ahead.

Pick a place and a date range, and weather-odds tells you what the weather has *usually* been like on those days in past years: typical temperatures, the chance of rain during your event hours, wind, frost, and recurring seasonal tendencies. It is a climatology tool, not a forecast.

## Status

**Definition phase. No application code yet.** The research and the draft specification are in [`docs/`](docs/README.md); start with [`docs/STATUS.md`](docs/STATUS.md). Open questions are GitHub issues collected in [#12](https://github.com/valentina98/weather-odds/issues/12).

Highlights from the first data check for Plovdiv ([details](docs/research/plovdiv-data-check.md)):

- The autumn patterns locals describe (late-September rain, a warm early October, a cold turn in late October) are not calendar patterns in 30–66 years of data. What people notice is the steep normal decline: the chance of a dry day of at least 18 °C drops from 68% in early October to 49% in late October.
- ERA5 reanalysis matches the Plovdiv station's temperatures closely but has too many wet days, so rain needs calibrating against station data.
- A single date's odds from 30 years are noisy (±15 percentage points for rain); pooling a week brings that to ±7.

## Data

The tool will download data on demand and never ship it. Sources and their licences are listed in [`docs/research/data-sources.md`](docs/research/data-sources.md) and [`docs/research/licensing.md`](docs/research/licensing.md). The free Open-Meteo API is for non-commercial use only.
