import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from pipeline import features, audit, metrics, partition
from inventory import reorder_scenario


class ForecastContracts(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame({'dteday': pd.date_range('2020-01-01', periods=80), 'cnt': np.arange(80), 'casual': np.arange(80), 'registered': np.zeros(80)})

    def test_future_target_changes_do_not_change_earlier_features(self):
        original = features(self.data)
        changed = self.data.copy()
        changed.loc[60:, 'cnt'] = 9999
        modified = features(changed)
        pd.testing.assert_frame_equal(original.loc[original.dteday <= self.data.dteday[60]].drop(columns='cnt'), modified.loc[modified.dteday <= self.data.dteday[60]].drop(columns='cnt'))
        row = original.loc[original.dteday.eq(self.data.dteday[50])].iloc[0]
        self.assertEqual(row.lag_1, 49)
        self.assertEqual(row.lag_7, 43)
        self.assertEqual(row.rolling_mean_7, np.mean(np.arange(43,50)))

    def test_split_windows_are_disjoint_and_ordered(self):
        parts = partition(features(self.data))
        train, val, test = [parts[parts.split.eq(s)] for s in ['train','validation','test']]
        self.assertLess(train.dteday.max(), val.dteday.min())
        self.assertLess(val.dteday.max(), test.dteday.min())

    def test_rejects_calendar_gap_and_duplicate_dates(self):
        with self.assertRaises(ValueError): audit(self.data.drop(index=30))
        with self.assertRaises(ValueError): audit(pd.concat([self.data,self.data.iloc[[1]]]))

    def test_metrics_against_hand_calculation_and_zero_actuals(self):
        result = metrics([1,3],[2,1])
        self.assertEqual(result['MAE'],1.5)
        self.assertAlmostEqual(result['RMSE'],np.sqrt(2.5))
        self.assertEqual(result['WAPE_percent'],75)
        self.assertEqual(result['bias_forecast_minus_actual'],-.5)
        self.assertIsNone(metrics([0,0],[0,1])['WAPE_percent'])

    def test_inventory_explicit_scenario_and_invalid_inputs(self):
        r = reorder_scenario(10,2,4,1.65,20)
        self.assertAlmostEqual(r['reorder_point'],46.6)
        self.assertAlmostEqual(r['gap_to_reorder_point'],26.6)
        with self.assertRaises(ValueError): reorder_scenario(10,-1,4,1.65,20)


if __name__ == '__main__': unittest.main()
