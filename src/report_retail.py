"""Render reports solely from frozen retail evaluation artifacts; does not retrain."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/'reports/retail'


def main():
    result=json.loads((REPORTS/'results.json').read_text(encoding='utf-8'))
    quality=result['quality']
    scores=pd.read_csv(REPORTS/'comparison.csv')
    preds=pd.read_csv(REPORTS/'test-predictions.csv',parse_dates=['date'],dtype={'product_id':str})
    winner=result['winner_selected_on_validation_MAE']
    figure_dir=REPORTS/'figures'
    figure_dir.mkdir(exist_ok=True)
    aggregate=preds.groupby('date')[['actual_units',winner]].sum()
    test=scores[scores.split.eq('test')]
    fig,axes=plt.subplots(2,1,figsize=(11,8),layout='constrained')
    axes[0].plot(aggregate.index,aggregate.actual_units,label='Observed gross sales',color='#1f2937')
    axes[0].plot(aggregate.index,aggregate[winner],label='Selected Random Forest',color='#2563eb',alpha=.85)
    axes[0].set(title='Historical test period: daily totals across five products',ylabel='Recorded units / day')
    axes[0].legend()
    axes[1].barh(test.model,test.MAE,color=['#94a3b8']*3+['#60a5fa','#2563eb'])
    axes[1].set(title='Like-for-like rolling one-day evaluation',xlabel='Mean absolute error (units per product-day)')
    fig.savefig(figure_dir/'retail-evaluation.png',dpi=150)
    plt.close(fig)
    champion=test[test.model.eq(winner)].iloc[0]
    strongest=test[test.model.isin(['naive','weekly_naive','mean_7'])].sort_values('MAE').iloc[0]
    improvement=100*(strongest.MAE-champion.MAE)/strongest.MAE
    def table(frame):
        return '\n'.join(f"| {r.split} | {r.model} | {r.rows} | {r.MAE:.2f} | {r.RMSE:.2f} | {r.WAPE_percent:.2f} | {r.bias_forecast_minus_actual:.2f} |" for r in frame.itertuples())
    audit='\n'.join(f'- {key}: {quality[key]}' for key in ['raw_rows','exact_duplicate_rows','cancelled_rows','nonpositive_quantity_rows','nonpositive_price_rows','eligible_gross_sales_rows','calendar_rows_without_sale_records'])
    content=f'''# Pranav lead contribution - retail forecasting

Executed 26 October 2026. This is a tested local prototype, not the full team submission.

## What is implemented

Real UCI Online Retail inputs; documented gross-sales cleaning; five products selected using training invoice coverage only; past-only features; fixed calendar splits; three simple baselines and two Random Forest configurations; validation-only model selection; test predictions; per-product errors; trusted local model artifacts; one-day inference CLI.

## Data audit

{audit}

Exclusion counts overlap and must not be summed. Customer IDs are not used in features or derived data. Exact-duplicate removal and zero-recorded-sales days are explicit assumptions for Gourav to review. Missing stockout flags mean measured sales may understate latent demand. Source metadata says no missing values, but actual workbook null counts are recorded in quality.json and take precedence.

## Actual model results

| Split | Model | Product-days | MAE | RMSE | WAPE % | Bias (forecast - actual) |
| --- | --- | --- | --- | --- | --- | --- |
{table(scores)}

Frozen validation winner: **{winner}**. Test MAE is {champion.MAE:.2f} units/product-day; WAPE is {champion.WAPE_percent:.2f}%. MAE is {improvement:.1f}% lower than the strongest simple test baseline ({strongest.model}), but remaining absolute errors and negative bias are substantial. Results do not establish operational usefulness or inventory savings. Do not report WAPE as accuracy.

## Evaluation contract

Train through 30 June 2011; validation 1 July-31 August; test 1 September-8 December. Every prediction is one day ahead with yesterday's actual sales available. This is not a multi-day forecast from a single fixed origin. Lag/rolling features exclude current/future outcomes. Selection is frozen before test scoring; latest inference model is a separate refit after evaluation. Do not tune more models against this inspected test window and call it untouched.

## Forecast output and limitations

next-day-forecast.csv predicts 9 December 2011 from historical data through 8 December. It is an archived as-of demonstration, not a prediction for 2026. Stock and supplier inputs are absent, so no automatic stockout or order recommendation is emitted. Sanjai's module must request explicit inputs and label scenarios. Dataset is old, covers one retailer, includes wholesale spikes and only five selected products; generalization is limited.

## Team handoff

Data schema and module boundaries are in ../../RETAIL-DATA-CONTRACT.md. Nine tests pass including future-target perturbation, shared split dates, online/offline feature equivalence and invalid history rejection. CLI output is checked against the saved pipeline forecast. Raw source hash verified unchanged. Model/dashboard/report integration and official review/submission remain later work.

![Retail holdout comparison](figures/retail-evaluation.png)

Source: Chen, D. (2015), Online Retail, UCI Machine Learning Repository, DOI:10.24432/C5BW33, CC BY 4.0. https://archive.ics.uci.edu/dataset/352/online+retail
'''
    (REPORTS/'LEAD-REPORT.md').write_text(content,encoding='utf-8')
    print('Retail report and figures generated from frozen scores.')


if __name__=='__main__': main()
