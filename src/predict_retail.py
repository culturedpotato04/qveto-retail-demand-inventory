"""CLI integration boundary for the dashboard owner; loads only our local artifact."""
import argparse
from pathlib import Path
import joblib
import pandas as pd
from retail_pipeline import forecast_next,ROOT


def main():
    parser=argparse.ArgumentParser(description='One-day retail forecast from consecutive recorded-sales history')
    parser.add_argument('--history',type=Path,default=ROOT/'data/processed/retail-daily.csv')
    parser.add_argument('--model',type=Path,default=ROOT/'models/retail-forecast-latest.joblib')
    parser.add_argument('--output',type=Path,default=ROOT/'reports/retail/cli-forecast.csv')
    args=parser.parse_args()
    history=pd.read_csv(args.history,parse_dates=['date'],dtype={'product_id':str})
    artifact=joblib.load(args.model)  # Never load arbitrary untrusted pickle/joblib files.
    unknown=set(history.product_id)-set(artifact['products'])
    if unknown: raise ValueError(f'Unsupported product IDs: {sorted(unknown)}')
    prediction=forecast_next(history,artifact['model'],artifact['model_name'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    prediction.to_csv(args.output,index=False)
    print(prediction.to_string(index=False))


if __name__=='__main__': main()
