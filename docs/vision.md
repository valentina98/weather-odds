# Vision

## Problem

When planning an outdoor gathering, a hike or a walk 1–3 months ahead, weather forecasts are useless (no skill beyond ~2 weeks), yet the date has to be chosen now. Locals know that some periods are usually better than others ("early October is often warm and sunny in Plovdiv"), but that knowledge is anecdotal and nobody can say how often it holds.

## What weather-odds does

For a chosen place and time window, weather-odds answers: **"In past years, how often was the weather good for my activity on these days and hours?"**

- It turns decades of historical weather into **odds**: the chance of rain during the event hours, typical temperature ranges, the chance of strong wind, heat, frost or snow.
- It shows **recurring patterns** (such as a late-September rainy spell or an early-October warm spell) with how reliable they are.
- It helps **pick the best dates** within the next 1–3 months by ranking days or weeks.

It is a **climatology tool, not a forecast.** It never claims to know what the weather will be on a specific day.

## Who it is for

- **Primary:** the owner, organising non-commercial friend gatherings, hikes, walks and other outdoor activities around Plovdiv, Bulgaria.
- **Secondary:** other developers who clone the public repo and run it for their own places. They configure it; no hosted service is planned at this stage (see open questions).

## Principles

1. **Honest uncertainty.** Every number comes with how many years it is based on and how noisy it is. The user can switch between month, week, day and hour views and see when daily detail is just noise.
2. **Precision over coverage.** Where Bulgarian data is more precise than global data, use it, even if that makes other countries less well supported.
3. **Event-centred.** The question is "will the event hours be dry and comfortable?", not "what is the daily average?" Hourly data matters.
4. **Configurable and reproducible.** Thresholds (what counts as rain, too hot, too windy), reference period, data sources and event hours live in a config file. Another developer can run it with one command and no API key.
5. **Free and open.** Non-commercial use of free data sources; no downloaded data committed to the repo.

## Non-goals (for now)

- Day-specific forecasts beyond the normal 1–2 week weather forecast.
- Training our own forecasting model.
- Running weather stations or collecting live data ourselves.
- A hosted public website (open question).
