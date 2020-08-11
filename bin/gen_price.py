import pandas as pd
import pdb
from cProfile import Profile
import shutil
import os, sys, time
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


        # Queue========================================================================
        eq = queue.EventQueue()
        
        timeObj = timeindex.TimeIndex(eq, date=self.date, store_path=self.store_path)    
        # TickHandler========================================================================
        tickObj = online_handler.OnlineTickHandler(csv_dir=data_path, date=self.date, events_queue=eq,
                                    store_path=self.store_path, subscribe_tickers=subscribe_tickers, 
                                    subscribe_fields=subscribe_fields)



        # ========================================================================
        eq.register('TIME', tickObj)

        # ========================================================================
        for i in timeObj.get_all_timestamp():
            timeObj.update_timeindex()
            eq.run()
            
        tickObj.store()
        


#         # ========================================================================
        eq.unregister('TIME', tickObj)




for date in os.listdir('/mnt/ssd/XSHG_XSHE/'):
    if (date[:6] == '202004' and not os.path.exists('/mnt/ssd/AlgoTrade/store/%s/' %date)): #or \
    #(date[:6] == '202004' and len(os.listdir('/mnt/ssd/AlgoTrade/store/%s/price/' %date))==0):
        print(date)
        store_path = '/home/cxh/Works/SSD/AlgoTrade/store/%s' %date
        utils.make_dirs(os.path.join(store_path, 'price'))
        print(date, store_path)
        fn = Fn(date, store_path)
        fn.backtest()


