import copy
import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from inventory import order_policy
from plan_inventory import build_plan


class InventoryContracts(unittest.TestCase):
    def test_hand_calculated_order_rounding_and_position(self):
        # s=46.6; S=70+1.65*2*sqrt(7)=78.731..., position=15.
        r = order_policy(10, 2, 4, 1.65, 20, 5, 10, 3, 12, 24)
        self.assertAlmostEqual(r['reorder_point'], 46.6)
        self.assertEqual(r['inventory_position'], 15)
        self.assertEqual(r['suggested_order_units'], 72)
        self.assertGreaterEqual(r['post_order_inventory_position'], r['order_up_to_units'])

    def test_no_order_above_trigger_and_minimum_pack_constraints(self):
        self.assertEqual(order_policy(10, 0, 2, 0, 100)['suggested_order_units'], 0)
        self.assertEqual(order_policy(1, 0, 1, 0, 1, coverage_days=1,
                                     pack_size=12, minimum_order=25)['suggested_order_units'], 36)
        self.assertEqual(order_policy(0, 0, 0, 0, 0)['suggested_order_units'], 0)
        self.assertEqual(order_policy(10, 0, 1, 0, 0, backorders=20)['suggested_order_units'], 100)

    def test_invalid_policy_inputs(self):
        for kwargs in [{'pack_size': 0}, {'pack_size': True}, {'minimum_order': 2.5},
                       {'coverage_days': 0}, {'lead_days': -1}, {'stock': float('nan')}]:
            base = dict(mean_daily=10, std_daily=2, lead_days=3, z_score=1.65, stock=10)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                order_policy(**{**base, **kwargs})

    def fixture(self):
        history = pd.DataFrame({'date': pd.date_range('2011-01-01', periods=28),
                                'product_id': 'A', 'units': 10.})
        config = dict(scenario_only=True, assumption_note='Invented test input',
                      as_of='2011-01-28', lookback_days=28, lead_days=3,
                      z_score=1.645, coverage_days=7, pack_size=12, minimum_order=24,
                      products=[dict(product_id='A', stock=0, on_order=0, backorders=0)])
        return history, config

    def test_snapshot_uses_only_past_data(self):
        h, c = self.fixture()
        a = build_plan(h, c)
        future = pd.DataFrame({'date': [pd.Timestamp('2011-01-29')], 'product_id': ['A'], 'units': [99999.]})
        pd.testing.assert_frame_equal(a, build_plan(pd.concat([h, future]), c))
        self.assertEqual(a.suggested_order_units.iloc[0], 108)

    def test_missing_history_stock_or_assumption_fails(self):
        h, c = self.fixture()
        with self.assertRaises(ValueError): build_plan(h.drop(index=2), c)
        with self.assertRaises(ValueError): build_plan(pd.concat([h, h.iloc[[0]]]), c)
        for change in [{'scenario_only': False}, {'products': []}, {'assumption_note': ''}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                build_plan(h, {**c, **change})
        bad = copy.deepcopy(c)
        del bad['products'][0]['stock']
        with self.assertRaises(KeyError): build_plan(h, bad)


if __name__ == '__main__':
    unittest.main()
