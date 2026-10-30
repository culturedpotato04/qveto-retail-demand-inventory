"""Reproducible descriptive analysis of frozen data/predictions; no model tuning."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'reports/retail'
    figs=out/'figures'
    figs.mkdir(exist_ok=True)
    daily=pd.read_csv(ROOT/'data/processed/retail-daily.csv',dtype={'product_id':str},parse_dates=['date'])
    pred=pd.read_csv(out/'test-predictions.csv',dtype={'product_id':str},parse_dates=['date'])
    winner=json.loads((out/'results.json').read_text())['winner_selected_on_validation_MAE']
    summary=daily.groupby('product_id').units.agg(days='size',mean='mean',std='std',maximum='max',total='sum')
    summary['zero_sales_fraction']=daily.assign(zero=daily.units.eq(0)).groupby('product_id').zero.mean()
    summary.to_csv(out/'demand-profile.csv')
    train=daily[daily.date.le('2011-06-30')].copy()
    train['weekday']=train.date.dt.day_name()
    weekday=train.groupby(['product_id','weekday']).units.mean().unstack().reindex(columns=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    weekday.to_csv(out/'training-weekday-profile.csv')
    pred['error']=pred[winner]-pred.actual_units
    pred['absolute_error']=pred.error.abs()
    pred['month']=pred.date.dt.strftime('%Y-%m')
    monthly=pred.groupby('month').apply(lambda g:pd.Series({'rows':len(g),'MAE':g.absolute_error.mean(),'RMSE':np.sqrt((g.error**2).mean()),'WAPE_percent':100*g.absolute_error.sum()/g.actual_units.sum(),'bias':g.error.mean()}),include_groups=False)
    monthly.to_csv(out/'test-month-errors.csv')
    worst=pred.nlargest(15,'absolute_error')[['date','product_id','actual_units',winner,'error','absolute_error']]
    worst.to_csv(out/'largest-errors.csv',index=False)
    fig,ax=plt.subplots(figsize=(11,4))
    for sku,g in daily.groupby('product_id'):
        ax.plot(g.date,g.units.rolling(7).mean(),label=sku,lw=1.2)
    ax.set(title='Recorded sales: seven-day trailing mean',ylabel='Units per day',xlabel='Historical date')
    ax.legend(ncol=5); fig.tight_layout(); fig.savefig(figs/'demand-pattern.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4))
    ax.scatter(pred.actual_units,pred[winner],alpha=.45,s=14)
    limit=max(pred.actual_units.max(),pred[winner].max()); ax.plot([0,limit],[0,limit],color='black',ls='--')
    ax.set(title='Frozen test: bursts are systematically underpredicted',xlabel='Actual recorded units',ylabel='Predicted units')
    fig.tight_layout(); fig.savefig(figs/'error-scatter.png',dpi=150);plt.close(fig)
    text='''# Retail analytical findings - 30 October 2026

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
'''
    (out/'ANALYSIS.md').write_text(text,encoding='utf-8')
    # Executed notebook uses the same reproducible analysis, with genuine captured outputs.
    code="from pathlib import Path\nimport pandas as pd\nROOT=Path.cwd() if (Path.cwd()/'src').exists() else Path.cwd().parent\nfor name in ['demand-profile.csv','test-month-errors.csv','largest-errors.csv']:\n    print(pd.read_csv(ROOT/'reports/retail'/name).to_string(index=False))"
    ns={'__name__':'notebook'}
    import contextlib,io,os
    buffer=io.StringIO(); previous=Path.cwd()
    try:
        os.chdir(ROOT)
        # Do not recurse into main(); read actual generated analytical outputs.
        with contextlib.redirect_stdout(buffer):
            exec(code,ns)
    finally: os.chdir(previous)
    notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'cells':[{'cell_type':'markdown','metadata':{},'source':['# Retail EDA and frozen error analysis\n','Executed 30 October 2026. Re-run from the project or notebooks directory after generating the retail pipeline outputs. No test-window tuning.\n']},{'cell_type':'code','execution_count':1,'metadata':{},'source':code.splitlines(True),'outputs':[{'output_type':'stream','name':'stdout','text':buffer.getvalue().splitlines(True)}]},{'cell_type':'markdown','metadata':{},'source':text.splitlines(True)}]}
    (ROOT/'notebooks/02-retail-analysis.ipynb').write_text(json.dumps(notebook,indent=1),encoding='utf-8')
    print(summary.to_string());print(monthly.to_string())

if __name__=='__main__':main()

