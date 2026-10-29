# Forecasts for 1–3 months ahead

Can anyone forecast the weather 1–3 months ahead, and is it worth showing next to the historical odds?

## Short answer

Yes, several providers publish seasonal forecasts, but their skill over Bulgaria is modest. They can tilt the odds (for example "55% chance this November is warmer than normal" instead of the climatological 33%), but they cannot tell you the weather on a specific day weeks ahead. Temperature is predicted better than precipitation, and skill drops sharply after the first month.

For weather-odds this means: **the historical climatology is the core product**; a seasonal "tilt" is an optional extra that must be shown as a probability shift, never as a daily forecast.

## Providers

| Provider | Range | What it gives | Access | Notes |
|---|---|---|---|---|
| **Copernicus C3S** multi-system seasonal forecast (ECMWF, UK Met Office, Météo-France, DWD, CMCC, and others) | 6 months | Monthly probabilities for below / near / above normal (terciles), reference period 1993–2016 | Free charts; data through the Copernicus CDS (key needed) | Updated on the 10th of each month. The most credible free source. |
| **ECMWF SEAS5 + EC46** through the Open-Meteo Seasonal API | EC46: 46 days at weekly resolution; SEAS5: about 7 months | Ensemble values at 36 km | Free, no key (non-commercial) | ECMWF announced extending SEAS5 to 13 months once per quarter. |
| **NIMH Bulgaria** (meteo.bg) | Monthly and seasonal | Probabilistic outlook synthesised from several world centres | Free, website; full version in Bulgarian only | Updated on the 27th–30th of each month. |
| **meteoblue** Seasonal Anomalies | 6 months | Monthly temperature and precipitation anomalies, multi-model super-ensemble | Paid API | Regional (100 km scale), not point forecasts. |
| **AccuWeather** 90-day | 90 days | Day-by-day values | Website | **Avoid.** No published verification; independent checks found 25–45 day forecasts often wrong by up to 10 °F and missing half the rain days. |

## What the research says about skill

- Seasonal systems add value over climatology and persistence in the Mediterranean region, but **temperature anomalies are predicted better than precipitation**, and skill decreases after the first month for nearly every score (Calì Quaglia et al., 2021, *Climate Dynamics*).
- Outside the tropics, seasonal skill is "markedly lower" (C3S evaluations).
- For weeks 3–4, ECMWF heat-wave forecasts were generally not better than a statistical forecast over Europe, **except in southeastern Europe** (NHESS 2025). Prolonged heat waves keep some predictability at 3 weeks.
- No independent study supports day-specific forecasts beyond ~2 weeks.

## Proposed use in weather-odds

- **v1:** none, or a link out to the NIMH and C3S outlooks.
- **Later (optional):** show the C3S or SEAS5 monthly tercile probabilities for the selected months next to the historical odds, clearly labelled. Store each month's outlook so we can later check how often it was right for Plovdiv.

This is an open question for the owner: [#7](https://github.com/valentina98/weather-odds/issues/7).

## Sources

- [Copernicus seasonal forecasts](https://climate.copernicus.eu/seasonal-forecasts), [C3S product descriptions](https://confluence.ecmwf.int/display/CKB/C3S+seasonal+forecast+product+descriptions)
- [Open-Meteo seasonal forecasts](https://openmeteo.substack.com/p/seasonal-weather-forecasts), [ECMWF SEAS5 extension](https://forum.ecmwf.int/t/seasonal-forecast-seas-model-extension/14477)
- [NIMH seasonal forecast](https://storm.cfd.meteo.bg/meteo7/en/forecasts/seasonal)
- [meteoblue seasonal forecast](https://www.meteoblue.com/en/blog/article/show/33845_Seasonal+climate+forecast+)
- [Gizmodo on AccuWeather 90-day](https://gizmodo.com/accuweathers-90-day-forecast-tool-is-misleading-as-hell-1771625577)
- [Calì Quaglia et al. 2021, Climate Dynamics](https://link.springer.com/article/10.1007/s00382-021-05895-6)
- [Extended-range heat-wave skill over Europe, NHESS 2025](https://nhess.copernicus.org/articles/25/1865/2025/)
