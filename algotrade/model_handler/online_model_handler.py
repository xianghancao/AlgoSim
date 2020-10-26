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
        X = np.vstack((event.feature_dict['f1'], event.feature_dict['f3'])).T

        pd.DataFrame(X).fillna(0, inplace=True)
        X[np.isinf(X)] = 0
        features_coe = [0.0002995517899696350, 5.45638371777303E-05]

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

        



