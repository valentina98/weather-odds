# Filling the gaps in the station's temperatures

_Milestone 3 ([#17](https://github.com/valentina98/weather-odds/issues/17)), 2026-11-05. Decision D46. Reproduce with `uv run weather-odds check` after `uv run weather-odds prefetch`._

The Plovdiv station (WMO 15625) measured the temperature every hour from 1997. Before that it measured every 3 hours (8 readings a day), and some years have no readings at all (1961–1964, 1968–1972, 1996). The tool keeps every measurement and fills only the gaps. Each fill was tested by hiding hours the station did measure, filling them, and comparing with the measurement. Following the [gap plan](../development-plan.md#filling-the-data-gaps), a fill is used only if:
- it beats the simplest alternative;
- its mean error (bias) stays within ±0.3 °C.

## What was compared

Three ways of filling the hours between readings, on 1997–2025:

| Hidden hours | Straight line between readings | ERA5's hourly shape, pinned to the readings | **The station's own mean daily curve, pinned to the readings** |
|---|---|---|---|
| Gaps of 1–6 hours: error | 1.16 °C | 1.10 °C | **0.90 °C** |
| Every hour except 8 a day (as before 1997): error | 0.78 °C | 0.98 °C | **0.73 °C** |
| Same, bias of the daily maximum | −0.37 °C | −0.03 °C | −0.20 °C |
| Same, bias of the daily minimum | +0.46 °C | +0.15 °C | +0.31 °C |

ERA5's hourly shape fits the station worse than a straight line: ERA5's day-to-night range is too narrow at Plovdiv ([all sources](all-sources.md)). The gap plan proposed ERA5's shape for the 3-hourly years. The test rules it out, and the station's own curve is used instead.

"Error" is the mean absolute error of the hidden hours; "bias" is the mean difference (filled minus measured).

## What the tool does (D46)

| Gap | Fill | Source label |
|---|---|---|
| up to 6 hours (including the hours between 3-hourly readings) | the station's mean daily curve for the month (from complete days), pinned to the readings on both sides | `station curve` |
| 6 hours to 7 days | ERA5, plus the station-minus-ERA5 difference for the same month and hour of day in the 5 years around the gap (ERA5 drifts against the station over the decades) | `era5 corrected` |
| longer | none: those hours stay missing, so years without station data are left out (D43) | – |

## The checks

`weather-odds check` hides hours in the years the station measured hourly, at random, and fills them the way the tool does:

| Fill | Hours | Error | Bias | Baseline | Baseline error | Baseline bias | Passed |
|---|---|---|---|---|---|---|---|
| gaps of 1-6 hours | 10,324 | 0.91 | +0.01 | straight line | 1.16 | +0.02 | yes |
| gaps of 1-7 days | 23,415 | 1.36 | -0.12 | plain ERA5 | 1.49 | +0.39 | yes |
| 3-hourly years rebuilt | 80,994 | 0.73 | +0.00 | straight line | 0.78 | -0.02 | yes |

- **3-hourly years rebuilt:** every other year of 1997–2025 is thinned to 8 readings a day; the others provide the daily curve. Daily maximum bias −0.19 °C (8 readings alone −0.39); daily minimum bias +0.30 °C (8 readings alone +0.51).

## What this means

- **The default period is measured almost entirely.** In 1997–2025, 98.8% of hours are measured, 1.1% follow the station's curve and 0.1% come from corrected ERA5. A typical year has about 30 filled hours (at most 491, in 2001).
- **Years before 1997 are two-thirds filled.** In 1973–1995, 33% of hours are measured and 65% follow the station's curve. Their hours are close (0.73 °C), but the daily maximum comes out about 0.2 °C too low and the minimum about 0.3 °C too high. This matters only when the user picks reference years before 1997, and the detail panel should say so.
- **Long gaps are rare and less precise** (1.36 °C an hour), but corrected ERA5 removes plain ERA5's +0.39 °C bias.
