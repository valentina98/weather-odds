# weather-odds

Historical weather odds for planning time outdoors (gatherings, hikes, walks) in Plovdiv, 1–3 months ahead.

Pick a timeframe and, optionally, a time of day. weather-odds shows a calendar coloured from green (usually good weather for being outdoors) to red (usually bad), based on past years. Select a day, week or month to see typical temperatures, the chance of rain, wind, frost and what most often spoiled the weather. It is a climatology tool, not a forecast.

## Status

**v1 is in development** (the specification was signed off on 29.10.2026). Progress and next steps are in [`docs/STATUS.md`](docs/STATUS.md); the research and the specification are in [`docs/`](docs/README.md); the work is planned in the [v1 milestone](https://github.com/valentina98/weather-odds/milestone/1). Code licence: [MIT](LICENSE).

Highlights from the first data check for Plovdiv ([details](docs/research/plovdiv-data-check.md)):

- The autumn patterns locals describe (late-September rain, a warm early October, a cold turn in late October) are not calendar patterns in 30–66 years of data. What people notice is the steep normal decline: the chance of a dry day of at least 18 °C drops from 68% in early October to 49% in late October.
- ERA5 reanalysis matches the Plovdiv station's temperatures closely but has too many wet days, so rain needs calibrating against station data.
- A single date's odds from 30 years are noisy (±15 percentage points for rain); pooling a week brings that to ±7.
- Early October does not warm up after late September, in any source or range of years, including the last 10 years ([details](docs/research/early-october.md)).
- Predicting each past year from other years shows that 30-year temperature statistics run about 1 °C cold because of warming, unless adjusted for the trend ([details](docs/research/validation.md)).
- Of all free sources, the Plovdiv station's own hourly temperatures are the most precise; ERA5 is the best grid for rain; CERRA is not more precise here ([details](docs/research/all-sources.md)).

## Data

The tool will download data on demand and never ship it. Sources and their licences are listed in [`docs/research/data-sources.md`](docs/research/data-sources.md) and [`docs/research/licensing.md`](docs/research/licensing.md). The free Open-Meteo API is for non-commercial use only.

## Development

Needs [uv](https://docs.astral.sh/uv/). From a clone:

```bash
uv sync
```

```bash
uv run pytest
```

```bash
uv run weather-odds config
```

The last command checks `config.yaml` in the current folder (or the built-in defaults if there is none) and prints the settings in effect. To change a default, copy [`config.example.yaml`](config.example.yaml) to `config.yaml` and edit it.

To download the data for the configured location into the cache (`.cache/` by default):

```bash
uv run weather-odds prefetch
```

It downloads only what is missing, plus the current year, which keeps growing. `--sources` limits it to some sources and `--refresh` downloads everything again. The dashboard follows in the [v1 milestone](https://github.com/valentina98/weather-odds/milestone/1).
