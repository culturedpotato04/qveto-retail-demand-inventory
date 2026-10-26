"""Join a dated, explicitly assumed inventory snapshot to recorded-sales history."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from inventory import order_policy

ROOT = Path(__file__).resolve().parents[1]


def build_plan(history, config):
    if config.get('scenario_only') is not True or not config.get('assumption_note'):
        raise ValueError('This demo requires scenario_only=true and an assumption_note')
    as_of = pd.Timestamp(config['as_of'])
    lookback = config['lookback_days']
    if isinstance(lookback, bool) or not isinstance(lookback, int) or lookback < 2:
        raise ValueError('lookback_days must be an integer >= 2')
    history = history.copy()
    history['date'] = pd.to_datetime(history['date'], errors='raise')
    if history[['date', 'product_id', 'units']].isna().any().any():
        raise ValueError('History contains missing fields')
    history['product_id'] = history.product_id.astype(str)
    if history.duplicated(['date', 'product_id']).any():
        raise ValueError('Duplicate product/date history')
    if not np.isfinite(history.units).all() or (history.units < 0).any():
        raise ValueError('Recorded units must be finite and nonnegative')
    rows = config['products']
    skus = [r['product_id'] for r in rows]
    if not skus or len(set(skus)) != len(skus):
        raise ValueError('Scenario products must be unique and nonempty')
    if set(skus) != set(history.product_id):
        raise ValueError('Scenario must cover exactly the supplied history products')
    expected = pd.date_range(end=as_of, periods=lookback)
    output = []
    for item in rows:
        sku = item['product_id']
        g = history[history.product_id.eq(sku)].sort_values('date')
        g = g[g.date.between(expected[0], as_of)]
        if list(g.date) != list(expected):
            raise ValueError(f'{sku}: need {lookback} consecutive daily records ending {as_of.date()}')
        mean, std = float(g.units.mean()), float(g.units.std(ddof=1))
        inputs = {key: config[key] for key in ['lead_days', 'z_score', 'coverage_days', 'pack_size', 'minimum_order']}
        inputs.update({key: item[key] for key in ['stock', 'on_order', 'backorders']})
        result = order_policy(mean, std, **inputs)
        output.append({'as_of': str(as_of.date()), 'product_id': sku,
                       'demand_basis': f'trailing_{lookback}_day_recorded_sales',
                       'mean_daily_units': mean, 'std_daily_units': std,
                       **inputs, **result, 'assumption_note': config['assumption_note']})
    return pd.DataFrame(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', type=Path, default=ROOT/'data/processed/retail-daily.csv')
    parser.add_argument('--config', type=Path, default=ROOT/'config/inventory-demo.json')
    parser.add_argument('--output', type=Path, default=ROOT/'reports/retail/inventory-scenario.csv')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    history = pd.read_csv(args.history, dtype={'product_id': str})
    result = build_plan(history, config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print('ASSUMPTION-ONLY DEMO: no observed stock inputs or measured business savings.')
    print(result[['product_id', 'reorder_triggered', 'suggested_order_units']].to_string(index=False))


if __name__ == '__main__':
    main()
