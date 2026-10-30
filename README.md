# Qveto Group 4 - Demand Forecasting & Inventory Optimization

## Final release - 30 October 2026

This section supersedes the dated starter status below. Completed by Shree Pranav G with AI assistance: forecasting pipeline, inventory policy, four-view Streamlit dashboard, validated FastAPI service, executed retail EDA notebook, failure analysis, final analytical report and editable eight-slide presentation. **17 tests passed on 30 October**, including UI and API flows. No unreceived teammate work or company acceptance is claimed.

After installing requirements and generating the retail pipeline outputs using the commands below:

```powershell
& '.\.venv\Scripts\python.exe' src/analyze_retail.py
& '.\.venv\Scripts\python.exe' -m streamlit run src/app.py --browser.gatherUsageStats false
# Optional API, in another terminal:
& '.\.venv\Scripts\python.exe' -m uvicorn api:app --app-dir src --host 127.0.0.1 --port 8000
```

Open the displayed localhost URL. Select a product, filter evaluation dates, generate the archived forecast, and edit stock/lead time/pack assumptions. Download filtered predictions or scenario JSON. API docs: http://127.0.0.1:8000/docs . Routes: GET /health, /products, /forecast/{product_id}?horizon=1; POST /inventory/scenario. Unknown products return 404; invalid horizons, negative/nonfinite numbers, fractional packs and extra scenario fields are rejected. API forecasts serve frozen archived inference; the dashboard runs the trusted local model. These are local research applications without production authentication or persistence.

- [Final report](reports/final/Final-Report.pdf)
- [Editable presentation](reports/final/Project-Presentation.pptx)
- [Executed retail notebook](notebooks/02-retail-analysis.ipynb)
- [Data quality, failure cases, inventory limits and recommendations](reports/retail/ANALYSIS.md)
- Product/time error tables: reports/retail/per-product-errors.csv, test-month-errors.csv, largest-errors.csv

Test MAE 46.29 units, RMSE 116.75, WAPE 68.64% error, bias -8.30. MAE is 22.57% lower than the strongest baseline (seven-day mean, 59.78). Rolling one-day evaluation uses actual preceding-day observations; it does not measure fixed-origin multi-day forecasts. No tuning on the inspected test window. The all-history deployment fit is distinct from the held-out evaluation fit. No stockout reduction, savings or service-level guarantee is established. See the report for operational data and new untouched-period validation still needed.

Raw data are downloaded/rebuilt using the commands below; processed retail CSVs are included in the release ZIP. Historical commit requirements cannot be recreated by this release. Repository upload, official sheet entry and company acceptance remain distinct states, with receipts outside the code repository.

## Dated starter notes - 26 October (superseded by final release above)

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
& '.\.venv\Scripts\python.exe' src/plan_inventory.py
& '.\.venv\Scripts\python.exe' src/build_review.py
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
- [Portable product-filter review page](reports/retail/review.html)
- [Inventory reference, formulas and integration contract](INVENTORY-INTEGRATION.md)
- config/inventory-demo.json and reports/retail/inventory-scenario.csv

## What Pranav's implementation does

Audits the actual workbook, constructs five daily product series selected from training invoices only, builds past-only features, compares three baselines with two Random Forest configurations on fixed time windows, selects the winner on validation MAE, evaluates the reserved test, saves models and exposes a one-day prediction CLI for the dashboard owner. All 14 current tests pass. CLI output matches saved forecasts; raw workbook hash is unchanged. A separate assumed-input inventory CLI and read-only HTML review connect the module outputs without retraining or repeating one-day predictions across a lead-time horizon.

## Honest limits

The current retail model still has substantial test error: the validation-selected model's test WAPE is 68.64%, not an accuracy score. The source is historical UK online retail, not the team's live business data. No stock, supplier lead-time or stockout fields exist. Missing-date sales are labeled zero recorded sales, not known zero latent demand. All inventory demo inputs must be explicit assumptions, and real replenishment outcomes cannot be claimed without a backtest and actual inputs.

The generated next-day prediction is for 9 December 2011 from archived history, not a 2026 business forecast. Inventory policy review/extension, final Streamlit dashboard, report/slides, team acceptance of assignments, shared GitHub remote and official submission remain team deliverables. The lead's HTML review is a working integration reference. Do not tune against the already inspected final test window.

## Sources

Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. DOI:10.24432/C5BW33. https://archive.ics.uci.edu/dataset/352/online+retail . Licence verified as CC BY 4.0 on 26 October 2026. Source workbook/raw archive stays local and excluded from Git; processed data does not retain customer IDs. See quality.json for actual null counts rather than relying on the source-page missing-value label.

## Earlier benchmark

The bike-rental experiment is preserved in README-BIKE-BENCHMARK.md, src/pipeline.py, notebooks/01-demand-analysis.ipynb and reports/RESULTS.md. Its earlier scores do not apply to this retail model. Run the retail commands above for the actual assigned project.
