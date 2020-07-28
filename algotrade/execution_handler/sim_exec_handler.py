import os
import numpy as np 
import pandas as pd
import yaml

#from .base import ExecutionHandler
from ..event import FillEvent

from ..utils.log import logger

log = logger('[SimExecHandler]')

def cal_amount(quantity, fill_price):
    """
    成交额
    """
    amount = quantity * fill_price
    return amount


def cal_commission_fee(quantity, fill_price, action):
    """
    股票交易手续费分三部分：印花税、过户费、证券监管费。
    券商交易佣金：最高为成交金额的3‰，最低5元起，单笔交易佣金不满5元按5元收取。
    """
    amount = quantity * fill_price
    fee = max(amount*0.0003, 5) 
    return round(fee, 2)


def cal_stamp_tax(quantity, fill_price, action):
    """
    印花税：成交金额的千1，向卖方单边征收
    """
    amount = quantity * fill_price
    if action == '卖':
        fee = amount*0.001
    else:
        fee = 0
    return round(fee, 2)


def cal_transfer_fee(quantity, fill_price, action):
    """
    过户费：从2015年8月1日起已经更改为上海和深圳都进行收取，按成交金额的0.002%收取
    """
    amount = quantity * fill_price
    if action == '卖':
        fee = amount*0.00002
    else:
        fee = 0
    return round(fee, 2)


class SimExecHandler():
    """
    模拟交易，将所有订单转换成实际订单，而不考虑延迟，滑点和成交率等问题。

    更精细的交易模型，或者下单算法可以考虑取代本Handler。

    1. 处理OrderEvent
    2. 查询最新价格
    2. 默认所有OrderEvent都能够按照最新价格成交，并生成FillEvent

    """

    def __init__(self, events_queue, tick_handler, store_path):
        """
        """
        self.events_queue = events_queue
        self.tick_handler = tick_handler
        self.exchange = "Sim"
        self.store_path = store_path
        self.fill_quantity_df = pd.DataFrame()
        self.fill_price_df = pd.DataFrame()
        self.fill_fee_df = pd.DataFrame()
        self.history_fill_dict = {}

    def on_order(self, event):
        if event.event_type == 'ORDER':
            # 查询最新价格
            self.sell_price_01 = self.tick_handler.get_sell_price_01()
            self.buy_price_01 = self.tick_handler.get_buy_price_01()
            self.timestamp = self.tick_handler.get_last_timestamp()
            # 生成FillEvent
            self.gen_fill_event(event)
            self._update_fill()
            #self.store()

    def gen_fill_event(self, event):
        exchange = self.exchange
        self.fill_dict = {}
        for i in event.order_dict:
            self.fill_dict[i] = {}
            self.fill_dict[i]['证券代码'] = i
            self.fill_dict[i]['成交状态'] = "成交"
            self.fill_dict[i]['成交日期'] = self.timestamp
            self.fill_dict[i]['买卖方向'] = event.order_dict[i]['买卖方向']
            self.fill_dict[i]['交易所'] = self.exchange
            if self.fill_dict[i]['买卖方向'] == '买':
                self.fill_dict[i]['成交价格'] = event.order_dict[i]['委托价格']
            elif self.fill_dict[i]['买卖方向'] == '卖':
                self.fill_dict[i]['成交价格'] = event.order_dict[i]['委托价格']
            self.fill_dict[i]['成交数量'] = event.order_dict[i]['委托数量']
            self.fill_dict[i]['成交额'] = cal_amount(self.fill_dict[i]['成交数量'],
                                                            self.fill_dict[i]['成交价格'])
            self.fill_dict[i]['佣金'] = cal_commission_fee(self.fill_dict[i]['成交数量'],
                                                                self.fill_dict[i]['成交价格'],
                                                                self.fill_dict[i]['买卖方向'])
            self.fill_dict[i]['印花税'] = cal_stamp_tax(self.fill_dict[i]['成交数量'],
                                                            self.fill_dict[i]['成交价格'],
                                                            self.fill_dict[i]['买卖方向'])
            self.fill_dict[i]['过户费'] = cal_transfer_fee(self.fill_dict[i]['成交数量'],
                                                                self.fill_dict[i]['成交价格'],
                                                                self.fill_dict[i]['买卖方向'])

        fill_event = FillEvent(self.fill_dict, self.timestamp)
        self.events_queue.put(fill_event)
        


    def _update_fill(self):
        self.history_fill_dict.update({self.timestamp:self.fill_dict})


    def store(self):
        """
        存储fill
        """
        store_path = os.path.join(self.store_path, 'fill')
        if not os.path.exists(store_path):
            os.mkdir(store_path)
        with open(os.path.join(store_path, 'history_fill.yaml').replace(':', '-'), 'w', encoding='utf-8') as f:
            yaml.dump(self.history_fill_dict, f, allow_unicode=True, sort_keys=False)


        # fill_dict_df = pd.DataFrame(self.fill_dict)
        # # quantity
        # fill_quantity_df = fill_dict_df.loc['数量']
        # fill_quantity_df.name = event.timestamp
        # self.fill_quantity_df = self.fill_quantity_df.append(fill_quantity_df)
        # self.fill_quantity_df.to_csv(os.path.join(store_path, 'fill_quantity.csv'))
        # # fill price
        # fill_price_df = fill_dict_df.loc['price']
        # fill_price_df.name = event.timestamp
        # self.fill_price_df = self.fill_price_df.append(fill_price_df)
        # self.fill_price_df.to_csv(os.path.join(store_path, 'fill_price.csv'))
        # # fee
        # fill_fee_df = fill_dict_df.loc['fee']
        # fill_fee_df.name = event.timestamp
        # self.fill_fee_df = self.fill_fee_df.append(fill_fee_df)
        # self.fill_fee_df.to_csv(os.path.join(store_path, 'fill_fee.csv'))


