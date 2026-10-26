"""Build a portable read-only review page from frozen CSV/JSON artifacts."""
import base64
import json
from html import escape
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/retail'


def main():
    result = json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    winner = result['winner_selected_on_validation_MAE']
    test = next(r for r in result['comparison'] if r['split'] == 'test' and r['model'] == winner)
    forecasts = pd.read_csv(OUT/'next-day-forecast.csv', dtype={'product_id': str})
    inventory = pd.read_csv(OUT/'inventory-scenario.csv', dtype={'product_id': str})
    products = result['quality']['selected_products']
    if set(forecasts.product_id) != set(inventory.product_id) or set(products) != set(forecasts.product_id):
        raise ValueError('Forecast, inventory and project product sets must match')
    forecast_date = pd.to_datetime(forecasts.date)
    stock_date = pd.to_datetime(inventory.as_of)
    if forecast_date.nunique() != 1 or stock_date.nunique() != 1 or forecast_date.iloc[0] != stock_date.iloc[0] + pd.Timedelta(days=1):
        raise ValueError('Forecast and inventory snapshot dates must align')
    if not inventory.scenario_only.eq(True).all():
        raise ValueError('Only explicitly labeled scenario inventory is supported')
    rows = forecasts.merge(inventory, on='product_id', validate='one_to_one')
    table = []
    for r in rows.to_dict('records'):
        table.append(f'''<tr data-sku="{escape(r['product_id'], quote=True)}"><td><strong>{escape(r['product_id'])}</strong><small>{escape(products[r['product_id']])}</small></td>
<td>{r['forecast_units']:.1f}</td><td>{r['mean_daily_units']:.1f}</td><td>{r['stock']:g}</td><td>{r['inventory_position']:g}</td><td>{r['reorder_point']:.1f}</td>
<td><span class="badge {'order' if r['reorder_triggered'] else ''}">{'Demo reorder' if r['reorder_triggered'] else 'Demo hold'}</span></td><td>{r['suggested_order_units']}</td></tr>''')
    options = ''.join(f'<option value="{escape(sku, quote=True)}">{escape(sku)} - {escape(name)}</option>' for sku, name in products.items())
    plot = base64.b64encode((OUT/'figures/retail-evaluation.png').read_bytes()).decode('ascii')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Qveto | Retail project review</title><style>
