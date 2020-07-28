import pandas as pd
from cProfile import Profile
import shutil
import os, sys, time
from fastprogress.fastprogress import progress_bar
sys.path.append('/home/cxh/Works/TradeWorks/AlgoTrade/')
import pdb


def fn(date):
    path = '/home/cxh/Works/000905cons.csv'
    df = pd.read_csv(path, dtype={'成分券代码Constituent Code': str})
    subscribe_tickers = df['成分券代码Constituent Code'].values.astype(str)
    #subscribe_tickers = ['000008', '000009']
    # subscribe_tickers = ['002387', '002920', '300253', '600884', '600338', '000012', '002019',
    #        '002127', '603650', '600859', '600649', '300459', '300113', '300496',
    #        '002317', '300002', '600640', '600529', '601865']



    # 参数 ========================================================================
    data_path = '/mnt/ssd/XSHG_XSHE/'
    store_path='/mnt/ssd/AlgoTrade/data/%s' %date
    if not os.path.exists(store_path):
        os.mkdir(store_path)
    subscribe_fields={"TAQ":['BuyPrice01', 'SellPrice01', 'BuyVolume01', 'SellVolume01', 'TotalBuyOrderVolume', 'TotalSellOrderVolume', 'WtAvgSellPrice',
                     'WtAvgBuyPrice'],
                     "TRADE":["ActiveBuy", "ActiveSell"]}

    init_position = {}
    for i in subscribe_tickers:
        init_position[i] = {'持仓':1000, '可用':1000, '上限':1000}


    # Queue========================================================================
    from algotrade.queue import sim_queue
    eq = sim_queue.SimQueue()


    
    # TickHandler========================================================================
    from algotrade.tick_handler import tick_handler
    tickObj = tick_handler.TickHandler(csv_dir=data_path, date=date, events_queue=eq,
                                store_path=store_path, subscribe_tickers=subscribe_tickers, 
                                subscribe_fields=subscribe_fields)


    # PositionHandler========================================================================
    from algotrade.position_handler import position_handler
    posObj = position_handler.PositionHandler(tick_handler=tickObj, init_position=init_position,
                               store_path=store_path)


    # 算法=========================================================
    from algotrade.algo_handler import algo
    algo = algo.Algo(eq, posObj, subscribe_fields=subscribe_fields,
                                store_path=store_path)


    # 订单========================================================================
    from algotrade.order_handler import order_handler
    orderObj = order_handler.OrderHandler(eq, tick_handler=tickObj, 
                                                position_handler=posObj,
                                                limit_position=init_position,
                                                store_path=store_path)

    # 执行========================================================================
    from algotrade.execution_handler import sim_exec_handler
    seObj = sim_exec_handler.SimExecHandler(eq, tickObj, store_path=store_path)


    # 遍历 ========================================================================
    for i in tickObj.get_all_timestamp():
        tickObj.update_tick()
        eq.run()

    tickObj.store()


for date in os.listdir('/mnt/ssd/XSHG_XSHE/'):
    if date[:6] == '202005' and date not in os.listdir('/mnt/ssd/AlgoTrade/data/'):
        fn(date)
#fn('20200608')

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


