# Licensing and "commercial use"

## The owner's use is non-commercial

The tool will be used to plan friend gatherings, hikes, walks and other outdoor activities. Nothing is paid by anyone. The code will be public on GitHub and is not sold.

Open-Meteo's free tier (our main candidate source) is limited to non-commercial use and defines that by reference to Creative Commons: *"not primarily intended for or directed towards commercial advantage or monetary compensation."* The test is the purpose of the use, not who the user is. The owner's use clearly qualifies.

## Three rules that follow

1. **The person running the tool is the data user, not the repo.** The repo contains no data and makes no requests by itself. If someone clones it to plan paid events, that is their commercial use and they need a paid Open-Meteo plan or a different source. The README must say this, and the API key and server address must be configurable.
2. **Code licence and data licence are separate.** The code gets an open-source licence (MIT proposed, see [#2](https://github.com/valentina98/weather-odds/issues/2)). Each data source keeps its own licence.
3. **Never commit downloaded data.** The tool downloads on demand and caches locally in a git-ignored folder. Derived charts in the docs carry attribution.

## Per source

| Source | Licence | Fine for the owner? | Notes for other users |
|---|---|---|---|
| Open-Meteo API (free tier) | Service: non-commercial, < 10,000 calls/day. Data: CC BY 4.0 | Yes | Commercial users need a paid key (~€29/month) or self-hosting |
| Open-Meteo AWS open data | CC BY 4.0 (attribution) | Yes | Fine for any use with attribution |
| Copernicus CDS (ERA5, CERRA, C3S) | CC BY 4.0 since 2 July 2025 | Yes | Fine for any use with attribution |
| NASA POWER | Public | Yes | Fine |
| NOAA GSOD | US public data; WMO Resolution 40 note for non-US stations | Yes | Check the WMO note before commercial use |
| Iowa Environmental Mesonet | Free | Yes | Be gentle with request volume |
| Meteostat | CC BY-NC 4.0 (most pages) | Yes | Not for commercial use |
| NIMH open data | Free public access; terms not stated | Yes (personal use) | Ask NIMH before any redistribution |
| E-OBS | Non-commercial research and education only | Unclear (event planning is not research) | Not used |

## Attribution text to show in the app

> Weather data: Open-Meteo.com (CC BY 4.0), Copernicus Climate Change Service ERA5 / CERRA (CC BY 4.0), NOAA NCEI, NASA POWER, Iowa Environmental Mesonet, NIMH Bulgaria (info.meteo.bg/openData), Meteostat.

Only the sources actually used for a given chart need to be listed.

## Sources

- [Open-Meteo terms](https://open-meteo.com/en/terms), [pricing](https://open-meteo.com/en/pricing)
- [Creative Commons NonCommercial interpretation](https://wiki.creativecommons.org/NonCommercial_interpretation)
- [Copernicus licence change to CC BY](https://forum.ecmwf.int/t/cc-by-licence-to-replace-licence-to-use-copernicus-products-on-02-july-2025/13464)
- [Meteostat licence](https://dev.meteostat.net/license), [Meteostat support](https://meteostat.net/en/support)
- [E-OBS product licence](https://ads.atmosphere.copernicus.eu/licences/licence-to-use-E-OBS-products)

This is a practical summary, not legal advice.
