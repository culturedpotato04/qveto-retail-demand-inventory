# Data dictionary and provenance

Official archive: https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip . Source page and licence verified 18 October 2026. UCI DOI:10.24432/C5W894, Hadi Fanaee-T (2013), CC BY 4.0. Use day.csv (731 rows), not the hourly file. Preserve source Readme.txt and citation.

| Fields | Meaning | Use |
| --- | --- | --- |
| dteday | Local calendar date, daily aggregation; source does not encode UTC offsets | Sorted time key |
| cnt | Total daily rentals | Target; historical values only enter features |
| casual, registered | Daily counts of unregistered/registered users; sum to cnt | Quality check only; exclude from predictors |
| instant | Source record index | Preserve, exclude from predictors |
| season, yr, mnth, holiday, weekday, workingday | Source calendar/season labels | Preserved; derive weekday/month directly from date for initial features |
| weathersit, temp, atemp, hum, windspeed | Realized weather and normalized measurements | Preserve, exclude from prospective forecasts without actual forecast-weather inputs |
| lag_1, lag_7 | cnt at t-1/t-7 | Available under rolling daily forecast contract |
| rolling_mean_7, rolling_std_7, rolling_mean_28 | Statistics over target history ending t-1; std uses sample ddof=1 | Past-only features |
| split | Sequential 60/20/20 after warm-up | Train, validation, reserved test |

Source page and bundled readme differ in some season wording and normalization descriptions. We do not use those fields for the initial baselines. No gaps or nulls are silently filled; the pipeline stops if quality checks fail. Stock, supplier lead times, promotions, SKU/store IDs and stockout labels are unavailable and must not be fabricated.
