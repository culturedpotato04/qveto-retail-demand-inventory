# Demand Forecasting & Inventory Optimization

Selected by Pranav/Codex on 18 October 2026 as the proposed first project. Group 4 has not yet confirmed this choice. The second project remains undecided.

## Current delivery

Week 1/2 forecasting groundwork is implemented: provenance and immutable source files, data dictionary, automated quality checks, exploratory plots, chronological feature generation, naive and seasonal-naive baselines, validation-only baseline selection, holdout evaluation and prediction exports. An inventory scenario calculator is provided separately and requires explicit user assumptions.

The benchmark uses real UCI daily bike-rental counts, not retail SKU sales. It exercises the forecasting workflow without inventing stock levels or lead times. Team/mentor acceptance of this domain adaptation is pending. No production inventory recommendation is made from rental data.

## Setup and run

Python 3.12 recommended. From this project directory:

```powershell
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\.venv\Scripts\python.exe' src/download_data.py
& '.\.venv\Scripts\python.exe' src/pipeline.py
& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

Open reports/RESULTS.md and notebooks/01-demand-analysis.ipynb after running. The notebook runs the actual pipeline and displays its generated figures. No Jupyter server is needed to run the Python scripts.

## Forecast contract

One day ahead at the start of date t, assuming actual demand through t-1 is available. Evaluation rolls forward daily, so each new day's observed demand can be used for the next prediction. This is not a fixed-origin multi-day forecast. Baselines use yesterday's demand and the same weekday last week. Features use only past targets plus calendar information available ahead of time. Contemporary weather, casual and registered counts are excluded: the latter two sum to the target.

After a 28-day feature warm-up, the first 60% of observations are training, the next 20% validation and the remainder test. Choose the baseline using validation MAE, then report its reserved test performance once. No trained advanced model or hyperparameter search is claimed in this phase.

## Inventory limits

`src/inventory.py` calculates a textbook scenario reorder point from explicit mean demand, daily standard deviation, constant lead time and service-level z score. It assumes independent daily demand and fixed lead time; those assumptions are not established by this dataset. For real use, obtain SKU-level stock, supplier constraints, lead-time observations and backtest inventory outcomes. A bike fleet is reusable, so retail replenishment formulas must not be applied to this rental benchmark as operational advice.

## Sources and attribution

Fanaee-T, H. (2013). Bike Sharing [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5W894. Dataset page: https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset . Current page specifies CC BY 4.0. Source readme also requests citation to Fanaee-T and Gama, *Event labeling combining ensemble detectors and background knowledge*, DOI:10.1007/s13748-013-0040-3. Preserve that attribution when redistributing.

Raw archive and downloaded files are under data/raw/. Reports/raw-manifest.json records hashes. No credentials or private internship documents belong in the project repository. Dashboard/API, advanced model comparison, inventory backtest, final slides and official submission remain later work. Local files are not GitHub pushes or team commit-day compliance.
