import pandas as pd
import pdb
from cProfile import Profile

def fn():
    path = '/home/cxh/Works/000905cons.csv'
    df = pd.read_csv(path, dtype={'成分券代码Constituent Code': str})
    #subscribe_tickers = df['成分券代码Constituent Code'].values.astype(str)
    #subscribe_tickers = ['000008', '000009']
    subscribe_tickers = ['002387', '002920', '300253', '600884', '600338', '000012', '002019',
           '002127', '603650', '600859', '600649', '300459', '300113', '300496']


    # 删文件夹========================================================================
    import shutil
    import os, sys, time
    #from tqdm.autonotebook import tqdm
    from fastprogress.fastprogress import progress_bar
    sys.path.append('/home/cxh/Works/TradeWorks/AlgoTrade/')


    # Queue========================================================================
    from algotrade.queue import sim_queue
    eq = sim_queue.SimQueue()

    # Signals========================================================================
    start_date = None #'2019-08-01 10:45:00'
    end_date = None #'2019-12-20 14:15:00'
    date = '20200601'
    data_path = '/mnt/ssd/XSHG_XSHE/'
    store_path='/home/cxh/Works/TradeWorks/AlgoTrade/output/%s' %date
    # for i in os.listdir(store_path):
    #     path = os.path.join(store_path, i)
    #     for j in os.listdir(path):
    #         os.remove(os.path.join(path, j))



    subscribe_fields={"TAQ":['BuyPrice01', 'SellPrice01', 'BuyVolume01', 'SellVolume01', 'TotalBuyOrderVolume', 'TotalSellOrderVolume', 'WtAvgSellPrice',
                     'WtAvgBuyPrice'],
                     "TRADE":["ActiveBuy", "ActiveSell"]}

    init_position = {}
    for i in subscribe_tickers:
        init_position[i] = {'持仓':10000, '可用':10000, '上限':10000}
        
    # TickHandler========================================================================
    from algotrade.tick_handler import tick_handler
    tickObj = tick_handler.TickHandler(csv_dir=data_path, date=date, events_queue=eq,
                                store_path=store_path, subscribe_tickers=subscribe_tickers, 
                                subscribe_fields=subscribe_fields)


    # PositionHandler========================================================================
    from algotrade.position_handler import position_handler
    posObj = position_handler.PositionHandler(tick_handler=tickObj, init_position=init_position,
                               store_path=store_path)


    # ========================================================================
    from algotrade.algo_handler import algo
    algo = algo.Algo(eq, posObj, subscribe_fields=subscribe_fields,
                                store_path=store_path)


    # ========================================================================
    from algotrade.order_handler import order_handler
    orderObj = order_handler.OrderHandler(eq, tick_handler=tickObj, 
                                                position_handler=posObj,
                                                limit_position=init_position,
                                                store_path=store_path)

    # ========================================================================
    from algotrade.execution_handler import sim_exec_handler
    seObj = sim_exec_handler.SimExecHandler(eq, tickObj, store_path=store_path)



    #algo.load_model('/home/cxh/Works/TradeWorks/AlgoTrade/data/20200601/reg_model.joblib')
    # ========================================================================
    eq.register('TICK', algo)
    eq.register('ALGO', orderObj)
    eq.register('ORDER', seObj)
    eq.register('FILL', posObj)

    # ========================================================================
    for i in tickObj.get_all_timestamp()[:450]:
        tickObj.update_tick()
        eq.run()

    tickObj.store()
    eq.store('TICK', algo)
    eq.store('ALGO', orderObj)
    eq.store('ORDER', seObj)
    eq.store('FILL', posObj)
    # ========================================================================
    eq.unregister('TICK', algo)
    eq.unregister('ALGO', orderObj)
    eq.unregister('ORDER', seObj)
    eq.unregister('FILL', posObj)


    # ========================================================================
    from algotrade.statistics import benchmark 
    b = benchmark.Benchmark(account_path=store_path)
    b.run()
    # ========================================================================
    from algotrade.statistics import trades 
    b = trades.Trades(account_path=store_path)
    b.run()
    # ========================================================================
    from algotrade.statistics import profiling
    pro = profiling.Profiling(account_path=store_path, benchmark='equal_wgts_benchmark')
    pro.run()
fn()

# prof = Profile()
# prof.enable()
# fn()
# prof.create_stats()
# #prof.print_stats()

# from pstats import Stats
# stats = Stats(prof)
# #stats.strp_dirs()
# stats.sort_stats('cumulative')
# stats.print_stats(20)
#stats.print_callers()


