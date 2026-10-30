"""Interactive, historical retail research dashboard. Run with streamlit run src/app.py."""
from pathlib import Path
import json
import joblib
import pandas as pd
import streamlit as st
from inventory import order_policy
from retail_pipeline import forecast_next

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/retail'
st.set_page_config(page_title='Retail demand lab', layout='wide')
st.title('Retail demand & inventory lab')
st.caption('Qveto Project 1 | Historical UK retail, December 2010 - December 2011')
st.warning('Research demonstration. Forecasts are for archived 2011 dates, not live 2026 sales. Stock and supplier inputs below are assumptions.')
quality = json.loads((REPORT/'quality.json').read_text())
catalog = quality['selected_products']
product = st.selectbox('Product', list(catalog), format_func=lambda key: f'{key} - {catalog[key]}')
pred = pd.read_csv(REPORT/'test-predictions.csv', dtype={'product_id':str}, parse_dates=['date'])
daily = pd.read_csv(ROOT/'data/processed/retail-daily.csv', dtype={'product_id':str}, parse_dates=['date'])
comparison = pd.read_csv(REPORT/'comparison.csv')
winner = json.loads((REPORT/'results.json').read_text())['winner_selected_on_validation_MAE']
overview, forecasts, risk, performance = st.tabs(['Demand overview', 'Product forecasts', 'Inventory scenario', 'Model performance'])
with overview:
    st.subheader('Rolling one-day evaluation')
    st.caption('Each prediction uses actual observations through the preceding day. This does not measure multi-day forecasts made at a fixed origin.')
    selected = pred[pred.product_id.eq(product)].set_index('date')
    dates = st.date_input('Evaluation date range', (selected.index.min().date(), selected.index.max().date()), min_value=selected.index.min().date(), max_value=selected.index.max().date())
    if len(dates)==2:
        selected=selected.loc[str(dates[0]):str(dates[1])]
    st.line_chart(selected[['actual_units',winner]].rename(columns={winner:'forecast_units'}))
    st.download_button('Download filtered predictions', selected.to_csv().encode(), 'predictions.csv', 'text/csv')
with forecasts:
    st.subheader('Historical pattern and archived next-day inference')
    history=daily[daily.product_id.eq(product)]
    st.line_chart(history.set_index('date')[['units']])
    st.caption('Trusted local model; trained through 8 December 2011. One-day horizon only. No user-uploaded model files are loaded.')
    if st.button('Generate archived forecast'):
        bundle=joblib.load(ROOT/'models/retail-forecast-latest.joblib')
        answer=forecast_next(history,bundle['model'],bundle['model_name'])
        st.dataframe(answer, hide_index=True)
        st.success(f"Archived forecast: {answer.forecast_units.iloc[0]:.2f} units for {answer.date.iloc[0].date()}")
with risk:
    st.subheader('Illustrative continuous-review inventory policy')
    st.caption('Trailing 28 recorded-sales days estimate mean and standard deviation. Constant lead time, independent stationary daily demand and normal approximation; no measured stockout or savings claim.')
    hist=daily[daily.product_id.eq(product)].sort_values('date').tail(28).units
    with st.form('inventory'):
        stock=st.number_input('Assumed stock on hand', min_value=0.0,value=50.0)
        on_order=st.number_input('Assumed units already on order', min_value=0.0,value=0.0)
        backorders=st.number_input('Assumed backorders',min_value=0.0,value=0.0)
        lead=st.number_input('Assumed supplier lead time (days)',min_value=0.0,value=3.0)
        coverage=st.number_input('Extra replenishment coverage (days)',min_value=0.1,value=7.0)
        z=st.number_input('Assumed normal safety factor',min_value=0.0,value=1.645)
        pack=st.number_input('Order pack size',min_value=1,value=12,step=1)
        minimum=st.number_input('Minimum order quantity',min_value=0,value=24,step=1)
        calculate=st.form_submit_button('Calculate scenario')
    if calculate:
        result=order_policy(float(hist.mean()),float(hist.std()),lead,z,stock,on_order,backorders,coverage,int(pack),int(minimum))
        st.metric('Illustrative order quantity',result['suggested_order_units'])
        st.json(result)
        st.download_button('Download scenario',json.dumps({'product_id':product,'as_of':'2011-12-08','assumed_inputs':{'stock':stock,'on_order':on_order,'backorders':backorders,'lead_days':lead,'coverage_days':coverage,'z_score':z,'pack_size':pack,'minimum_order':minimum},'result':result},indent=2), 'scenario.json','application/json')
with performance:
    st.subheader('Frozen model comparison')
    st.caption('Selected using validation MAE, before test scoring. Bias = forecast minus actual. WAPE is percentage error, not accuracy.')
    score=comparison[(comparison.split=='test') & (comparison.model==winner)].iloc[0]
    a,b,c=st.columns(3)
    a.metric('Test MAE (units)',f'{score.MAE:.2f}')
    b.metric('Test RMSE (units)',f'{score.RMSE:.2f}')
    c.metric('Test WAPE (error)',f'{score.WAPE_percent:.2f}%')
    st.dataframe(comparison,hide_index=True)
    errors=pd.read_csv(REPORT/'per-product-errors.csv',dtype={'product_id':str})
    st.dataframe(errors[errors.product_id.eq(product)],hide_index=True)
    st.caption('Large burst errors and negative bias limit operational use. Five popular products are not representative of the full catalog; price, promotions, lost demand and inventory are unavailable.')
