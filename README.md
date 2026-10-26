# Qveto Group 4 - Demand Forecasting & Inventory Optimization

Main implementation: **real retail product-level forecasting**, started by Pranav as lead on 26 October 2026 after Gourav confirmed Project 1. Working completion date is **6 November**, based on Gourav's understanding; exact official cutoff/review slot remains unverified. Internal freeze: 5 November.

## Run the lead contribution

Python 3.12 recommended. From this project directory:

```powershell
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\.venv\Scripts\python.exe' src/download_retail.py
& '.\.venv\Scripts\python.exe' src/retail_pipeline.py
& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v
& '.\.venv\Scripts\python.exe' src/predict_retail.py
& '.\.venv\Scripts\python.exe' src/report_retail.py
```

The downloaded workbook is about 24 MB and raw data/dependencies need additional disk space. Existing raw files are preserved by the downloader. Internet is needed for the first source/dependency download, then the pipeline runs locally. Do not load untrusted joblib/pickle model files.

## Ready artifacts

- [Lead results and plots](reports/retail/LEAD-REPORT.md)
- [Integration contracts and provenance](RETAIL-DATA-CONTRACT.md)
- reports/retail/comparison.csv and per-product-errors.csv
- reports/retail/test-predictions.csv
- reports/retail/next-day-forecast.csv and cli-forecast.csv
- models/retail-forecast.joblib (historical evaluation cutoff)
- models/retail-forecast-latest.joblib (latest historical refit)
- data/processed/retail-daily.csv and retail-features.csv
- tests/test_retail.py and tests/test_pipeline.py

## What Pranav's implementation does

Audits the actual workbook, constructs five daily product series selected from training invoices only, builds past-only features, compares three baselines with two Random Forest configurations on fixed time windows, selects the winner on validation MAE, evaluates the reserved test, saves models and exposes a one-day prediction CLI for the dashboard owner. All nine current tests pass. CLI output matches saved forecasts; raw workbook hash is unchanged.

## Honest limits

The current retail model still has substantial test error: the validation-selected model's test WAPE is 68.64%, not an accuracy score. The source is historical UK online retail, not the team's live business data. No stock, supplier lead-time or stockout fields exist. Missing-date sales are labeled zero recorded sales, not known zero latent demand. All inventory demo inputs must be explicit assumptions, and real replenishment outcomes cannot be claimed without a backtest and actual inputs.

The generated next-day prediction is for 9 December 2011 from archived history, not a 2026 business forecast. Final dashboard, inventory policy integration, report/slides, team acceptance of assignments, shared GitHub remote and official submission remain team deliverables. Do not tune against the already inspected final test window.

## Sources

Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. DOI:10.24432/C5BW33. https://archive.ics.uci.edu/dataset/352/online+retail . Licence verified as CC BY 4.0 on 26 October 2026. Source workbook/raw archive stays local and excluded from Git; processed data does not retain customer IDs. See quality.json for actual null counts rather than relying on the source-page missing-value label.

## Earlier benchmark

The bike-rental experiment is preserved in README-BIKE-BENCHMARK.md, src/pipeline.py, notebooks/01-demand-analysis.ipynb and reports/RESULTS.md. Its earlier scores do not apply to this retail model. Run the retail commands above for the actual assigned project.
