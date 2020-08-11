import os
import numpy as np
import pandas as pd


from .base import ModelHandler
from ..event import ModelEvent
from ..utils.log import logger
log = logger('[OnlineModelHandler]')

    
class OnlineModelHandler(ModelHandler):
    def __init__(self, events_queue, store_path):
        print('v0.0.2')
        self.store_path = store_path
        self.events_queue = events_queue
        super().__init__()
        self.history_predict_y = pd.DataFrame()
        
        
    def model(self, event):
        """
        在线预测
        """
        X = np.vstack((event.feature_dict['f1'], event.feature_dict['f2'], event.feature_dict['f3'], event.feature_dict['f4'], event.feature_dict['f5'], event.feature_dict['f6'], event.feature_dict['f7'], event.feature_dict['f8'], event.feature_dict['f9'], 
            event.feature_dict['f10'], event.feature_dict['f11'], event.feature_dict['f12'], event.feature_dict['f13'], event.feature_dict['f14'], event.feature_dict['f15'], event.feature_dict['f16'], event.feature_dict['f17'], event.feature_dict['f18'],
            event.feature_dict['f19'], event.feature_dict['f20'], event.feature_dict['f21'], event.feature_dict['f22'], event.feature_dict['f23'], event.feature_dict['f24'], event.feature_dict['f25'], event.feature_dict['f26'], event.feature_dict['f27'],
            event.feature_dict['f28'], event.feature_dict['f29'])).T

        pd.DataFrame(X).fillna(0, inplace=True)
        X[np.isinf(X)] = 0
        features_coe = [ 5.35669145e-04,  3.71151111e-04, -3.42312762e-04,  7.38368034e-05,
                        3.93802604e-04, -8.61703344e-04,  1.50958046e-03,  2.43364664e-02,
                       -6.44919510e-02, -3.32045972e-06,  1.13215474e-01, -2.16001574e-02,
                        8.51526346e-01,  7.55244644e-04,  2.51590559e+00, -1.75783442e+00,
                       -1.51718319e-04,  1.52544407e-04, -4.16282667e-06,  2.95180017e-05,
                       -1.51420440e-04,  2.45460560e-04,  1.21291153e-04, -8.15870422e-05,
                       -3.29896437e-05, -8.72056822e-05,  7.01080210e-02,  6.18569664e-03,
                        9.14276766e-02,  7.01804728e-02]
#         features_coe = [ 8.31264346e-04,  0, 8.96479941e-05,  6.82576828e-04, -7.85994274e-04,
#                         1.49442546e-04,  1.33546463e-02, -1.13962501e-02,  1.54540861e-04,
#                         1.44654527e-01, -1.72515318e-01,  6.33161738e-02,  0, 2.02167511e+00,
#                        -2.23140282e+00,  2.01106302e-04,  1.71409332e-04,  7.21477461e-05,
#                         9.53081738e-05,  2.77125044e-04, -1.04011687e-04,  1.25233311e-04,
#                         1.00856955e-03, -9.96475219e-05, -1.01525665e-03,  3.30604160e-03,
#                         3.35190917e-04,  7.75227626e-03,  1.32179441e-02]
        # features_coe = [0.000593972, 0, 7.42E-05, 0.000741643, -0.000797053, -3.61E-05, 0.008191945, -0.005073631, 0.000200604, 0.096722214, -0.128728383, -0.011528502, 0, 3.161629128, -3.36067329, 0.000275046, 0.000208558, 8.04E-05, 0.00012493, 0.000251887, -0.000129593, 0.000173111, 0.001160089, -0.000105772, -0.001165951, 0.005288762, 0.000470316, 0.007666061, 0.015196477]
        y = X * np.array(features_coe)
        self.predict_y = np.nansum(y, axis=1)
        return
    
    
    def update_event(self):
        model_event = ModelEvent(timestamp=self.timestamp,
                                  ticker_names=self.ticker_names,
                                  predict_y=self.predict_y.values)
        self.events_queue.put(model_event)
        return
        
    
    def update_history_predict_y(self):
        self.history_predict_y = self.history_predict_y.append(pd.DataFrame(self.predict_y, columns=[self.timestamp],
                                                                           index=self.ticker_names).T)
        

    def on_feature(self, event):
        if event.event_type == 'FEATURE':
            self._update_timestamp(event)
            self._update_ticker_names(event)
            self.model(event)
            self.update_event()
            self.update_history_predict_y()
            return
        
    def store(self):
        log.info('store ...')
        store_path = os.path.join(self.store_path, 'model')
        if not os.path.exists(store_path):
            os.mkdir(store_path)
        self.history_predict_y.to_csv(os.path.join(store_path, 'predict_y.csv'))

        



