# Data sources

What historical weather data we can use, what each source really contains for Plovdiv, and the trade-offs.
Everything marked "tested" was downloaded and checked from a cloud session on 2026-10-28; ECMWF IFS and CERRA were added on 2026-10-29. **How each source compares with the Plovdiv measurements: [all-sources.md](all-sources.md).**
Numbers comparing sources against each other are in [plovdiv-data-check.md](plovdiv-data-check.md).

## Summary

- **No single source is complete for Plovdiv.** Station measurements are precise but patchy, especially for rain. Gridded model data (reanalysis) is complete and covers any point, including mountain trails, but it is smoothed over 9–25 km.
- **Measured rain at Plovdiv exists only for 1973–1999 (amounts) and from 2022 (NIMH).** From 2000 to 2021 we only have "rain was observed" flags from airport and synoptic reports, not amounts.
- **ERA5 is the backbone.** It is complete hourly from 1940 to a few days ago, and Open-Meteo publishes it on AWS without a key or rate limit. At Plovdiv its height-corrected daily maximum matches the station within 0.1 °C on average, but it has more wet days than the station (39% more in 1973–1999, 8% more in 2022–2025), so rain needs calibrating.
- **Bulgarian precision:** the Plovdiv station's own hourly temperatures (Meteostat/NOAA ISD, measured, from 1997) are the most precise temperature source. NIMH's open-data portal is the best source of measured daily rain (166 stations), but only from January 2022. CERRA (5.5 km) was tested and is not more precise here: similar to ERA5 for temperature, much too wet.

## Gridded data (any location, complete, modelled)

| Source | Resolution | Period | Access | Licence | Status |
|---|---|---|---|---|---|
| **ERA5** via Open-Meteo AWS open data (`s3://openmeteo/data/copernicus_era5/`) | 0.25° (~25 km), hourly | 1940 → ~5 days ago | No key, no limit. Files in Open-Meteo's `.om` format, read with the `omfiles` Python package; one location-year reads in about a second. Wind is stored in m/s (the API converts to km/h). | CC BY 4.0 | ✅ Tested. Variables: temperature, precipitation, snowfall, wind gusts, wind components, cloud cover, radiation, dew point, pressure. |
| **ERA5-Land** via the same bucket | 0.1° (~9 km), hourly | 1950 → recent | Same as above | CC BY 4.0 | ✅ Tested, but the bucket only holds temperature, dew point, snow depth and soil variables (no precipitation). **At Plovdiv its daily maximum is 2–3 °C too cool in summer**, even after height correction; plain ERA5 is better there. |
| **ECMWF IFS** (operational model archive) via the same bucket (`ecmwf_ifs`) | ~9 km (O1280 reduced Gaussian grid), hourly | 2017 → today | Same as above; the grid is stored as one flat axis of 6.6 million points | CC BY 4.0 | ✅ Tested (2026-10-29). Temperature, precipitation, gusts, plus CAPE and **lightning density** (a possible thunder proxy). Only 9 years, so useful as a check of recent years, not as the backbone. At Plovdiv its early-October curve matches ERA5 within about 0.5 °C. |
| ERA5 ensemble via the same bucket | 0.5°, 3-hourly | 1940 → recent | Same as above | CC BY 4.0 | Not used: coarser than ERA5. Its spread could later show ERA5's own uncertainty. |
| **Open-Meteo Historical API** | ERA5, ERA5-Land, CERRA, ECMWF IFS (9 km, from 2017) | 1940 → ~5 days ago | No key. Free tier: non-commercial, < 10,000 calls/day per network address. | Data CC BY 4.0 | ✅ Tested (2026-10-29). The daily limit was reached again after a few large requests. **Its default "ERA5 seamless" product uses ERA5-Land temperatures, 3 °C too cold in summer at Plovdiv**; ask for plain ERA5 (`models=era5`, still to be checked). Applies an elevation correction to temperature (90 m terrain model). |
| **CERRA** (Copernicus European Regional Reanalysis) | 5.5 km, hourly | 1984/85 → mid 2021 on Open-Meteo; to July 2026 on Copernicus | Open-Meteo API, or Copernicus CDS (key + dataset licence; only whole-Europe fields) | CC BY 4.0 | ✅ Tested through the Open-Meteo API, 1985–2021. Daily maximum: about as good as ERA5 (mean absolute difference 1.34 vs 1.24 °C). Rain: 35% wet days against the station's 17%. **Not used.** |
| **Copernicus CDS** (ERA5 point time series, CERRA) | as above | as above | Free account + API key (`CDSAPI_KEY`), licence accepted once per dataset on the website, request queue | CC BY 4.0 (since July 2025) | ✅ Key works from the `weather-odds` environment (2026-10-29). Not needed: CERRA is not used, and ERA5 is available without a key. |
| **NASA POWER** | ~0.5° (~50 km), daily (hourly from 2001) | 1981 → recent | No key, simple JSON API | Public | ✅ Tested. Precipitation is MERRA-2 corrected with observations. Too coarse for the Plovdiv basin or mountains. |
| **E-OBS** (gridded station measurements) | 0.1°, daily | 1950 → recent | CDS key or large files from the ECA&D site | **Non-commercial research and education only** | Not used. No hourly data; licence is a poor fit for an event-planning tool. |

