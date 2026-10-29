# Recurring calendar patterns ("singularities")

The idea behind weather-odds started from a local observation in Plovdiv: rain at the end of September, then a warm, sunny spell in early October, then a cold turn at the end of October. This page collects what is known about such patterns. The Plovdiv data check is in [plovdiv-data-check.md](plovdiv-data-check.md).

## What climatologists call them

A **singularity** (German *Witterungsregelfall*) is weather that tends to recur around the same calendar dates more often than chance would suggest. Well-known European examples:

| Name | Typical dates | Region | How reliable |
|---|---|---|---|
| Eisheiligen (Ice Saints) | mid-May | Central Europe | Often cited, weak |
| Schafskälte (sheep cold) | 4–20 June, peak ~11 June | Central Europe | Moderate |
| Altweibersommer (old wives' summer) | mid-September to early October | Central Europe | **MeteoSwiss: ~70–80% of years** in long-term statistics; the German weather service uses mid-September to early October. Several sources report it has become less regular recently. |
| Weihnachtstauwetter (Christmas thaw) | late December | Central Europe | Moderate |
| January thaw | ~20–25 January | North America | Debated. Godfrey, Wilks & Schultz (2002) asked "Is the January Thaw a Statistical Phantom?" |
| Indian summer | mid/late autumn | North America | Folk term; no strong statistical study found |

The Czech equivalent is *babí léto*. A 2026 Charles University thesis (Tkadlecová, "Singularities in Czechia during climate change") analysed the Indian summer, Christmas thaw and St. Medard period for 1976–2025 with daily station data, which is the same kind of analysis weather-odds would do.

## The Bulgarian folk pattern

Bulgarian sources disagree on the timing:

- **Bulgarian Wikipedia** describes *циганско (сиромашко) лято* as a warm, dry period at the **end of October and in November**, caused by stable anticyclones. Folk tradition starts it at **Dimitrovden (26 October)** and lets it last up to about 40 days.
- **Other Bulgarian sources** place it in **September to early October**, lasting from a few days to three weeks. This matches the owner's experience of a warm early October.
- The national news agency BTA uses *сиромашко лято* ("poor man's summer") for the period from Dimitrovden to Nikulden (6 December).

The Plovdiv data does not show a warm early October in any range of years. In the last 10–15 years it shows a non-significant pause in the cooling around 15–25 October, close to Dimitrovden ([early-october.md](early-october.md)).

Naming note: in English-language docs and UI we use **"late-autumn warm spell"** or the Bulgarian *сиромашко лято*, because the English translation of the other folk name can read as an ethnic slur.

## Scientific caution

- Many claimed singularities disappear under proper statistical testing; they can be **patterns seen in noise** from small samples.
- The main argument against them is the lack of a physical mechanism for a fixed calendar date. The better-supported ones are tied to circulation that is common at that time of year (for example a high-pressure system settling over Central Europe in late September).
- A pattern can be **real but unreliable**: "a warm spell happens in early October in 7 of 10 years, starting anywhere between 28 September and 12 October." A smoothed average curve hides this; a day-by-day frequency chart shows it.
- **Climate change shifts them.** Plovdiv has warmed noticeably since the 1980s, and the European literature reports that some singularities have become less regular.

## What this means for the tool

1. Show patterns as **frequencies** ("in X of the last N years"), never as promises.
2. Use **light smoothing** (a pooling window the user can change). Heavy 31-day smoothing, as Weather Spark uses, removes exactly the patterns users care about.
3. Show **uncertainty bands**, and only flag a pattern when it is clearly outside the noise and appears in both halves of the record (a split-sample check).
4. Prefer a **recent reference period** (about 30 years) so warming does not bias "typical" values.

## Sources

- [Singularity (climate), Wikipedia](https://en.wikipedia.org/wiki/Singularity_(climate))
- [Godfrey, Wilks & Schultz 2002, "Is the January Thaw a Statistical Phantom?"](https://www.atms.unca.edu/cgodfrey/pubs/Godfrey_etal2002.pdf)
- [MeteoSwiss blog on Altweibersommer](https://www.meteoschweiz.admin.ch/ueber-uns/meteoschweiz-blog/de/2023/10/herbst.html)
- [wetter.net on Altweibersommer](https://www.wetter.net/wetter-news/altweibersommer-8413.html)
- [Spektrum lexicon: Altweibersommer](https://www.spektrum.de/lexikon/geowissenschaften/altweibersommer/589)
- [Tkadlecová 2026, Charles University](https://dspace.cuni.cz/handle/20.500.11956/210306)
- [Bulgarian Wikipedia: Циганско лято](https://bg.wikipedia.org/wiki/%D0%A6%D0%B8%D0%B3%D0%B0%D0%BD%D1%81%D0%BA%D0%BE_%D0%BB%D1%8F%D1%82%D0%BE)
- [BTA on Dimitrovden](https://www.bta.bg/bg/news/bulgaria/75446-Predstoyashti-sabitiya-za-26-oktomvri)
