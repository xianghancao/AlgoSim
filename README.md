
## 2. 概况

## 2.1 Event

| 事件           | 模块  | 描述 |
| -------------: | -----------: | :------------- |
| TickEvent      | price_handler | 生成价格事件 |
| AlgoEvent | algo_handler   | 生成算法事件 |
| OrderEvent | order_handler | 生成订单事件 |
| FillEvent | execution_handler | 负责回测和实盘 |
| PositionEvent    | position_handler     | 更新持仓和账簿 |
|  | statistics | 统计基准，PNL等 |
|  | utils | 包括日志，解析价格，performance等功能 |
|  | queue | 负责队列 |


## Handler
### tick_handler
### order_handler
### execution_handler
### position_handler

```python
import os, sys, time
sys.path.append('/your_path/AlgoLearn/')
subscribe_tickers = ['000008', '600167', '600195','600216']
subscribe_fields={"TAQ":['BuyPrice01', 'SellPrice01', 'BuyVolume01', 'SellVolume01', 'TotalBuyOrderVolume', 'TotalSellOrderVolume', 'WtAvgSellPrice',
                 'WtAvgBuyPrice'],
                 "TRADE":["ActiveBuy", "ActiveSell"]}

init_position = {}
for i in subscribe_tickers:
    init_position[i] = {'基准持仓':1000,'持仓':1000, '可用':1000, '上限':1000}

init_cash = 20000000



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
tickObj = online_handler.OnlineTickHandler(csv_dir=data_path, 
                                        date=self.date, 
                                        events_queue=eq,
                                        store_path=self.store_path, 
                                        subscribe_tickers=subscribe_tickers, 
                                        subscribe_fields=subscribe_fields)

# tickObj = offline_handler.OfflineTickHandler(off_path=self.store_path, date=self.date, events_queue=eq,
#                             subscribe_tickers=subscribe_tickers, subscribe_fields=subscribe_fields)


# FeatureHandler========================================================================

featureObj = online_feature_handler.OnlineFeatureHandler(eq, 
                                                         feature_name_list=['f1', 'f3'],
                                                         subscribe_fields=subscribe_fields,
                                                        store_path=self.store_path)
    
#         featureObj = offline_feature_handler.OfflineFeatureHandler(eq,
                                                        # subscribe_fields=subscribe_fields,
#                                                                  off_path=self.store_path)

#ModelHandler========================================================================
modelObj = online_model_handler.OnlineModelHandler(eq, 
                                                store_path=self.store_path)
#         modelObj = offline_model_handler.OfflineModelHandler(eq, off_path=self.store_path)


#PositionHandler========================================================================

posObj = position_handler.PositionHandler(tick_handler=tickObj, init_position=init_position,
                          init_cash=init_cash, store_path=self.store_path)


# ========================================================================

algoObj = online_algo_handler_cxh.OnlineAlgoHandler(eq, 
                                                posObj, 
                                                tick_handler=tickObj, 
                                                store_path=self.store_path)



# ========================================================================

orderObj = order_handler.OrderHandler(eq, tick_handler=tickObj, 
                                                position_handler=posObj,
                                                limit_position=init_position,
                                                store_path=self.store_path)

# ========================================================================

execObj = sim_exec_handler.SimExecHandler(eq,
                                         tickObj,
                                        store_path=self.store_path)




# ========================================================================
eq.register('TIME', tickObj)
eq.register('TICK', featureObj)
eq.register('FEATURE', modelObj)
eq.register('MODEL', algoObj)
eq.register('ALGO', orderObj)
eq.register('ORDER', execObj)
eq.register('FILL', posObj)

# ========================================================================
for i in timeObj.get_all_timestamp():
    timeObj.update_timeindex()
    eq.run()

timeObj.store()
tickObj.store()
featureObj.store()
modelObj.store()
algoObj.store()
posObj.store()
orderObj.store()
execObj.store()



# ========================================================================
eq.unregister('TIME', tickObj)
eq.unregister('TIME', featureObj)
eq.unregister('FEATURE', modelObj)
eq.unregister('MODEL', algoObj)
eq.unregister('ALGO', orderObj)
eq.unregister('ORDER', execObj)
eq.unregister('FILL', posObj)



# ========================================================================
from algotrade.statistics import trades
b = trades.Trades(account_path=self.store_path)
b.run()

# ========================================================================
from algotrade.statistics import profiling
pro = profiling.Profiling(account_path=self.store_path, benchmark='benchmark')
pro.run()


```