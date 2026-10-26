# Pranav's lead contribution - delivery index

Project: Demand Forecasting & Inventory Optimization Using Machine Learning, confirmed by Gourav's direct message on 26 October. Pranav confirms he is team lead. Working deadline 6 November; exact official review/submission cutoff pending confirmation.

## Implemented now

- Real UCI Online Retail pipeline for five training-selected products.
- Provenance/hash, actual missing-value and cancellation/return/duplicate audit.
- Past-only features, shared chronological windows and explicit zero-recorded-sales policy.
- Three baselines plus two Random Forest configurations; validation-selected winner frozen before test scoring.
- Per-product metrics, historical predictions and charts; remaining errors and limitations visible.
- Evaluation and latest-refit model artifacts; reusable one-day inference function and CLI.
- Nine passing tests; CLI equivalence and raw source integrity verified.

## Read/use

- [Lead report](reports/retail/LEAD-REPORT.md)
- [Shared data/model contract](RETAIL-DATA-CONTRACT.md)
- [Setup](README.md)

Forecasting code is started and reviewable. Full project is not complete: data-policy cross-review, inventory-policy integration, Streamlit dashboard, report/slides and official submission remain. Model errors are substantial and inventory inputs are absent. An earlier bike-rental learning benchmark is preserved separately; its scores must not be used for this retail project.

Only local Git work is recorded. No remote repository, team message, cloud publication or official submission has been performed in this task. Every team member should implement and commit their own module; do not present the proposed work split as accepted or completed by them.