## Station measurements (one point each)

All for Plovdiv synoptic station **WMO 15625** unless stated otherwise.

| Source | What it has for Plovdiv | Gaps and problems | Licence | Status |
|---|---|---|---|---|
| **NOAA GSOD** (Global Summary of the Day) | Daily max/min temperature from 1959; **measured daily precipitation 1973–1999**; daily flags for rain, snow, thunder, fog | Missing years: 1960–64, 1968–72, 1996. **No precipitation amounts after 2000** (reported as "no data"). The rain flag counts jump in 1997 and the thunder flag is zero 2015–2018, so the flags are not consistent over time. | US public data (WMO Resolution 40 note for non-US stations) | ✅ Tested |
| **Meteostat** (bulk data) | Daily temperature 1997 → now; **hourly temperature measured almost every hour from 1997** (3-hourly 1980–1995, 1996 missing; 99.9% from NOAA ISD and airport reports); hourly wind and humidity | **No measured precipitation or gusts.** Precipitation, gusts and weather codes are filled from DWD MOSMIX forecasts, so they must not be used as observations. | CC BY-NC 4.0 on most pages; licence page says CC BY 4.0 for aggregated data | ✅ Tested; the hourly temperatures are the proposed temperature source (D34) |
| **Iowa Environmental Mesonet** – airport reports (METAR) for Plovdiv airport **LBPD** | Reports every 30 min from about 2000 (sparser before), with present-weather codes: rain, showers, drizzle, thunder, snow | Airport only; no rain amounts; airport opening hours limit night coverage in some years | Free | ✅ Tested |
| **NIMH open data** ([info.meteo.bg/openData](https://info.meteo.bg/openData/)) | **Measured daily precipitation at 166 Bulgarian stations** (Plovdiv = station 46011), monthly CSV files; daily snow cover; monthly temperature means and extremes | **Only from January 2022.** Labelled experimental and unverified. A blank cell means either "no precipitation" or "no report"; the files do not say which. Temperature only as monthly values. | Free public access; licence terms not stated on the portal | ✅ Tested |
| **NIMH paid data** (written request to the institute) | Complete official records for any station | Price on request; cannot be redistributed in a public repo | Per contract | Not requested |
| **NOAA GHCN-Daily** | Nothing: only 4 Bulgarian stations (Vidin, Varna, Sofia, Kardzhali) | – | Public | ✅ Checked |
| **Ogimet** (SYNOP archive) | Would have daily summaries | Returns 403 to automated requests | – | ❌ Not usable |
| **stringmeteo.com** | Amateur archive of Bulgarian synoptic data from 1999 | Terms unclear; would need scraping | Unknown | Not used |

## Services we will not build on

| Service | Why not |
|---|---|
| Weather Spark | Website only, no data access. Useful as a sanity check: it shows smoothed daily climatology for Plovdiv from MERRA-2. |
| Visual Crossing | Needs a key; free tier is 1,000 records/day, which is about 3 years of daily data for one place. |
| meteoblue history / seasonal | Paid API. |
| Open-Meteo paid key | About €29/month; unnecessary for a non-commercial hobby tool. |
| ERA5 on Google Cloud (ARCO) or the ECMWF AWS mirror | Organised as whole-globe time slices; reading one point's 35 years means downloading huge volumes. The Open-Meteo bucket solves the same problem efficiently. |

## Implications for the design

1. **Default data path for end users:** free sources only: the Plovdiv station (Meteostat/NOAA) for temperature, ERA5 from Open-Meteo (AWS bucket or API with plain ERA5) for rain and wind, airport reports for thunder. No key needed.
2. **Fallback / bulk path without limits:** ERA5 from the Open-Meteo AWS bucket. Useful for development in the cloud and for long series.
3. **Station layer for Bulgaria:** combine NIMH (rain amounts from 2022), GSOD (rain amounts 1973–1999, temperature) and airport reports (rain occurrence by hour from ~2000) to *check and correct* the gridded data, rather than as the primary input.
4. **No CERRA:** tested and not more precise at Plovdiv ([all sources](all-sources.md)).
5. **Never commit downloaded data.** Each user's tool downloads and caches it locally.
