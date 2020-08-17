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
        X = np.vstack((event.feature_dict['f1'], event.feature_dict['f3'], event.feature_dict['f4'], event.feature_dict['f5'], event.feature_dict['f6'], event.feature_dict['f7'], event.feature_dict['f8'], event.feature_dict['f9'], 
            event.feature_dict['f10'], event.feature_dict['f11'], event.feature_dict['f12'], event.feature_dict['f14'], event.feature_dict['f15'], event.feature_dict['f16'], event.feature_dict['f17'], event.feature_dict['f18'],
            event.feature_dict['f19'], event.feature_dict['f20'], event.feature_dict['f21'], event.feature_dict['f22'], event.feature_dict['f23'], event.feature_dict['f24'], event.feature_dict['f25'], event.feature_dict['f26'], event.feature_dict['f27'],
            event.feature_dict['f28'], event.feature_dict['f29'])).T

        pd.DataFrame(X).fillna(0, inplace=True)
        X[np.isinf(X)] = 0
        features_coe = [0.0003017452307439870, 5.53970994851047E-05, 0.0005772662234802970, -0.0005982384982235760, 6.44450900108092E-05, 0.016629428138884900, -0.015176484798513600, 0.0001520485675084980, 0.051223408768408900, -0.09429230975514690, -0.020789704549452400, 2.28532542860932, -2.4009240222880700, 0.0001507781961141350, 0.00015427538623097100, 5.20781640142478E-05, 8.23842890588953E-05, 0.00018044525542249000, -8.58934712926328E-05, 0.00010518879362590100, 0.0008509351047675170, -7.24624401413996E-05, -0.0008567182746997160, 0.0036142288152125800, 0.0002190817146477710, 0.004608530879051720, 0.007786741865566570]

        y = X * np.array(features_coe)
        self.predict_y = np.nansum(y, axis=1)
        return
    
    
    def update_event(self):
        model_event = ModelEvent(timestamp=self.timestamp,
                                  ticker_names=self.ticker_names,
                                  predict_y=self.predict_y)
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

        



