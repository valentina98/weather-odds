# Vision

## Problem

When planning an outdoor gathering, a hike or a walk 1–3 months ahead, weather forecasts are useless (no skill beyond ~2 weeks), yet the date has to be chosen now. Locals know that some periods are usually better than others ("early October is often warm and sunny in Plovdiv"), but that knowledge is anecdotal and nobody can say how often it holds.

## What weather-odds does

For Plovdiv and a chosen timeframe and time of day, weather-odds answers: **"In past years, how often was the weather good for being outdoors on these days and hours?"**

- It rates past weather on **one outdoor-weather scale**, shown as a calendar coloured from **green (good) to red (bad)**. Cold, heat, rain, wind and thunder all lower the rating.
- Selecting a day, week or month shows the details: typical temperatures, the chance of rain, wind, heat, frost or snow, and what most often spoiled the weather.
- It shows **recurring patterns** with how reliable they have been. At Plovdiv these are few and small (see [early October](research/early-october.md)).

It is a **climatology tool, not a forecast.** It uses only past statistics, never current weather or forecasts, and never claims to know the weather on a specific day.

## Who it is for

- **Primary:** the owner, organising non-commercial friend gatherings, hikes, walks and other outdoor time in Plovdiv, Bulgaria.
- **Secondary:** other developers who clone the public repo and run it locally. v1 covers Plovdiv only; other cities (Sofia, Varna) may come later.

## Principles

1. **Honest uncertainty.** Every number comes with how many years it is based on and how noisy it is. The user can switch between month, week and day views and see when daily detail is just noise. Defaults are checked by predicting past years from other years ([validation](research/validation.md)).
2. **Precision over coverage.** Plovdiv first, with Bulgarian station data wherever it is more precise.
3. **Time-of-day aware.** The question is "will those hours be dry and comfortable?", not "what is the daily average?" Hourly data matters.
4. **Configurable and reproducible.** Thresholds of the scale, reference years, data sources and the default time of day live in a config file. Another developer can run it with one command and no API key.
5. **Free and open.** MIT-licensed code; non-commercial use of free data sources; no downloaded data committed to the repo.

## Non-goals (for now)

- Forecasts of any kind, including seasonal outlooks.
- Ratings per activity.
- Training our own forecasting model.
- Running weather stations or collecting live data ourselves.
- A hosted website: the tool runs locally.
