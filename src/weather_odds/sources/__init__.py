"""Data adapters, one module per source (milestone 2, #16).

Each adapter downloads its raw files into the cache, only what is missing (the
current year's files are always refreshed), and parses them into a tidy table:

- hourly tables are indexed by the start of each hour, in the location's time zone;
- daily tables are indexed by the local calendar date.

Columns come from one vocabulary, in fixed units:

    temperature      air temperature, deg C
    tmax, tmin       daily extremes, deg C
    precipitation    mm in the hour or the day
    rain_seen        rain, drizzle, showers or thunder reported by an observer
    thunder          thunder reported
    snow_seen        snow reported
    reports          number of airport reports in the hour

A value that was not measured is missing (NaN or <NA>), never guessed. Filling
gaps and combining sources is the next step (milestone 3, #17).
"""

from weather_odds.sources import airport, gsod, meteostat, nimh
from weather_odds.sources.base import Source

SOURCES: dict[str, Source] = {s.name: s for s in (meteostat.SOURCE, airport.SOURCE, gsod.SOURCE, nimh.SOURCE)}

__all__ = ["SOURCES", "Source"]
