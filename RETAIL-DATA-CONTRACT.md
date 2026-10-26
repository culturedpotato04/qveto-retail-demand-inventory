# Shared integration contract - retail project

Lead owner: Shree Pranav G. Implementation path: src/retail_pipeline.py; CLI: src/predict_retail.py.

## Data input and ownership

Gourav owns the source/quality review. Starting source is UCI Online Retail by Daqing Chen (2015), DOI:10.24432/C5BW33, CC BY 4.0. Source page https://archive.ics.uci.edu/dataset/352/online+retail . Workbook has transactions from December 2010 to December 2011. Raw archive/workbook remain local and immutable; never add them, customer identifiers or company documents to the shared Git history.

Derived daily CSV columns:

| Column | Contract |
| --- | --- |
| date | ISO calendar date, sorted/consecutive within product |
| product_id | StockCode string, one of the five training-selected SKUs |
| units | Nonnegative gross recorded sales units for that date/product |
| has_recorded_sale | Whether any eligible source sales line exists on that date |

Scope: UK, positive quantities/prices, non-cancelled invoices, nonempty descriptions, stock codes matching five digits plus optional letter. Exact duplicate lines are excluded as an explicit cleaning assumption; some may represent legitimate repeats, so Gourav must audit this decision. Negative/cancelled rows are excluded from gross demand, not treated as negative demand. Missing CustomerID is not grounds to discard a sale; identifiers are unused and absent from derived data.

Dates without eligible sale lines are zero **recorded sales**, not certified zero latent demand. Closure, missing extraction and stockouts cannot be distinguished. Last source day (9 December) is excluded because the day is partial; this boundary decision is documented, not inferred from forecast error. Selected products come only from pre-July training invoice coverage. No top-product choice uses validation/test sales.

## Forecast and evaluation

One day ahead with all actual observations through yesterday available. Lag 1/7/14 and rolling mean/std ending yesterday; known calendar fields only. No same-day quantity/price, CustomerID, or future target feature. Shared chronological boundaries: train through 30 June 2011; validation July-August; reserved test September-8 December. Same dates for every product/model after 28-day warm-up.

Candidate selection: validation MAE only, among naive, weekly-naive, seven-day mean and two fixed Random Forest configurations. Winner frozen before test scoring. Candidate trees refit on train+validation for test scoring. The separate latest inference artifact refits the frozen winner on all history **after** evaluation. It must not be used to claim holdout scores.

## Output contracts

- reports/retail/comparison.csv: split, model, rows, MAE, RMSE, WAPE_percent, bias_forecast_minus_actual.
- reports/retail/test-predictions.csv: date, product_id, actual_units and each candidate prediction; daily rolling evaluation.
- reports/retail/next-day-forecast.csv: date, product_id, forecast_units, model; historical as-of forecast, not a forecast for October 2026.
- models/retail-forecast.joblib: train+validation artifact for historical test cutoff.
- models/retail-forecast-latest.joblib: inference artifact fitted through the last historical data date. Only load trusted local artifacts.
- reports/retail/quality.json: data exclusions, source hash, training-selected catalog and missing-field limitations.

Varsha can call the prediction CLI or import forecast_next for the dashboard. Rayash reviews features/splits and per-product errors. Sanjai's inventory module should consume a forecast and separately supplied stock, lead time, service level, order minimum and pack size. Missing inputs must display "inventory inputs required", not invented replenishment advice. Any demo inputs must be clearly labeled scenario assumptions.
