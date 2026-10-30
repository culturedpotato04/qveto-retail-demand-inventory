"""Read-only archived forecasts and explicit scenario calculation; no model uploads."""
from pathlib import Path
import json
import math
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from inventory import order_policy

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/retail'
app=FastAPI(title='Archived retail forecasting',version='1.0.0')

@app.get('/health')
def health(): return {'status':'ok','historical_only':True}

@app.get('/products')
def products(): return json.loads((REPORT/'quality.json').read_text())['selected_products']

@app.get('/forecast/{product_id}')
def forecast(product_id:str,horizon:int=Query(1,ge=1,le=1)):
    if product_id not in products(): raise HTTPException(404,'Unknown product')
    frame=pd.read_csv(REPORT/'next-day-forecast.csv',dtype={'product_id':str})
    row=frame[frame.product_id.eq(product_id)].iloc[0].to_dict()
    return {**row,'historical_only':True,'horizon_days':horizon,'as_of':'2011-12-08','basis':'Archived inference from the trusted local model; not live demand'}

class Scenario(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    mean_daily:float=Field(ge=0)
    std_daily:float=Field(ge=0)
    lead_days:float=Field(ge=0)
    z_score:float=Field(ge=0)
    stock:float=Field(ge=0)
    on_order:float=Field(0,ge=0)
    backorders:float=Field(0,ge=0)
    coverage_days:float=Field(7,gt=0)
    pack_size:int=Field(1,ge=1,strict=True)
    minimum_order:int=Field(0,ge=0,strict=True)

@app.post('/inventory/scenario')
def scenario(inputs:Scenario):
    try:
        result=order_policy(**inputs.model_dump())
        if any(isinstance(v,float) and not math.isfinite(v) for v in result.values()):
            raise ValueError('Inputs exceed supported numeric range')
        return result
    except (ValueError,OverflowError) as exc: raise HTTPException(422,str(exc)) from exc
