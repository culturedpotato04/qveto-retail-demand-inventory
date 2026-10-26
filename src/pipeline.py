"""Reproducible real-data demand audit, EDA and rolling one-day baseline evaluation."""
from __future__ import annotations
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ['lag_1', 'lag_7', 'rolling_mean_7', 'rolling_std_7', 'rolling_mean_28', 'weekday', 'month']


def audit(raw):
    data = raw.copy()
    data['dteday'] = pd.to_datetime(data['dteday'], errors='raise')
    data = data.sort_values('dteday').reset_index(drop=True)
    missing_dates = pd.date_range(data.dteday.min(), data.dteday.max()).difference(data.dteday)
    quality = {'rows': len(data), 'columns': list(data.columns),
               'date_start': str(data.dteday.min().date()), 'date_end': str(data.dteday.max().date()),
               'duplicate_dates': int(data.dteday.duplicated().sum()), 'duplicate_rows': int(data.duplicated().sum()),
               'missing_dates': [str(x.date()) for x in missing_dates],
               'missing_values': {k: int(v) for k, v in data.isna().sum().items()},
               'negative_targets': int((data.cnt < 0).sum()),
               'noninteger_targets': int((data.cnt % 1 != 0).sum()),
               'target_component_mismatches': int((data.cnt != data.casual + data.registered).sum())}
    if quality['duplicate_dates'] or len(missing_dates) or data.isna().any().any() or quality['negative_targets'] or quality['noninteger_targets'] or quality['target_component_mismatches']:
        raise ValueError('Source quality checks failed; investigate instead of silently repairing')
    return data, quality


def features(data):
    frame = data[['dteday', 'cnt']].copy()
    frame['lag_1'] = frame.cnt.shift(1)
    frame['lag_7'] = frame.cnt.shift(7)
    history = frame.cnt.shift(1)
    frame['rolling_mean_7'] = history.rolling(7).mean()
    frame['rolling_std_7'] = history.rolling(7).std(ddof=1)
    frame['rolling_mean_28'] = history.rolling(28).mean()
    frame['weekday'] = frame.dteday.dt.dayofweek
    frame['month'] = frame.dteday.dt.month
    return frame.dropna().reset_index(drop=True)


def partition(frame):
    result = frame.copy()
    n = len(result)
    result['split'] = ['train'] * int(n * .6) + ['validation'] * (int(n * .8) - int(n * .6)) + ['test'] * (n - int(n * .8))
    return result


def metrics(actual, forecast):
    actual = np.asarray(actual, dtype=float)
    forecast = np.asarray(forecast, dtype=float)
    if len(actual) == 0 or actual.shape != forecast.shape or not np.isfinite(actual).all() or not np.isfinite(forecast).all():
        raise ValueError('Metric inputs must be nonempty, finite and equally shaped')
    error = forecast - actual
    denominator = np.abs(actual).sum()
    return {'MAE': float(np.abs(error).mean()), 'RMSE': float(np.sqrt(np.mean(error ** 2))),
            'WAPE_percent': float(np.abs(error).sum() / denominator * 100) if denominator else None,
            'bias_forecast_minus_actual': float(error.mean())}


