# Cross-validation: how good are the historical odds?

_Run on 2026-10-29 with [`research/validate_odds.py`](../../research/validate_odds.py), [`validate_vs_station.py`](../../research/validate_vs_station.py) and [`validate_scale.py`](../../research/validate_scale.py) for issue [#7](https://github.com/valentina98/weather-odds/issues/7). Numbers are in [validation.json](validation.json), [validation-station.json](validation-station.json) and [validation-scale.json](validation-scale.json)._

**Short answer:**
- Each year from 1996 to 2025 was predicted only from other years' statistics. **Temperature odds are informative, but the warming makes plain 30-year statistics about 1 °C too cold.** Shifting older years by the warming trend fixes most of that and lowers the error by about 0.1 °C.
- **Pooling ±7 days beats ±3 days** for both temperature and rain.
- **Rain odds barely beat a flat chance:** at Plovdiv the chance of a wet day hardly changes through the year.
- **Against what the station measured**, the station's own past years give the best-calibrated temperature ranges; ERA5's are too narrow ([below](#against-the-station)).
- **The calendar colour works:** the chance of a Good or Great day is 33% better than a flat chance and, with trend adjustment, well calibrated ([below](#the-outdoor-weather-scale)).

Defaults from this: the last 30 complete years, ±7-day pooling, and trend adjustment for temperature (agreed in [#6](https://github.com/valentina98/weather-odds/issues/6), with an on/off switch).

![Cross-validation](img/validation.png)

## How it was tested

As suggested in [#7](https://github.com/valentina98/weather-odds/issues/7): pretend one year's weather is unknown, predict it from other years, score the prediction against what happened, and repeat for every year. Here "predict" means only what the tool will show: the statistics of past years for that date. No current weather is used.

- **Target years:** 1996–2025, every day. Data: ERA5 at Plovdiv; station data replaces or checks it when reachable.
- **Training years:**
  - **"N years before":** only the N years before the target year (N = 10, 15, 20, 30, or all since 1961). This is exactly what the tool would have known at the time, so it is the honest test.
  - **"All other years":** also uses years after the target. This is the leave-one-year-out variant from #7. It looks slightly better because later years share the target year's warmer climate, which the real tool cannot know.
- **Pooling:** each date uses the training years' values from ±0, 3, 7 or 15 days around it.
- **Trend adjustment** (temperature only): each training year is shifted by the linear warming trend fitted to the training years. For example, a year 20 years before the target is shifted by 20 × the trend per year.
- **Scores** (lower is better):
  - **CRPS** for daily maximum temperature: the average error of the whole predicted distribution, in °C.
  - **Brier score** for the chance of a wet day (≥ 1 mm): the squared error of the predicted chance.
  - **Bias:** observed minus predicted mean.
  - **Coverage:** how often the day fell inside the predicted 10–90% range. 80% is right.

## Results

**Daily maximum temperature** (whole year; Sep–Nov behaves the same)

| Training years | Pooling | Trend-adjusted | CRPS | Bias | In 10–90% range |
|---|---|---|---|---|---|
| 30 before | ±3 days | no | 2.49 °C | +1.07 °C | 77% |
| 30 before | ±7 days | no | 2.47 °C | +1.07 °C | 77% |
| **30 before** | **±7 days** | **yes** | **2.38 °C** | **+0.32 °C** | **79%** |
| 30 before | ±15 days | yes | 2.37 °C | +0.32 °C | 81% |
| 10 before | ±7 days | no | 2.42 °C | +0.51 °C | 79% |
| 10 before | ±7 days | yes | 2.41 °C | +0.03 °C | 79% |
| All since 1961 | ±7 days | no | 2.53 °C | +1.27 °C | 75% |
| All since 1961 | ±7 days | yes | 2.41 °C | +0.75 °C | 77% |
| 30 before | ±0 days | no | 2.53 °C | +1.07 °C | 78% |
| All other years of 1996–2025 (uses later years) | ±7 days | no | 2.44 °C | 0.00 °C | 80% |

- **Trend adjustment** lowers the 30-year error by 0.10 °C (95% interval 0.06–0.14, at ±3 days) and removes most of the cold bias.
- **Without trend adjustment, fewer years are better:** the last 10 years beat the last 30. That matches the warming. With trend adjustment, 30 years are slightly better than 10, because more years mean less noise.
- **Pooling:** ±7 days is better than ±3 by a small but clear 0.016 °C (0.009–0.022). ±15 is better still, but it blurs real changes within a month.

**Chance of a wet day**

| Training years | Pooling | Brier score |
|---|---|---|
| 10 before | ±0 days | 0.193 |
| 30 before | ±0 days | 0.182 |
| 30 before | ±3 days | 0.1774 |
| **30 before** | **±7 days** | **0.1769** |
| 30 before | ±15 days | 0.1765 |
| All since 1961 | ±7 days | 0.1768 |

- **Pooling matters most:** a single date's chance from 10 or 30 years is clearly worse.
- Beyond ±7 days, and beyond 20–30 years, the gains are tiny.
- The default settings (30 years, ±3 days) are only **0.8% better than a flat chance** (Brier skill score 0.008). A flat chance means the same wet-day chance on every day of the year, from the same 30 years. At Plovdiv, the wet-day chance in ERA5 (±7 days, 1996–2025) varies only between 12% in late August and 35% in late May. Each year's rain falls on different days, so a calendar cannot say much about which week will be wet.
- **Reliability** (right panel): mid-range chances are right (predicted 22%, observed 22%), but the extremes are too extreme (predicted 13% → observed 20%; predicted 33% → observed 30%). Part of the calendar's variation in rain chance is noise. Wider pooling or a seasonal smoothing of the rain chance would help.

## Against the station

The checks above predict ERA5 from ERA5. What matters to a user is the weather at Plovdiv, so each year 2001–2025 was also predicted from the 30 years before it and scored against the station's measured daily maximum ([`validate_vs_station.py`](../../research/validate_vs_station.py), ±7 days):

| Predicted from | Trend-adjusted | Error (CRPS) | Bias | In the 10–90% range (80% is right) |
|---|---|---|---|---|
| **Station** | **yes** | 2.58 °C | **+0.15 °C** | **81%** |
| Station | no | 2.59 °C | +0.48 °C | 83% |
| ERA5 | yes | 2.56 °C | −0.10 °C | 76% |
| ERA5 | no | 2.62 °C | +0.79 °C | 75% |
| ERA5 corrected to the station (monthly) | yes | 2.57 °C | −0.40 °C | 77% |

- **The average errors are practically equal.** But ERA5's predicted ranges are too narrow against the station: only 76% of days fall inside the 10–90% range. The station's own years give 81%.
- ERA5 also warms faster than the station: +1.20 against +0.76 °C per decade since 1996 ([all sources](all-sources.md)). Trend adjustment with ERA5's trend therefore over-warms older years at the station.
- **For temperature, the station's own data is the better base for Plovdiv**, with the trend fitted to the station.

## The outdoor-weather scale

The calendar colours a date by the chance that a past day rated Good or Great ([methodology §4](../spec/methodology.md#4-outdoor-weather-scale)). Each year 1996–2025 was predicted from the 30 years before it (ERA5, daylight hours, ±7 days) and scored against which days of that year really were Good or Great ([`validate_scale.py`](../../research/validate_scale.py)):

| | Brier score | Flat chance | Skill over the flat chance |
|---|---|---|---|
| Not adjusted | 0.170 | 0.250 | 32% |
| **Trend-adjusted** | **0.167** | 0.250 | **33%** |

**Reliability, trend-adjusted:** does a predicted chance come true that often?

| Predicted | 5% | 15% | 25% | 35% | 45% | 55% | 67% | 73% | 86% |
|---|---|---|---|---|---|---|---|---|---|
| Observed | 5% | 17% | 24% | 37% | 52% | 49% | 67% | 72% | 84% |
| Days | 1,930 | 740 | 636 | 406 | 370 | 427 | 2,246 | 2,341 | 1,811 |

- **The colours carry real information:** a third better than a flat chance. Unlike rain alone, the scale follows the strong seasonal cycle of temperature.
- **With trend adjustment the chances are honest:** 67% means 67%.
**No pooling and more years** (trend-adjusted; [`validate_scale.py`](../../research/validate_scale.py)):

| Pooling | Training years | Skill over a flat chance | Highest predicted chances: predicted → observed |
|---|---|---|---|
| ±7 days | 30 before | **33%** | 86% → 84% |
| ±0 days | 30 before | 31% | 93% → 84%, 83% → 78% |
| ±0 days | all before (from 1966; 30–59 years) | 31% | 93% → 83%, 84% → 81% |

- Without pooling, a date's chance rests on only 30 past days, so the highest and lowest chances are too extreme.
- More years do not help: older years describe an older climate, even after trend adjustment. For temperature they are slightly worse ([table above](#results): all years before, trend-adjusted, 2.45 vs 2.44 °C at ±0); for rain slightly better (Brier 0.180 vs 0.182).

- **Without trend adjustment**, mid-season chances come out too low (predicted 24%, observed 32%; predicted 45%, observed 54%), because recent springs and autumns have more good days than older years suggest.

## What this means for the tool

1. **Pooling:** ±7 days scored best. The owner chose **no pooling (±0) as the default** (D26), and the user can choose up to ±15. Using all years instead of 30 does not make up for the missing pooling (table below).
2. **Default reference period: the last 30 complete years** (the owner's choice), with **trend adjustment for temperature** on by default (agreed in #6). Without it, the tool would show temperatures about 1 °C colder than the climate they are used in. Fit the trend to the data the temperatures come from: the station for Plovdiv.
3. **Rain should be shown as a broad chance**, not as a day-by-day signal. The colour of a week should not jump because of rain noise. This supports pooling and the monthly/weekly views for rain.
4. **Temperature from the station** (measured hourly from 1997) gives better-calibrated ranges than ERA5.
5. **The calendar colour is validated:** a third better than a flat chance, well calibrated with trend adjustment. Re-run when the station temperatures and thunder enter the scale.

## Reproduce

See [research/README.md](../../research/README.md).