:root{font-family:system-ui,sans-serif;color:#dce8f5;background:#0d1522}*{box-sizing:border-box}body{margin:0}main{max-width:1280px;margin:auto;padding:40px 28px}h1{font-size:clamp(28px,4vw,44px);letter-spacing:-1.4px;margin:12px 0}h2{font-size:23px;margin:0 0 14px}.eyebrow{color:#88cbbb;letter-spacing:2px;font-size:12px}p{line-height:1.6;color:#aebed1}.banner{border-left:4px solid #e9b968;background:#28251f;padding:14px 18px;color:#f3dab4;border-radius:5px;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card,section{background:#152133;border:1px solid #293a50;border-radius:12px;padding:20px}.card b{display:block;font-size:30px;margin-top:10px}.card small{color:#aebed1}section{margin-top:22px}.split{display:grid;grid-template-columns:1fr 1fr;gap:22px}label{display:block;margin:20px 0 8px}select{background:#0d1522;color:#fff;border:1px solid #61748b;border-radius:6px;padding:12px;width:min(100%,600px)}.scroll{overflow-x:auto;margin-top:18px}table{border-collapse:collapse;width:100%;font-size:14px;min-width:1000px}th,td{text-align:left;padding:14px 12px;border-bottom:1px solid #293a50}th{color:#9bb2ca;font-weight:500}td small{display:block;color:#aebed1;font-size:11px;max-width:200px;margin-top:5px}.badge{font-size:11px;border:1px solid #476977;border-radius:20px;padding:5px 9px;white-space:nowrap}.order{color:#ffe1a5;border-color:#aa884b}img{display:block;width:100%;height:auto;border-radius:8px;background:#fff}code{color:#a4e0cf}li{line-height:1.8;color:#b8c7d9}a{color:#92dac7}footer{margin-top:24px;color:#94a8be;font-size:13px}[hidden]{display:none}@media(max-width:760px){.grid{grid-template-columns:repeat(2,1fr)}.split{grid-template-columns:1fr}main{padding:24px 15px}.card b{font-size:26px}}
</style><main><div class="eyebrow">QVETO / GROUP 4 / LOCAL INTEGRATION REVIEW</div>
<h1>Retail demand, with the evidence visible.</h1><p>Pranav's forecasting core and an inventory integration reference. Prepared 26 October 2026. Archived sales through 8 December 2011.</p>
<div class="banner"><strong>Historical forecast + assumed inventory.</strong> The forecast is for 9 December 2011. Every stock, lead-time and supplier setting is invented for this demo. These are not live purchase recommendations.</div>
<div class="grid"><div class="card"><small>Test MAE / units per SKU-day</small><b>__MAE__</b></div><div class="card"><small>Test WAPE / lower is better</small><b>__WAPE__%</b></div><div class="card"><small>Test coverage</small><b>495</b><small>99 days x 5 products</small></div><div class="card"><small>Automated checks</small><b>14 passed</b><small>Recorded 26 October 2026</small></div></div>
<section><h2>Product forecast & inventory scenario</h2><p>ML predicts the next day's recorded sales. The inventory policy uses trailing 28-day recorded-sales mean and standard deviation, independently of that one-day prediction. Displayed units are rounded; calculations retain precision.</p>
<label for="product">Choose product</label><select id="product"><option value="all">All five products</option>__OPTIONS__</select><p id="selection" aria-live="polite">Showing 5 products.</p>
<div class="scroll"><table><thead><tr><th>Product</th><th>ML next-day units</th><th>28-day mean</th><th>Assumed stock</th><th>Inventory position</th><th>Reorder point</th><th>Scenario status</th><th>Demo order units</th></tr></thead><tbody>__ROWS__</tbody></table></div></section>
<section><h2>Frozen model evaluation</h2><p>Winner: <code>__WINNER__</code>, chosen on July-August validation MAE. Final test: 1 September-8 December 2011. Predictions are rolling one day ahead with actual previous-day observations. Substantial error remains; WAPE is not an accuracy score.</p><img src="data:image/png;base64,__PLOT__" alt="Historical held-out actual and predicted aggregate sales, with model MAE comparison"></section>
<div class="split"><section><h2>Inventory assumptions</h2><ul><li>Fixed supplier lead time: 3 days; extra cycle coverage: 7 days.</li><li>Normal approximation z = 1.645; achieved service level is unmeasured.</li><li>Independent, stationary daily demand and deterministic lead time.</li><li>Pack size: 12 units. Minimum order: 24 units.</li><li>Position = stock + on-order - backorders.</li><li>Continuous-review trigger at or below reorder point; order to the target, rounded up to packs.</li></ul><p>Inputs live in <code>config/inventory-demo.json</code>. No inventory backtest or measured savings is available.</p></section>
<section><h2>Team handoff</h2><ul><li>Gourav: review cleaning, returns, duplicates and zero-day assumptions.</li><li>Rayash: independently audit features, evaluation and errors.</li><li>Sanjai: review/extend this policy and replace assumptions when verified inputs exist.</li><li>Varsha: build final dashboard and report/slides using these contracts.</li><li>Pranav: integrate, review contributions and prepare release.</li></ul><p>Assignments await acknowledgement. Shared repository and official submission remain pending. Working date: 6 November; company cutoff unverified.</p></section></div>
<footer>Source: <a href="https://archive.ics.uci.edu/dataset/352/online+retail">Chen (2015), UCI Online Retail, CC BY 4.0</a>. Customer IDs are excluded. No-sale dates are zero recorded sales; latent demand and stockouts are unknown. This self-contained page makes no network requests until a source link is opened.</footer>
</main><script>const picker=document.getElementById('product');picker.addEventListener('change',()=>{let count=0;document.querySelectorAll('tr[data-sku]').forEach(row=>{row.hidden=picker.value!=='all'&&row.dataset.sku!==picker.value;if(!row.hidden)count++});document.getElementById('selection').textContent='Showing '+count+' product'+(count===1?'':'s')+'.'});</script></html>'''
    replacements = {'__MAE__': f"{test['MAE']:.2f}", '__WAPE__': f"{test['WAPE_percent']:.2f}",
                    '__WINNER__': escape(winner), '__OPTIONS__': options,
                    '__ROWS__': '\n'.join(table), '__PLOT__': plot}
    for key, value in replacements.items():
        page = page.replace(key, value)
    target = OUT/'review.html'
    target.write_text(page, encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()
