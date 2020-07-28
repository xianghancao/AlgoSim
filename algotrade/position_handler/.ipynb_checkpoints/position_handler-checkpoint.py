import os
import pandas as pd
import yaml
from ..utils.log import logger
log = logger('[PositionHandler]')


class PositionHandler(object):
    """
    处理T+1交易行为，处理FillEvent事件，更新当前持仓
    
    提供持仓查询
    """
    def __init__(self, tick_handler, init_position, store_path):
        """
        初始化持仓和账簿
        """
        self.init_cash = 0
        self.store_path = store_path
        self.tick_handler = tick_handler
        self.position = init_position

        self.init_position()
        self.init_book()


    def init_position(self):
        """
        初始化持仓记录
        """
        self.history_position = {}

 

    def init_book(self):
        """
        初始化账簿
        """
        self.book = {}
        self.book['现金'] = self.init_cash
        self.book['股票资产'] = 0
        self.book['总资产'] = self.book['现金'] + self.book['股票资产']
        self.history_book = {}



    def on_fill(self, event):
        if event.event_type == "FILL":
            self.get_last_price()
            self.update_timestamp(event)

            self.update_position(event)
            self.update_book(event)

            self.update_history_position()
            self.update_history_book()
            self.store()


    def get_last_price(self):
        """
        查询最新价格
        """
        last_price = self.tick_handler.get_last_price()
        ticker= self.tick_handler.get_ticker_names()
        self.last_price_dict = pd.Series(last_price, index=ticker).to_dict()


    def get_position(self):
        """
        返回当前持仓
        """
        return self.position


    def update_timestamp(self, event):
        self.timestamp = event.timestamp


    def update_position(self, event):
        """
        更新持仓
        """
        fill_dict = event.fill_dict
        for ticker in fill_dict:
            # 当前没有持仓，初始为0
            if self.position.get(ticker) is None:
                if fill_dict[ticker]['买卖方向'] == '卖':
                    raise Exception('第一笔订单不能卖空')
                self.position[ticker] = {}
                self.position[ticker]["持仓"] = 0
                self.position[ticker]['可用'] = 0
                self.position[ticker]['现价'] = 0
                self.position[ticker]['市值'] = 0

        for ticker in self.position:
            # 将Fill更新到当前持仓
            if ticker in fill_dict:
                if fill_dict[ticker]['买卖方向'] == '买':
                    self.position[ticker]['可用'] = self.position[ticker]['持仓']
                    self.position[ticker]['持仓'] += event.fill_dict[ticker]['成交数量']
                    self.position[ticker]['现价'] = self.last_price_dict[ticker]
                    self.position[ticker]['市值'] = self.position[ticker]['持仓'] * self.position[ticker]['现价']


                elif fill_dict[ticker]['买卖方向'] == '卖':
                    self.position[ticker]['持仓'] -= event.fill_dict[ticker]['成交数量']
                    self.position[ticker]['可用'] = self.position[ticker]['持仓']
                    self.position[ticker]['现价'] = self.last_price_dict[ticker]
                    self.position[ticker]['市值'] = self.position[ticker]['持仓'] * self.position[ticker]['现价']

            else:
                self.position[ticker]['现价'] = self.last_price_dict[ticker]
                self.position[ticker]['市值'] = self.position[ticker]['持仓'] * self.position[ticker]['现价']


    def update_book(self, event):
        """
        更新历史持仓记录
        """
        self.book['股票资产'] = 0
        self.book['手续费'] = 0
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
        self.book['总资产'] = self.book['现金'] + self.book['股票资产']


    def update_history_book(self):
        """
        更新历史持仓记录
        """
        self.history_book.update({self.timestamp:self.book})


    def update_history_position(self):
        """
        更新历史持仓记录
        """
        self.history_position.update({self.timestamp:self.position})
        print(self.history_position)

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
        self.history_position_df = pd.DataFrame(self.history_position).T
        self.history_position_df.to_csv(os.path.join(store_path, 'history_position.csv'))


        #store_history_book
        store_path = os.path.join(self.store_path, 'book')
        if not os.path.exists(store_path):
            os.mkdir(store_path)

        self.history_book_df = pd.DataFrame(self.history_book).T
        self.history_book_df.to_csv(os.path.join(store_path, 'history_book.csv'))



