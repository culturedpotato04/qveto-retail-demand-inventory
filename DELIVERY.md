# Week 1/2 delivery - 18 October 2026

Project: Demand Forecasting & Inventory Optimization. Chosen by Pranav/Codex for a proposal; Group 4 confirmation pending. Public rental-data benchmark adaptation is explicit, not a claim that retail/inventory data was supplied.

| Required early deliverable | Artifact |
| --- | --- |
| Data provenance / dictionary / limitations | DATA-DICTIONARY.md and source Readme.txt |
| Original source preservation and hashes | data/raw/ and reports/raw-manifest.json |
| Quality report | reports/results.json quality section and reports/RESULTS.md |
| Audited/interim data | data/interim/daily-audited.csv |
| EDA notebook and figures | notebooks/01-demand-analysis.ipynb and reports/figures/eda.png |
| Past-only lag and rolling features | src/pipeline.py and data/processed/features-and-baselines.csv |
| Chronological split and horizon contract | README.md and reports/results.json |
| Naive / seasonal-naive baselines | src/pipeline.py and reports/baseline-comparison.csv |
| Reserved test predictions and errors | reports/test-predictions.csv and reports/figures/holdout.png |
| Repeatable environment and checks | requirements.txt and tests/test_pipeline.py |

Validation: five meaningful tests pass; source audit passes on 731 daily observations; 28 warm-up rows are excluded from modeling. No source imputation/deletion required. Naive wins on validation MAE. Its 141-day test MAE is 894.30 rentals/day, RMSE 1301.79 and WAPE 15.26%. These are baseline scores, not an advanced model improvement.

Inventory scenario formula is implemented and tested in src/inventory.py. Stock/supplier data, the retail-domain adaptation, advanced models, dashboard/API, final presentation, team repo/branches and official progress submission remain pending. No team decision, pushed commits or attendance is fabricated.
