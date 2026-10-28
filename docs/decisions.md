# Decision log

Decisions made so far, newest last. "Accepted" means the owner confirmed it; "Proposed" means it is a recommendation waiting for the owner (usually with an open issue).

| ID | Date | Decision | Status | Why / source |
|---|---|---|---|---|
| D1 | 2026-10-28 | weather-odds is a **climatology tool** (historical odds), not a forecast. | Accepted | Forecast skill beyond ~2 weeks is low; see [forecast-providers](research/forecast-providers.md). |
| D2 | 2026-10-28 | **Purpose: planning outdoor activities** – friend gatherings, hikes, walks. | Accepted | Owner. |
| D3 | 2026-10-28 | **Use is non-commercial.** Nothing is paid by anyone. Free tiers (Open-Meteo, Meteostat) are fine. | Accepted | Owner; see [licensing](research/licensing.md). |
| D4 | 2026-10-28 | **Any location can be configured, but only Plovdiv is tested** at first. Data is downloaded only for selected locations. | Accepted | Owner. |
| D5 | 2026-10-28 | **Prefer precision over coverage**: use Bulgarian data where it is more precise, even if other countries are less well supported. | Accepted | Owner. |
| D6 | 2026-10-28 | **Granularity is selectable**: month, week, day and hour (time window). | Accepted | Owner. Daily views must show their noise (pooling window + intervals). |
| D7 | 2026-10-28 | **Public GitHub repo, configurable, runnable by other developers, with an analysis dashboard.** | Accepted | Owner. |
| D8 | 2026-10-28 | **Docs and spec before code.** No implementation until the owner closes the specification phase. Questions go to GitHub issues assigned to the owner. | Accepted | Owner. |
| D9 | 2026-10-28 | **Never commit downloaded weather data**; download on demand, cache locally. | Accepted | Licences differ per source. |
| D10 | 2026-10-28 | Repo name: **weather-odds**. | Accepted | Owner created it. |
| D11 | 2026-10-28 | **ERA5 is the gridded backbone** (temperature from ERA5, not ERA5-Land, at Plovdiv); station data (NOAA GSOD, NIMH, airport reports) is used to check and calibrate it. | Proposed | Only ERA5 is complete in time and space, and it matched the Plovdiv station best; see [data-sources](research/data-sources.md) and [Plovdiv data check](research/plovdiv-data-check.md). |
| D12 | 2026-10-28 | **Default data path needs no key**: Open-Meteo API, with Open-Meteo's AWS open data as a fallback. Copernicus CDS (CERRA, seasonal) is optional with a key. | Proposed | Open-Meteo's free daily limit is often exhausted from shared cloud addresses; the AWS bucket has no limit. |
| D13 | 2026-10-28 | Default **reference period: the last 30 complete years** (now 1996–2025). | Proposed | Plovdiv warmed noticeably since the 1980s; see the data check. Open issue. |
| D14 | 2026-10-28 | "Good day" odds are computed as the **joint frequency** of historical days meeting all conditions, not by multiplying separate chances. | Proposed | Rain, temperature and wind are correlated; multiplying would be wrong. |
| D15 | 2026-10-28 | English docs use **"late-autumn warm spell" / *сиромашко лято*** rather than the other Bulgarian folk name. | Proposed | The literal English translation can read as an ethnic slur in a public repo. |
| D16 | 2026-10-28 | Code licence: **MIT** (proposed). | Proposed | Open issue. |
