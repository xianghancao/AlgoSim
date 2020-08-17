import pandas as pd
import pdb
from cProfile import Profile
import shutil
import os, sys, time
from fastprogress.fastprogress import progress_bar
sys.path.append('/home/cxh/Works/AlgoTrade/')

from algotrade.utils import utils
    
    
# 参数 ========================================================================
import numpy as np
path = '/home/cxh/Works/000905closeweight.csv'
df = pd.read_csv(path, dtype={'成分券代码Constituent Code': str, '权重(%)Weight(%)':float})
df.index = df['成分券代码Constituent Code']
subscribe_tickers = df['成分券代码Constituent Code'].values.astype(str).tolist()
#subscribe_tickers = ['000008', '600167', '600195','600216']
data_path = '/mnt/ssd/XSHG_XSHE/'

subscribe_fields={"TAQ":['BuyPrice01', 'SellPrice01', 'BuyVolume01', 'SellVolume01', 'TotalBuyOrderVolume', 'TotalSellOrderVolume', 'WtAvgSellPrice',
                 'WtAvgBuyPrice'],
                 "TRADE":["ActiveBuy", "ActiveSell"]}

price = pd.read_csv('/home/cxh/Works/2020-07-31_close_price.csv', index_col=0).iloc[0]
pos = ((df['权重(%)Weight(%)'] * 0.01 * 100000000/(price * 100)).astype(np.int) * 100).to_dict()
init_position = {}
for i in pos:
    init_position[i] = {'基准持仓':pos[i],'持仓':pos[i], '可用':pos[i], '上限':pos[i]}

init_cash = 20000000





class Fn():
    def __init__(self, date, store_path):
        self.store_path=store_path

        utils.make_dirs(self.store_path)
        self.date = date


    def backtest(self):
        from algotrade.engine import queue, timeindex
        from algotrade.tick_handler import online_handler, offline_handler
        from algotrade.feature_handler import online_feature_handler, offline_feature_handler
        from algotrade.model_handler import online_model_handler, offline_model_handler
        from algotrade.position_handler import position_handler
        from algotrade.algo_handler import online_algo_handler_cxh
        from algotrade.order_handler import order_handler
        from algotrade.execution_handler import sim_exec_handler

        # Queue========================================================================
        eq = queue.EventQueue()
        timeObj = timeindex.TimeIndex(eq, date=self.date, store_path=self.store_path)    
        # TickHandler========================================================================
#         tickObj = online_handler.OnlineTickHandler(csv_dir=data_path, date=self.date, events_queue=eq,
#                                     store_path=self.store_path, subscribe_tickers=subscribe_tickers, 
#                                     subscribe_fields=subscribe_fields)

        tickObj = offline_handler.OfflineTickHandler(off_path=self.store_path, date=self.date, events_queue=eq,
                                    subscribe_tickers=subscribe_tickers, subscribe_fields=subscribe_fields)


        # FeatureHandler========================================================================

#         featureObj = online_feature_handler.OnlineFeatureHandler(eq, subscribe_fields=subscribe_fields,
#                                                          store_path=self.store_path)
            
        featureObj = offline_feature_handler.OfflineFeatureHandler(eq, subscribe_fields=subscribe_fields,
                                                                 off_path=self.store_path)

#         # ModelHandler========================================================================

        modelObj = online_model_handler.OnlineModelHandler(eq, store_path=self.store_path)
#         #modelObj = offline_model_handler.OfflineModelHandler(eq, off_path=self.store_path)

        
# #         # PositionHandler========================================================================

        posObj = position_handler.PositionHandler(tick_handler=tickObj, init_position=init_position,
                                  init_cash=init_cash, store_path=self.store_path)


# #         #         # ========================================================================

        algoObj = online_algo_handler_cxh.OnlineAlgoHandler(eq, posObj, tick_handler=tickObj, store_path=self.store_path)
        


# # # #         # ========================================================================

        orderObj = order_handler.OrderHandler(eq, tick_handler=tickObj, 
                                                        position_handler=posObj,
                                                        limit_position=init_position,
                                                        store_path=self.store_path)

# # # #         # ========================================================================

        execObj = sim_exec_handler.SimExecHandler(eq, tickObj, store_path=self.store_path)




        # ========================================================================
        eq.register('TIME', tickObj)
        eq.register('TIME', featureObj)
        eq.register('FEATURE', modelObj)
        eq.register('MODEL', algoObj)
        eq.register('ALGO', orderObj)
        eq.register('ORDER', execObj)
        eq.register('FILL', posObj)
    
        # ========================================================================
        for i in timeObj.get_all_timestamp():
            timeObj.update_timeindex()
            eq.run()

        #timeObj.store()
        #tickObj.store()
        
        #featureObj.store()
        modelObj.store()
        algoObj.store()
        posObj.store()
        orderObj.store()
        execObj.store()

        

#         # ========================================================================
        eq.unregister('TIME', tickObj)
        eq.unregister('TIME', featureObj)
        eq.unregister('FEATURE', modelObj)
        eq.unregister('MODEL', algoObj)
        eq.unregister('ALGO', orderObj)
        eq.unregister('ORDER', execObj)
        eq.unregister('FILL', posObj)

        
    def profile(self):
#         # ========================================================================
        from algotrade.statistics import trades
        b = trades.Trades(account_path=self.store_path)
        b.run()
#         # ========================================================================
        from algotrade.statistics import profiling
        pro = profiling.Profiling(account_path=self.store_path, benchmark='equal_wgts_benchmark')
        pro.run()



fn = Fn('20200604', store_path='/home/cxh/Works/AlgoTrade/store/20200604')
fn.backtest()
fn.profile()

