import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from retail_pipeline import make_features,forecast_next,NUMERIC,split_labels


class RetailContracts(unittest.TestCase):
    def history(self):
        return pd.DataFrame({'date':pd.date_range('2011-01-01',periods=60),'product_id':['A']*60,'units':np.arange(60)})

    def test_no_current_or_future_target_in_features(self):
        base=self.history()
        original=make_features(base)
        base.loc[40:,'units']=9999
        altered=make_features(base)
        cutoff=pd.Timestamp('2011-02-10')
        pd.testing.assert_frame_equal(original[original.date<=cutoff][NUMERIC],altered[altered.date<=cutoff][NUMERIC])

    def test_online_features_match_offline_feature_generation(self):
        h=self.history()
        class Capture:
            def predict(self,frame):
                self.frame=frame
                return np.array([1.])
        model=Capture()
        forecast_next(h,model,'random_forest_leaf_3')
        extra=pd.concat([h,pd.DataFrame({'date':[h.date.max()+pd.Timedelta(days=1)],'product_id':['A'],'units':[0]})],ignore_index=True)
        offline=make_features(extra).iloc[-1]
        np.testing.assert_allclose(model.frame[NUMERIC].iloc[0].astype(float),offline[NUMERIC].astype(float))

    def test_horizon_and_history_validation(self):
        h=self.history()
        result=forecast_next(h,None,'naive')
        self.assertEqual(result.forecast_units.iloc[0],59)
        self.assertEqual(result.date.iloc[0],pd.Timestamp('2011-03-02'))
        with self.assertRaises(ValueError): forecast_next(h.iloc[:10],None,'naive')
        with self.assertRaises(ValueError): forecast_next(h.drop(index=35),None,'naive')

    def test_same_validation_and_test_cutoffs_for_all_products(self):
        self.assertEqual(list(split_labels(pd.Series(pd.to_datetime(['2011-06-30','2011-07-01','2011-08-31','2011-09-01'])))),['train','validation','validation','test'])


if __name__=='__main__': unittest.main()
