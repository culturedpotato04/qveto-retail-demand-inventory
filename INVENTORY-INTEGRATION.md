# Inventory integration reference - 26 October 2026

Implemented by Pranav/Codex on the lead branch. This is a starting reference for Sanjai's proposed policy task and Varsha's dashboard integration, not their contribution or acknowledgement.

## Run

After generating the retail daily history and forecasts using README.md:

```powershell
& '.\.venv\Scripts\python.exe' src/plan_inventory.py
& '.\.venv\Scripts\python.exe' src/build_review.py
& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

Open reports/retail/review.html in a browser. It is self-contained, works offline and has a product filter. It is a read-only integration review, not the final Streamlit application. To refresh its data, rerun the commands after updating the input artifacts. No model is retrained by these two scripts.

## What the policy means

The UCI source has no observed inventory, lead times or supplier constraints. Every stock/on-order/backorder/lead-time/pack input in config/inventory-demo.json is explicitly invented. The snapshot is dated 8 December 2011 to align with the archived history. No fields imply real current stock.

Demand mean and sample standard deviation come from the 28 consecutive recorded-sales days ending at the configured snapshot, excluding later records. The one-day ML forecast is shown alongside but is not repeated across the supplier lead time. Missing/duplicate history dates, incomplete product coverage, missing stock inputs and invalid nonnegative values fail validation.

Illustrative continuous-review (s,S) policy:

- Safety stock = z x daily standard deviation x sqrt(lead days).
- Reorder point s = daily mean x lead days + safety stock.
- Inventory position = stock + on-order - backorders; negative position is allowed.
- Target S = mean x (lead days + extra cycle coverage) + z x standard deviation x sqrt(lead days + extra cycle coverage).
- At position <= s, order the positive gap to S, respecting minimum order and rounding up to the next whole pack. Otherwise order zero. With zero demand and no backorders, order zero.

Extra cycle coverage is not a review frequency. This assumes continuous review, constant lead time and independent stationary daily demand with a normal approximation. z=1.645 is an assumed normal quantile, not evidence of achieved service. No costs, constraints on maximum storage, correlated demand or variable lead-time risks are modeled. No simulation/backtest or realized business savings is claimed. Sanjai should review these assumptions, test alternative policies using a separate evaluation design, and obtain verified operational inputs before real recommendations.

## Integration contract

plan_inventory.py --history daily.csv --config scenario.json --output plan.csv writes one row per supplied SKU. It requires an exact match between history SKUs and scenario product IDs. Forecast outputs are kept separate and joined only in the review page; the page rejects mismatched products or dates.

Output includes demand basis, as_of, mean/std, every assumed policy input, safety stock, reorder point, position, trigger, target, suggested whole-unit order and assumption note. scenario_only remains true in every output row. Inputs are in units and calendar days; z is dimensionless. Forecasts/orders do not contain customer identifiers.

## Evidence

All 14 tests pass, including hand-calculated policy arithmetic, equality at the trigger, pack/minimum rounding, zero demand, negative inventory position, invalid inputs, duplicate/gapped history and future-data exclusion. Review page loaded in a browser; selecting product 85099B showed one row, returning to All showed five. Forecast metrics were read from the frozen results and not changed. Dashboard/report/slides ownership and team acceptance remain pending.
