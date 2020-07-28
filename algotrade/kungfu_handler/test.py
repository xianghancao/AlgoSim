# -*- coding: UTF-8 -*-
import kungfu.yijinjing.time as kft
from kungfu.wingchun.constants import *

SOURCE = Source.XTP
ACCOUNT = "53191001689"
tickers = ["600000","600001"]
VOLUME = 200
EXCHANGE = Exchange.SSE

# 启动前回调，添加交易账户，订阅行情，策略初始化计算等
def pre_start(context):
    context.add_account(SOURCE, ACCOUNT, 100000.0)
    context.subscribe(SOURCE, tickers, EXCHANGE)
    context.subscribe("bar", tickers, EXCHANGE)
    context.ordered = False
# 启动准备工作完成后回调，策略只能在本函数回调以后才能进行获取持仓和报单
def post_start(context):
    context.log.warning("post_start")
    log_book(context,None)


# 收到快照行情时回调，行情信息通过quote对象获取
def on_quote(context, quote):
    context.log.info("[on_quote] {}".format(quote))
    if quote.instrument_id in tickers:
        # 如果没有报单则报单
        if not context.ordered:
            order_id = context.insert_order(quote.instrument_id, EXCHANGE, ACCOUNT, quote.last_price, VOLUME, PriceType.Limit, Side.Buy, Offset.Open)
            # order_id = context.insert_order(quote.instrument_id, EXCHANGE, ACCOUNT, quote.last_price, VOLUME, PriceType.Any, Side.Buy, Offset.Open)#上期所不支持市价单
            if order_id > 0:
                context.ordered = True
                context.log.info("[order] (rid){} (ticker){}".format(order_id, quote.instrument_id))
                # 通过添加时间回调，在三秒以后撤单
                context.add_timer(context.now() + 3 * 1000000000, lambda ctx, event: cancel_order(ctx, order_id))


# 收到订单状态回报时回调
def on_order(context, order):
    context.log.info("[on_order] {}".format(order))


# 收到成交信息回报时回调
def on_trade(context, trade):
    context.log.info("[on_trade] {}".format(trade))


# 策略释放资源前回调，仍然可以获取持仓和报单
def pre_stop(context):
    context.log.info("[befor strategy stop]")


# 策略释放资源后回调
def post_stop(context):
    context.log.info("[befor process stop]")


## 自定义函数
# 自定义持仓和资金日志输出函数
def log_book(context, event):
    context.log.warning("[avail]{}".format(context.book.asset.avail))
    context.log.warning("[acc_avail]{}".format(context.get_account_book(SOURCE, ACCOUNT).asset.avail))
    book = context.book
    asset = book.asset
    context.log.warning(
        "[strategy capital] (avail){} (margin){} (market_value){} (initial_equity){} (dynamic_equity){} (static_equity){} (realized_pnl){} (unrealized_pnl){}".format(
            asset.avail, asset.margin, asset.market_value, asset.initial_equity,
            asset.dynamic_equity, asset.static_equity, asset.realized_pnl, asset.unrealized_pnl))
    book = context.get_account_book(SOURCE, ACCOUNT)
    asset = book.asset
    context.log.warning(
        "[account capital] (avail){} (margin){} (market_value){} (initial_equity){} (dynamic_equity){} (static_equity){} (realized_pnl){} (unrealized_pnl){}".format(
            asset.avail, asset.margin, asset.market_value, asset.initial_equity,
            asset.dynamic_equity, asset.static_equity, asset.realized_pnl, asset.unrealized_pnl))
    context.logger.warning("acc_pos")
    for key in book.long_positions:
        log_stock_pos(context, book.long_positions[key])
    # log_future_pos(context, pos)
    context.logger.warning("str_pos")
    for key in context.book.long_positions:
        log_stock_pos(context, context.book.long_positions[key])
        # log_future_pos(context, pos)


# 自定义股票持仓数据日志输出函数
def log_stock_pos(context, pos):
    context.log.info(
        "(instrument_id){} (instrument_type){} (exchange_id){} (direction){} (volume){} (yesterday_volume){} (last_price){} (pre_close_price){} (close_price){} (avg_open_price){} (position_cost_price){} (realized_pnl){} (unrealized_pnl){} ".format(
            pos.instrument_id, pos.instrument_type, pos.exchange_id, pos.direction,
            pos.volume, pos.yesterday_volume, pos.last_price, pos.pre_close_price, pos.close_price, pos.avg_open_price,
            pos.position_cost_price, pos.realized_pnl, pos.unrealized_pnl))


# 自定义撤单回调函数
def cancel_order(context, order_id):
    action_id = context.cancel_order(order_id)
    if action_id > 0:
        context.log.info("[cancel order] (action_id){} (rid){} ".format(action_id, order_id))