def main():
    reports = ROOT / 'reports'
    figures = reports / 'figures'
    figures.mkdir(parents=True, exist_ok=True)
    for folder in ['interim', 'processed']:
        (ROOT / 'data' / folder).mkdir(parents=True, exist_ok=True)
    manifest = []
    for file in sorted((ROOT / 'data' / 'raw').rglob('*')):
        if file.is_file():
            manifest.append({'file': str(file.relative_to(ROOT)), 'bytes': file.stat().st_size, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    data, quality = audit(pd.read_csv(ROOT / 'data' / 'raw' / 'uci-bike-sharing' / 'day.csv'))
    data.to_csv(ROOT / 'data' / 'interim' / 'daily-audited.csv', index=False)
    frame = partition(features(data))
    frame['naive'] = frame.lag_1
    frame['seasonal_naive_7'] = frame.lag_7
    frame.to_csv(ROOT / 'data' / 'processed' / 'features-and-baselines.csv', index=False)
    rows = []
    for split in ['validation', 'test']:
        subset = frame[frame.split.eq(split)]
        for model in ['naive', 'seasonal_naive_7']:
            rows.append({'split': split, 'baseline': model, 'n': len(subset), **metrics(subset.cnt, subset[model])})
    comparison = pd.DataFrame(rows)
    # Selection uses validation only, even though both holdout benchmark rows are reported.
    selected = comparison[comparison.split.eq('validation')].sort_values('MAE').iloc[0].baseline
    comparison.to_csv(reports / 'baseline-comparison.csv', index=False)
    frame[frame.split.eq('test')][['dteday', 'cnt', 'naive', 'seasonal_naive_7']].to_csv(reports / 'test-predictions.csv', index=False)
    split_info = {s: {'rows': len(g), 'start': str(g.dteday.min().date()), 'end': str(g.dteday.max().date())} for s,g in frame.groupby('split', sort=False)}
    results = {'date': '2026-10-18', 'quality': quality, 'warmup_rows': len(data)-len(frame), 'splits': split_info,
               'horizon': 'rolling one day ahead', 'selected_by_validation_MAE': selected, 'metrics': rows,
               'inventory_inputs_available': False, 'team_confirmation': 'pending',
               'runtime': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'matplotlib': matplotlib.__version__}}
    (reports / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    (reports / 'raw-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    data.cnt.describe().to_csv(reports / 'demand-descriptive-statistics.csv')
    weekly = data.groupby(data.dteday.dt.dayofweek).cnt.mean()
    monthly = data.set_index('dteday').cnt.resample('MS').mean()
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), layout='constrained')
    axes[0].plot(data.dteday, data.cnt, lw=.8, color='#166534')
    axes[0].set(title='Observed daily bike rentals - UCI 2011-2012', ylabel='Rentals / day')
    axes[1].bar(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], weekly.reindex(range(7)), color='#2563eb')
    axes[1].set(title='Descriptive weekday averages - full dataset', ylabel='Mean rentals / day')
    axes[2].plot(monthly.index, monthly.values, marker='o', color='#7c3aed')
    axes[2].set(title='Descriptive monthly averages - full dataset', ylabel='Mean rentals / day')
    fig.savefig(figures / 'eda.png', dpi=150)
    plt.close(fig)
    holdout = frame[frame.split.eq('test')]
    fig, ax = plt.subplots(figsize=(11, 4), layout='constrained')
    ax.plot(holdout.dteday, holdout.cnt, label='Actual', lw=1.2, color='#111827')
    ax.plot(holdout.dteday, holdout[selected], label=selected, alpha=.7, color='#2563eb')
    ax.set(title=f'Reserved test window - {selected} chosen on validation MAE', ylabel='Rentals / day')
    ax.legend()
    fig.savefig(figures / 'holdout.png', dpi=150)
    plt.close(fig)
    table = '\n'.join('| ' + ' | '.join([row['split'], row['baseline'], str(row['n']), f"{row['MAE']:.2f}", f"{row['RMSE']:.2f}", f"{row['WAPE_percent']:.2f}", f"{row['bias_forecast_minus_actual']:.2f}"]) + ' |' for row in rows)
    report = f'''# Week 1/2 forecasting results

Real UCI daily bike-rental benchmark. Team confirmation of proposed project/domain adaptation pending. Run date: 18 October 2026.

## Data and quality

{len(data)} daily observations, {quality['date_start']} through {quality['date_end']}. No missing dates, duplicate dates, nulls or negative/noninteger targets. Total demand equals casual plus registered for every row. Raw files are preserved with SHA-256 hashes. No source records were imputed or deleted. The first {len(data)-len(frame)} rows are excluded from modeling only to warm up past-only features.

## Baselines

| Window | Baseline | Days | MAE | RMSE | WAPE % | Bias |
| --- | --- | --- | --- | --- | --- | --- |
{table}

Chosen on validation MAE: **{selected}**. Split boundaries and full-precision metrics are in results.json. All methods use the same validation/test dates. Bias is forecast minus actual; positive means overprediction. WAPE aggregates absolute errors over total observed demand, rather than averaging daily percentages.

## Interpretation and limits

Daily observed rentals are a demand proxy, not unconstrained demand or inventory sales. There is only one aggregate series, no SKU/store or stockout labels, and no supplier/stock information. The descriptive EDA uses the full dataset but does not tune models; model selection uses validation MAE only. Same-day weather and target components are excluded from features. Later observed test-day targets enter subsequent one-day forecasts, as permitted by the stated rolling-origin contract; do not present these as a multi-day forecast made before the whole test window.

No causal claims, inventory savings, advanced model improvement or production readiness are established. Dataset age, two-year coverage, seasonal changes and unusual events limit generalization. Dashboard/API, advanced models and real inventory backtesting remain later work.

## Figures

![Exploratory analysis](figures/eda.png)

![Test-window forecast](figures/holdout.png)
'''
    (reports / 'RESULTS.md').write_text(report, encoding='utf-8')
    print(comparison.to_string(index=False))
    print('Selected on validation MAE:', selected)
    print('Quality and split checks passed. Results:', reports)


if __name__ == '__main__':
    main()
