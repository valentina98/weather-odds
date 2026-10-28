# Data sources

What historical weather data we can use, what each source really contains for Plovdiv, and the trade-offs.
Everything marked "tested" was downloaded and checked from a cloud session on 2026-10-28.
Numbers comparing sources against each other are in [plovdiv-data-check.md](plovdiv-data-check.md).

## Summary

- **No single source is complete for Plovdiv.** Station measurements are precise but patchy, especially for rain. Gridded model data (reanalysis) is complete and covers any point, including mountain trails, but it is smoothed over 9–25 km.
- **Measured rain at Plovdiv exists only for 1973–1999 (amounts) and from 2022 (NIMH).** From 2000 to 2021 we only have "rain was observed" flags from airport and synoptic reports, not amounts.
- **ERA5 is the backbone.** It is complete hourly from 1940 to a few days ago, and Open-Meteo publishes it on AWS without a key or rate limit. At Plovdiv its height-corrected daily maximum matches the station within 0.1 °C on average, but it has about 40% too many wet days, so rain needs calibrating.
- **Bulgarian precision:** NIMH's open-data portal is the best source of measured daily rain (166 stations), but only from January 2022. CERRA (5.5 km European reanalysis, 1985–mid 2021) is the most precise gridded option but needs either the rate-limited Open-Meteo API or a Copernicus key.

## Gridded data (any location, complete, modelled)

| Source | Resolution | Period | Access | Licence | Status |
|---|---|---|---|---|---|
| **ERA5** via Open-Meteo AWS open data (`s3://openmeteo/data/copernicus_era5/`) | 0.25° (~25 km), hourly | 1940 → ~5 days ago | No key, no limit. Files in Open-Meteo's `.om` format, read with the `omfiles` Python package; one location-year reads in about a second. | CC BY 4.0 | ✅ Tested. Variables: temperature, precipitation, snowfall, wind gusts, wind components, cloud cover, radiation, dew point, pressure. |
| **ERA5-Land** via the same bucket | 0.1° (~9 km), hourly | 1950 → recent | Same as above | CC BY 4.0 | ✅ Tested, but the bucket only holds temperature, dew point, snow depth and soil variables (no precipitation). **At Plovdiv its daily maximum is 2–3 °C too cool in summer**, even after height correction; plain ERA5 is better there. |
| **Open-Meteo Historical API** | ERA5, ERA5-Land, CERRA, ECMWF IFS (9 km, from 2017) | 1940 → ~5 days ago | No key. Free tier: non-commercial, < 10,000 calls/day per network address. | Data CC BY 4.0 | ⚠️ Works, but from cloud sessions the shared address is usually over the daily limit. On a personal computer it works normally. Applies an elevation correction to temperature (90 m terrain model). |
| **CERRA** (Copernicus European Regional Reanalysis) | 5.5 km, hourly | 1984/85 → mid 2021 on Open-Meteo; the Copernicus version continues | Open-Meteo API, or Copernicus CDS with a free account and API key | CC BY 4.0 | ⚠️ Not tested (API limit; no CDS key yet). Not in the Open-Meteo AWS bucket. |
| **Copernicus CDS** (ERA5 point time series, CERRA, seasonal forecasts) | as above | as above | Free account + API key (`CDSAPI_KEY`), licence accepted once per dataset on the website, request queue | CC BY 4.0 (since July 2025) | Reachable; not used yet (needs the key). |
| **NASA POWER** | ~0.5° (~50 km), daily (hourly from 2001) | 1981 → recent | No key, simple JSON API | Public | ✅ Tested. Precipitation is MERRA-2 corrected with observations. Too coarse for the Plovdiv basin or mountains. |
| **E-OBS** (gridded station measurements) | 0.1°, daily | 1950 → recent | CDS key or large files from the ECA&D site | **Non-commercial research and education only** | Not used. No hourly data; licence is a poor fit for an event-planning tool. |

## Station measurements (one point each)

All for Plovdiv synoptic station **WMO 15625** unless stated otherwise.

| Source | What it has for Plovdiv | Gaps and problems | Licence | Status |
|---|---|---|---|---|
| **NOAA GSOD** (Global Summary of the Day) | Daily max/min temperature from 1959; **measured daily precipitation 1973–1999**; daily flags for rain, snow, thunder, fog | Missing years: 1960–64, 1968–72, 1996. **No precipitation amounts after 2000** (reported as "no data"). The rain flag counts jump in 1997 and the thunder flag is zero 2015–2018, so the flags are not consistent over time. | US public data (WMO Resolution 40 note for non-US stations) | ✅ Tested |
| **Meteostat** (bulk data) | Daily temperature 1997 → now; hourly temperature, wind, humidity, pressure from 1939 | **No measured precipitation.** Recent precipitation and weather codes are filled from DWD MOSMIX forecasts, so they must not be used as observations. | CC BY-NC 4.0 on most pages; licence page says CC BY 4.0 for aggregated data | ✅ Tested |
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

1. **Default data path for end users:** Open-Meteo Historical API. It needs no key, has CERRA and ERA5-Land, and each user's own computer has its own daily quota.
2. **Fallback / bulk path without limits:** ERA5 from the Open-Meteo AWS bucket. Useful for development in the cloud and for long series.
3. **Station layer for Bulgaria:** combine NIMH (rain amounts from 2022), GSOD (rain amounts 1973–1999, temperature) and airport reports (rain occurrence by hour from ~2000) to *check and correct* the gridded data, rather than as the primary input.
4. **Optional precision layer:** CERRA via the Copernicus CDS, once a key is available.
5. **Never commit downloaded data.** Each user's tool downloads and caches it locally.
