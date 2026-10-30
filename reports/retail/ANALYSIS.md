# Retail analytical findings - 30 October 2026

Computed from the frozen 26 October model outputs; no test-based model changes.

## Data quality and interpretation
541,909 raw rows include 5,268 exact duplicates, 9,288 cancellations, 10,624 nonpositive-quantity rows and 2,517 nonpositive-price rows. Counts overlap and must not be added as mutually exclusive exclusions. Retain positive UK merchandise sales, exclude cancellations and final partial date, drop exact duplicates as an explicit assumption. Some identical rows may be legitimate repeat line entries. Customer ID has 135,080 missing values and is not used or retained. Missing descriptions are excluded by the preparation filter. 475,216 eligible gross-sales rows precede the five-product selection.

Only recorded gross sales are modeled, not net sales after returns or unconstrained demand. The five products are selected using training invoices only. There are 377 panel rows with no recorded sale; they become zero recorded units, but closures and stockouts cannot be distinguished. The sample cannot justify full-catalog or live-business claims.

## Demand patterns
Training-only weekday profiles avoid using test behavior for feature selection. Weekday differences are descriptive associations; trading hours and their causes are not established by this dataset. Zero days and occasional large orders create intermittent/bursty sales. Full-calendar profiles and plots are descriptive; no new model was fitted from them. One year of data is insufficient to establish repeatable annual seasonality.

## Evaluation and failure cases
Fixed chronological splits and past-only rolling features support a rolling one-day-ahead evaluation. Validation MAE selects Random Forest leaf size 10 before test scoring; train plus validation is then used for the evaluation refit. Test data remain reserved from model selection. The deployment demonstration is a separate all-history refit.

Selected test MAE 46.2864 units, RMSE 116.7474 units, WAPE 68.6412%, bias -8.3004 units. The strongest test baseline is seven-day mean with MAE 59.7804; relative MAE reduction is 22.5727%. This is not classification accuracy. RMSE far above MAE indicates severe large misses. The largest-error table and scatter expose underpredicted order bursts; monthly metrics quantify temporal variation without tuning to it. Unknown promotions, bulk purchases and stock availability prevent causal explanations. Product WAPE may be unstable for low-volume subsets. No confidence intervals or significance claim is made for serially dependent observations.

## Inventory policy and recommendations
Safety stock = z * daily standard deviation * sqrt(lead days). Reorder point = mean daily sales * lead days + safety stock. Position = on hand + on order - backorders. A continuous-review (s,S) trigger at or below the reorder point orders toward mean*(lead+extra coverage)+z*std*sqrt(lead+extra coverage), respecting pack size and minimum order.

All stock, lead time and service factors are user assumptions. This formula assumes stationary independent daily demand, fixed lead time and a normal approximation, which bursty sales may violate. Extra coverage is a cycle target, not a periodic review interval. A one-day ML prediction is never multiplied across supplier lead time. Demand standard deviation is a simple scenario proxy, not a calibrated forecast-error distribution. No measured stockout reduction, service-level guarantee, savings or cost optimum is established.

Before operational use, obtain stock snapshots, receipts, supplier lead-time distributions, prices/promotions and lost-sales indicators. Backtest feasible replenishment policies with holding/stockout/order costs and rolling-origin uncertainty calibration on a new untouched period. Extend SKU coverage and monitor drift, bias and exceptions before any automated purchasing. Current app/API are local research tools without production authentication or multi-user persistence.

## Sources and contribution
Chen, D. (2015), Online Retail, UCI Machine Learning Repository, DOI 10.24432/C5BW33, CC BY 4.0: https://archive.ics.uci.edu/dataset/352/online+retail . Raw workbook SHA-256: 43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d.
Qveto Project 1 brief and SOP are local reference sources; originals are preserved outside the public project repository. Pranav completed the implementation with AI assistance. No unreceived teammate work or independent review is claimed.
