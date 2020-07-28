import os
import pandas as pd
import yaml, copy
import numpy as np
import pdb
from ..utils.log import logger
log = logger('[PositionHandler]')


class PositionHandler(object):
    """
    处理T+1交易行为，处理FillEvent事件，更新当前持仓，账簿
    
    提供持仓查询
    """
    def __init__(self, tick_handler, init_position, store_path):
        """
        初始化持仓和账簿
        """
        self.init_cash = 0
        self.store_path = store_path
        self.tick_handler = tick_handler
        self.init_position = init_position

        self._init_position()
        self._init_book()


    def _init_position(self):
        """
        初始化持仓记录
        """
        self.position = copy.deepcopy(self.init_position)
        self.history_position = {}

        for ticker in self.position:
            self.position[ticker]['现价'] = 0
            self.position[ticker]['市值'] = 0
            self.position[ticker]['净开仓'] = 0
            self.position[ticker]['初始持仓市值'] = 0

    def _init_book(self):
        """
        初始化账簿
        """
        self.book = {}
        self.book['现金'] = self.init_cash
        self.book['初始现金'] = self.init_cash
        self.history_book = {}




    def _query_last_price(self):
        self.sell_price_01 = self.tick_handler.get_sell_price_01()
        self.buy_price_01 = self.tick_handler.get_buy_price_01()
        self.ticker_names = self.tick_handler.get_ticker_names()



    def update_timestamp(self, event):
        self.timestamp = event.timestamp


    def update_position(self, event):
        """
        更新持仓
        """
        fill_dict = event.fill_dict
        for ticker in self.position:
            # 将Fill更新到当前持仓
            # 更新其他未交易股票的市值
            if ticker in fill_dict:
                if fill_dict[ticker]['买卖方向'] == '买':
                    self.position[ticker]['持仓'] += event.fill_dict[ticker]['成交数量']
                    self.position[ticker]['净开仓'] += event.fill_dict[ticker]['成交数量']
                    self.position[ticker]['可用'] = self.position[ticker]['可用']
                    self.position[ticker]['现价'] = event.fill_dict[ticker]['成交价格']
                    self.position[ticker]['市值'] = round(self.position[ticker]['持仓'] * self.position[ticker]['现价'])


                elif fill_dict[ticker]['买卖方向'] == '卖':
                    self.position[ticker]['持仓'] -= event.fill_dict[ticker]['成交数量']
                    self.position[ticker]['净开仓'] -= event.fill_dict[ticker]['成交数量']
                    self.position[ticker]['可用'] -= event.fill_dict[ticker]['成交数量']
                    self.position[ticker]['现价'] = event.fill_dict[ticker]['成交价格']
                    self.position[ticker]['市值'] = round(self.position[ticker]['持仓'] * self.position[ticker]['现价'])

            else:
                self.position[ticker]['现价'] = self.buy_price_01[ticker]
                self.position[ticker]['市值'] = round(self.position[ticker]['持仓'] * self.position[ticker]['现价'])
            self.position[ticker]['初始持仓市值'] = round(self.position[ticker]['初始持仓'] * self.position[ticker]['现价'])


    def update_book(self, event):
        """
        更新历史持仓记录
        """
        self.book['股票资产'] = 0
        self.book['手续费'] = 0
        self.book['初始持仓股票资产'] = 0
        fill_dict = event.fill_dict
        for ticker in self.position:
            if ticker in fill_dict:
                if fill_dict[ticker]['买卖方向'] == '买':
                    self.book['现金'] = self.book['现金'] - event.fill_dict[ticker]['成交额'] - event.fill_dict[ticker]['佣金']
                    self.book['手续费'] += event.fill_dict[ticker]['佣金']
                elif fill_dict[ticker]['买卖方向'] == '卖':
                    fee = event.fill_dict[ticker]['佣金'] + event.fill_dict[ticker]['印花税'] + event.fill_dict[ticker]['过户费']
                    self.book['手续费'] += fee
                    self.book['现金'] = self.book['现金'] + event.fill_dict[ticker]['成交额'] - fee
            else:
                pass
            self.book['股票资产'] = self.book['股票资产'] + self.position[ticker]['市值']
            self.book['初始持仓股票资产'] = self.book['初始持仓股票资产'] + self.position[ticker]['初始持仓市值']
        self.book['手续费'] = round(self.book['手续费'], 2)
        self.book['现金'] = round(self.book['现金'], 2)
        self.book['总资产'] = self.book['现金'] + self.book['股票资产']
        self.book['初始持仓资产'] = self.init_cash + self.book['初始持仓股票资产']




    def update_history_book(self):
        """
        更新历史持仓记录
        """
        self.history_book.update({self.timestamp:copy.deepcopy(self.book)})


    def update_history_position(self):
        """
        更新历史持仓记录
        """
        self.history_position.update({self.timestamp:copy.deepcopy(self.position)})


# 外部调用 ------------------------------------------------------------------------------------------
    def on_fill(self, event):
        if event.event_type == "FILL":
            self._query_last_price()
            self.update_timestamp(event)

            self.update_position(event)
            self.update_book(event)


            self.update_history_position()
            self.update_history_book()

            #self.store()




    def store(self):
        """
        存储持仓到指定目录下，建议在执行入口目录
        """
        store_path = os.path.join(self.store_path, 'position')
        if not os.path.exists(store_path):
            os.mkdir(store_path)

        with open(os.path.join(store_path, 'history_position.yaml').replace(':', '-'), 'w', encoding='utf-8') as f:
            yaml.dump(self.history_position, f, allow_unicode=True, sort_keys=False)

        #store_history_position
        capital, position = {}, {}
        for i in self.history_position:
            capital[i] = {}
            position[i] = {}
            for j in self.ticker_names:
                capital[i][j] = self.history_position[i][j]['市值']
                position[i][j] = self.history_position[i][j]['持仓']
        self.history_capital_df = pd.DataFrame(capital).T
        self.history_capital_df.to_csv(os.path.join(store_path, 'history_capital.csv'))

        self.history_position_df = pd.DataFrame(position).T
        self.history_position_df.to_csv(os.path.join(store_path, 'history_position.csv'))


        self.history_book_df = pd.DataFrame(self.history_book).T
        self.history_book_df.to_csv(os.path.join(store_path, 'history_book.csv'))


            
    def get_position(self):
        """
        返回当前持仓
        """
        return self.position

    def get_book(self):
        """
        返回当前账簿
        """
        return self.book
