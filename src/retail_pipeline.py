"""Real retail lead contribution: audited product series, past-only ML and forecasts.

Run from any directory: python src/retail_pipeline.py
Uses fixed dates and training-only SKU selection; never tunes on the holdout.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
import joblib
from pipeline import metrics

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ['lag_1','lag_7','lag_14','mean_7','mean_28','std_28','weekday','month','day_of_year']
TRAIN_END = pd.Timestamp('2011-06-30')
VAL_END = pd.Timestamp('2011-08-31')
DATA_END = pd.Timestamp('2011-12-08')  # Exclude last partial source date, 9 December.


def make_features(daily):
    daily = daily.sort_values(['product_id','date']).copy()
    pieces = []
    for sku, group in daily.groupby('product_id', sort=True):
        g = group.copy()
        past = g.units.shift(1)
        for lag in (1,7,14): g[f'lag_{lag}'] = g.units.shift(lag)
        g['mean_7'] = past.rolling(7).mean()
        g['mean_28'] = past.rolling(28).mean()
        g['std_28'] = past.rolling(28).std(ddof=1)
        g['weekday'] = g.date.dt.dayofweek
        g['month'] = g.date.dt.month
        g['day_of_year'] = g.date.dt.dayofyear
        pieces.append(g)
    return pd.concat(pieces, ignore_index=True).dropna(subset=NUMERIC)


def split_labels(dates):
    return np.where(dates <= TRAIN_END,'train',np.where(dates <= VAL_END,'validation','test'))


def build_model(leaf):
    encoder = ColumnTransformer([('sku',OneHotEncoder(handle_unknown='ignore',sparse_output=False),['product_id'])],remainder='passthrough')
    return Pipeline([('encode',encoder),('regressor',RandomForestRegressor(n_estimators=120,min_samples_leaf=leaf,max_depth=12,random_state=42,n_jobs=2))])


def prepare():
    raw_path = ROOT/'data/raw/retail/original/Online Retail.xlsx'
    frame = pd.read_excel(raw_path,engine='openpyxl',dtype={'InvoiceNo':str,'StockCode':str})
    quality = {'raw_rows':len(frame),'raw_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
               'missing_by_column':{k:int(v) for k,v in frame.isna().sum().items()},
               'exact_duplicate_rows':int(frame.duplicated().sum()),
               'cancelled_rows':int(frame.InvoiceNo.str.upper().str.startswith('C').sum()),
               'nonpositive_quantity_rows':int(frame.Quantity.le(0).sum()),
               'nonpositive_price_rows':int(frame.UnitPrice.le(0).sum())}
    # Explicit, reproducible gross-sales policy. Reasons can overlap; counts are not additive.
    clean = frame.drop_duplicates().copy()
    keep = (clean.Country.eq('United Kingdom') & clean.Quantity.gt(0) & clean.UnitPrice.gt(0)
            & ~clean.InvoiceNo.str.upper().str.startswith('C')
            & clean.StockCode.str.fullmatch(r'\d{5}[A-Z]?').fillna(False)
            & clean.Description.notna() & clean.InvoiceDate.notna())
    clean = clean.loc[keep,['InvoiceNo','StockCode','Description','Quantity','InvoiceDate']].copy()
    clean['date'] = pd.to_datetime(clean.InvoiceDate).dt.normalize()
    clean = clean[clean.date <= DATA_END]
    training = clean[clean.date <= TRAIN_END]
    # SKU selection by training invoice coverage, never future target volume.
    ranking = training.groupby('StockCode').InvoiceNo.nunique().sort_values(ascending=False,kind='stable')
    selected = ranking.head(5).index.tolist()
    catalog = training[training.StockCode.isin(selected)].groupby('StockCode').Description.agg(lambda x:x.mode().iloc[0]).to_dict()
    daily = clean[clean.StockCode.isin(selected)].groupby(['StockCode','date']).Quantity.sum()
    calendar = pd.date_range(clean.date.min(),DATA_END,freq='D')
    full = pd.MultiIndex.from_product([selected,calendar],names=['product_id','date'])
    panel = daily.reindex(full).rename('units').reset_index()
    panel['has_recorded_sale'] = panel.units.notna()
    panel['units'] = panel.units.fillna(0).astype(int)
    quality.update({'eligible_gross_sales_rows':len(clean),'selected_products':catalog,
                    'sku_selection':'top five by distinct training invoices through 2011-06-30',
                    'calendar_rows_without_sale_records':int((~panel.has_recorded_sale).sum()),
                    'zero_policy':'zero recorded sales in this file; unknown latent demand/stockout/closure, not certified true zero demand',
                    'last_partial_date_excluded':'2011-12-09','customer_ids_retained_in_derived_outputs':False,
                    'stock_or_supplier_fields_available':False})
    return panel,quality


def forecast_next(history, model, model_name):
    rows=[]
    for sku,g in history.groupby('product_id',sort=True):
        g=g.sort_values('date')
        if len(g)<28 or not np.isfinite(g.units).all() or g.units.lt(0).any():
            raise ValueError('Need at least 28 nonnegative daily records per product')
        if not g.date.diff().dropna().eq(pd.Timedelta(days=1)).all():
            raise ValueError('History must contain consecutive dates')
        target=g.date.iloc[-1]+pd.Timedelta(days=1)
        values=g.units.to_numpy()
        row={'product_id':sku,'date':target,'lag_1':values[-1],'lag_7':values[-7],'lag_14':values[-14],
             'mean_7':values[-7:].mean(),'mean_28':values[-28:].mean(),'std_28':values[-28:].std(ddof=1),
             'weekday':target.dayofweek,'month':target.month,'day_of_year':target.dayofyear}
        rows.append(row)
    out=pd.DataFrame(rows)
    if model_name=='naive': prediction=out.lag_1.to_numpy()
    elif model_name=='weekly_naive': prediction=out.lag_7.to_numpy()
    elif model_name=='mean_7': prediction=out.mean_7.to_numpy()
    else: prediction=np.maximum(0,model.predict(out[['product_id']+NUMERIC]))
    return pd.DataFrame({'date':out.date,'product_id':out.product_id,'forecast_units':prediction,'model':model_name})


def main():
    out=ROOT/'reports/retail'
    out.mkdir(parents=True,exist_ok=True)
    (ROOT/'data/processed').mkdir(exist_ok=True,parents=True)
    (ROOT/'models').mkdir(exist_ok=True)
    daily,quality=prepare()
    daily.to_csv(ROOT/'data/processed/retail-daily.csv',index=False)
    featured=make_features(daily)
    featured['split']=split_labels(featured.date)
    featured.to_csv(ROOT/'data/processed/retail-features.csv',index=False)
    groups={s:featured[featured.split.eq(s)] for s in ['train','validation','test']}
    assert groups['train'].date.max()<groups['validation'].date.min()<groups['test'].date.min()
    trained={}
    val_predictions={name:groups['validation'][col].to_numpy() for name,col in [('naive','lag_1'),('weekly_naive','lag_7'),('mean_7','mean_7')]}
    for leaf in (3,10):
        name=f'random_forest_leaf_{leaf}'
        model=build_model(leaf)
        model.fit(groups['train'][['product_id']+NUMERIC],groups['train'].units)
        trained[name]=model
        val_predictions[name]=np.maximum(0,model.predict(groups['validation'][['product_id']+NUMERIC]))
    comparison=[]
    for name,values in val_predictions.items():
        comparison.append({'split':'validation','model':name,'rows':len(values),**metrics(groups['validation'].units,values)})
    winner=min(comparison,key=lambda x:x['MAE'])['model']
    # Freeze winner before touching test scores, then refit ML candidates with train+validation.
    fit_data=featured[featured.split.ne('test')]
    test=groups['test']
    test_predictions={'naive':test.lag_1.to_numpy(),'weekly_naive':test.lag_7.to_numpy(),'mean_7':test.mean_7.to_numpy()}
    final_models={}
    for name in trained:
        leaf=int(name.rsplit('_',1)[1])
        model=build_model(leaf)
        model.fit(fit_data[['product_id']+NUMERIC],fit_data.units)
        final_models[name]=model
        test_predictions[name]=np.maximum(0,model.predict(test[['product_id']+NUMERIC]))
    predictions=test[['date','product_id','units']].copy().rename(columns={'units':'actual_units'})
    per_product=[]
    for name,values in test_predictions.items():
        comparison.append({'split':'test','model':name,'rows':len(values),**metrics(test.units,values)})
        predictions[name]=values
        for sku,index in test.groupby('product_id').groups.items():
            positions=test.index.get_indexer(index)
            per_product.append({'product_id':sku,'model':name,**metrics(test.loc[index,'units'],np.asarray(values)[positions])})
    pd.DataFrame(comparison).to_csv(out/'comparison.csv',index=False)
    pd.DataFrame(per_product).to_csv(out/'per-product-errors.csv',index=False)
    predictions.to_csv(out/'test-predictions.csv',index=False)
    selected=final_models.get(winner)
    bundle={'model':selected,'model_name':winner,'features':NUMERIC,'cutoff':str(VAL_END.date()),'products':quality['selected_products']}
    joblib.dump(bundle,ROOT/'models/retail-forecast.joblib',compress=3)
    # Production-fit variant uses all history only after locked evaluation is saved.
    if selected is not None:
        selected=build_model(int(winner.rsplit('_',1)[1]))
        selected.fit(featured[['product_id']+NUMERIC],featured.units)
    next_day=forecast_next(daily,selected,winner)
    next_day.to_csv(out/'next-day-forecast.csv',index=False)
    joblib.dump({**bundle,'model':selected,'cutoff':str(DATA_END.date())},ROOT/'models/retail-forecast-latest.joblib',compress=3)
    split_summary={s:{'rows':len(g),'start':str(g.date.min().date()),'end':str(g.date.max().date())} for s,g in groups.items()}
    result={'run_date':'2026-10-26','winner_selected_on_validation_MAE':winner,'quality':quality,'splits':split_summary,
            'features':NUMERIC,'horizon':'rolling one day ahead; actual previous-day observations available',
            'inventory_predictions':'not produced: no observed inventory/lead-time fields','comparison':comparison}
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (out/'quality.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
    print(pd.DataFrame(comparison).to_string(index=False))
    print('Frozen validation winner:',winner)
    print('Lead forecasting module completed; results:',out)


if __name__=='__main__': main()
