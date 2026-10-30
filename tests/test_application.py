import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fastapi.testclient import TestClient
from api import app
from streamlit.testing.v1 import AppTest

class APIContracts(unittest.TestCase):
    def test_forecasts_and_rejected_requests(self):
        c=TestClient(app)
        self.assertEqual(len(c.get('/products').json()),5)
        result=c.get('/forecast/20725').json()
        self.assertEqual(result['date'],'2011-12-09')
        self.assertTrue(result['historical_only'])
        self.assertEqual(c.get('/forecast/unknown').status_code,404)
        self.assertEqual(c.get('/forecast/20725?horizon=7').status_code,422)

    def test_scenario_arithmetic_and_validation(self):
        c=TestClient(app)
        body=dict(mean_daily=10,std_daily=0,lead_days=3,z_score=1.645,stock=0,coverage_days=7,pack_size=12,minimum_order=24)
        result=c.post('/inventory/scenario',json=body)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['suggested_order_units'],108)
        self.assertEqual(c.post('/inventory/scenario',json={**body,'stock':-1}).status_code,422)
        self.assertEqual(c.post('/inventory/scenario',json={**body,'pack_size':1.5}).status_code,422)
        self.assertEqual(c.post('/inventory/scenario',json={**body,'secret':'x'}).status_code,422)

class DashboardFlow(unittest.TestCase):
    def test_product_forecast_and_inventory_interaction(self):
        app=AppTest.from_file(str(ROOT/'src/app.py'),default_timeout=40).run()
        self.assertFalse(app.exception)
        app.selectbox[0].select('22423').run()
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertIn('2011-12-09',app.success[0].value)
        app.number_input[0].set_value(0.0)
        app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertGreater(int(next(m for m in app.metric if m.label=='Illustrative order quantity').value),0)
        app.number_input[0].set_value(1000000.0)
        app.button[1].click().run()
        self.assertEqual(int(next(m for m in app.metric if m.label=='Illustrative order quantity').value),0)
