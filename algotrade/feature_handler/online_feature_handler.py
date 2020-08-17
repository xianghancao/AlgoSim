import os
import numpy as np
import pandas as pd
from numba import jit

from ..utils.log import logger
log = logger('[OnlineFeatureHandler]')
from .operators import *
from .base import FeatureHandler
from ..event import FeatureEvent
    
class OnlineFeatureHandler(FeatureHandler):
    def __init__(self, events_queue, subscribe_fields, store_path):
        self.look_back = 120
        self.store_path = store_path
        self.events_queue = events_queue
        self.subscribe_fields = subscribe_fields['TAQ'] + subscribe_fields['TRADE']
        self.tick_data = {}
        
        super().__init__()
        self._init_TickFrame()
        self._init_history_feature()
        
        
    def _calculate_X(self, BuyVolume01, SellVolume01, BuyPrice01, SellPrice01,
                    TotalBuyOrderVolume, TotalSellOrderVolume, ActiveBuy, ActiveSell,
                    WtAvgSellPrice, WtAvgBuyPrice, ticker_names, timeindex): 
        """
        计算特征矩阵X
        """
        log.info('calculate_X ...')
        feature_dict, self.feature_dict = {}, {}
        feature_dict['f1'] = (BuyVolume01 - SellVolume01)/(BuyVolume01 + SellVolume01)
        feature_dict['f3'] = ts_rank_m(feature_dict['f1'], 3)
        feature_dict['f4'] = diff_m(rank_m(feature_dict['f1']), 3)
        feature_dict['f5'] = diff_m(feature_dict['f1'], 3)
        feature_dict['f6'] = (TotalBuyOrderVolume - TotalSellOrderVolume)/(TotalBuyOrderVolume + TotalSellOrderVolume)
        feature_dict['f7'] = diff_m(feature_dict['f6'], 10)
        feature_dict['f8'] = diff_m(rank_m(feature_dict['f6']), 10)
        feature_dict['f9'] = ts_rank_m(feature_dict['f6'], 20)

        BuyPrice01[BuyPrice01==0] =  SellPrice01[BuyPrice01==0] - 0.01
        SellPrice01[SellPrice01==0] =  BuyPrice01[SellPrice01==0] + 0.01
        mid_price = (BuyPrice01 + SellPrice01)/2
        ret_6 = mid_price/delay_m(mid_price, 2) -1
        ret_60 = mid_price/delay_m(mid_price,20)-1
        ret_120 = mid_price/delay_m(mid_price,40) -1

        feature_dict['f10'] = ret_120
        feature_dict['f11'] = rank_m(ret_120)
        feature_dict['f12'] = rank_m(ret_60)
        feature_dict['f14'] = ret_6
        feature_dict['f15'] = rank_m(ret_6)
        feature_dict['f16'] = ts_rank_m(ret_6, 40)
        
        active_bs_imbalance120 = (ts_sum_m(ActiveBuy, 40) - ts_sum_m(ActiveSell, 40))/(ts_sum_m(ActiveBuy, 40) + ts_sum_m(ActiveSell, 40))
        active_bs_imbalance60 = (ts_sum_m(ActiveBuy, 20) - ts_sum_m(ActiveSell, 20))/(ts_sum_m(ActiveBuy, 20) + ts_sum_m(ActiveSell, 20))
        active_bs_imbalance30 = (ts_sum_m(ActiveBuy, 10) - ts_sum_m(ActiveSell, 10))/(ts_sum_m(ActiveBuy, 10) + ts_sum_m(ActiveSell, 10))
        
        feature_dict['f17'] = active_bs_imbalance120
        feature_dict['f18'] = ts_rank_m(feature_dict['f17'], 3)
        feature_dict['f19'] = ts_rank_m(active_bs_imbalance60, 20)
        feature_dict['f20'] = active_bs_imbalance30
        feature_dict['f21'] = diff_m(feature_dict['f20'], 10)
        feature_dict['f22'] = ts_rank_m(feature_dict['f20'], 20)
        feature_dict['f23'] = diff_m(feature_dict['f20'], 3)
        feature_dict['f24'] = diff_m(rank_m(feature_dict['f20']), 20)
        feature_dict['f25'] = diff_m(rank_m(feature_dict['f20']), 3)

        price_imbalance = (WtAvgSellPrice - mid_price)/(WtAvgSellPrice-WtAvgBuyPrice)
        feature_dict['f26'] = diff_m(price_imbalance, 10)
        feature_dict['f27'] = rank_m(price_imbalance)
        feature_dict['f28'] = diff_m(rank_m(price_imbalance), 20)
        feature_dict['f29'] = diff_m(price_imbalance, 3)


        for i in feature_dict:
            self.feature_dict[i] = feature_dict[i][-1]
        return
        
        
    def _update_event(self, event):
        algo_event = FeatureEvent(timestamp=self.timestamp,
                                  ticker_names=self.ticker_names,
                                  feature_dict=self.feature_dict)
        self.events_queue.put(algo_event)
        return 
    
    

    def _init_TickFrame(self):
        for field in self.subscribe_fields:
            self.tick_data[field] = pd.DataFrame()
        self.tick_data['timeindex'] = []
        return
        
    def _init_history_feature(self):
        self.history_feature = {}
        for i in range(1, 30):
            self.history_feature['f%s' %i] = pd.DataFrame()
        self.history_y = pd.DataFrame()
        return
    
    def _update_history_feature(self):
        for i in self.feature_dict:
            self.history_feature[i] = self.history_feature[i].append(pd.DataFrame(self.feature_dict[i],
                                                                                 index=self.ticker_names,
                                                                                 columns=[self.timestamp]).T)
        return
        
    
    def _update_TickFrame(self, event):
        log.info('update TickFrame')
        self.tick_data['timeindex'].append(event.timestamp)

        for field in self.subscribe_fields:
            df = pd.DataFrame(event.field_dict[field], index=[event.timestamp])
            self.tick_data[field] = self.tick_data[field].append(df)
            setattr(self, field, self.tick_data[field].iloc[-self.look_back:].values)
        self.timeindex = self.tick_data['timeindex']
        return


        
    # 外部调用 ----------------------------------------------------------------------------
    def on_tick(self, event):
        if event.event_type == "TICK": 
            self._update_timestamp(event)
            self._update_ticker_names(event)
            self._update_TickFrame(event)
            if len(self.tick_data['timeindex']) >= self.look_back:
                self._calculate_X(self.BuyVolume01, self.SellVolume01, self.BuyPrice01, self.SellPrice01,
                        self.TotalBuyOrderVolume, self.TotalSellOrderVolume, self.ActiveBuy, self.ActiveSell,
                        self.WtAvgSellPrice, self.WtAvgBuyPrice, self.ticker_names, self.timeindex)
                self._update_event(event)
                self._update_history_feature()
        return     
        

    def store(self):
        log.info('store ...')
        store_path = os.path.join(self.store_path, 'feature')
        if not os.path.exists(store_path):
            os.mkdir(store_path)
        for i in self.history_feature:
            self.history_feature[i].to_csv(os.path.join(store_path, '%s.csv' %i))