import pandas as pd
import numpy as np
import pdb
from cProfile import Profile
import shutil
import os, sys, time
#from tqdm.autonotebook import tqdm
from fastprogress.fastprogress import progress_bar
sys.path.append('/home/cxh/Works/AlgoTrade/')

from algotrade.utils import utils
    
    
# 参数 ========================================================================
path = '/home/cxh/Works/000905cons.csv'
df = pd.read_csv(path, dtype={'成分券代码Constituent Code': str})
subscribe_tickers = df['成分券代码Constituent Code'].values.astype(str).tolist()
data_path = '/mnt/ssd/XSHG_XSHE/'

subscribe_fields={"TAQ":['BuyPrice01', 'SellPrice01', 'BuyVolume01', 'SellVolume01', 'TotalBuyOrderVolume', 'TotalSellOrderVolume', 'WtAvgSellPrice',
                 'WtAvgBuyPrice'],
                 "TRADE":["ActiveBuy", "ActiveSell"]}





class Fn():
    def __init__(self, date, store_path):
        self.store_path=store_path

        utils.make_dirs(self.store_path)
        self.date = date


    def backtest(self):
        from algotrade.engine import queue, timeindex
        from algotrade.tick_handler import online_handler, offline_handler
        from algotrade.feature_handler import online_feature_handler, offline_feature_handler

        # Queue========================================================================
        eq = queue.EventQueue()
        timeObj = timeindex.TimeIndex(eq, date=self.date, store_path=self.store_path)    
        # TickHandler========================================================================

        tickObj = offline_handler.OfflineTickHandler(off_path=self.store_path, date=self.date, events_queue=eq,
                                    subscribe_tickers=subscribe_tickers, subscribe_fields=subscribe_fields)


        # FeatureHandler========================================================================

        featureObj = online_feature_handler.OnlineFeatureHandler(eq, subscribe_fields=subscribe_fields,
                                                         store_path=self.store_path)
            


        # ========================================================================
        eq.register('TIME', tickObj)
        eq.register('TICK', featureObj)

    
        # ========================================================================
        for i in timeObj.get_all_timestamp():
            timeObj.update_timeindex()
            eq.run()
        
        featureObj.store()

        

#         # ========================================================================
        eq.unregister('TIME', tickObj)
        eq.unregister('TICK', featureObj)



for date in np.sort(os.listdir('/mnt/ssd/AlgoTrade/store/')):
    if date[:6] == '202006' and not os.path.exists('/mnt/ssd/AlgoTrade/store/%s/feature' %date):
        utils.make_dirs('/mnt/ssd/AlgoTrade/store/%s/feature/' %date)
        store_path = '/home/cxh/Works/SSD/AlgoTrade/store/%s' %date
        fn = Fn(date, store_path)
        fn.backtest()
