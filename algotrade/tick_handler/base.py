
import os, time, datetime, shutil, pdb
from ..event import TickEvent
from ..utils.log import logger
log = logger('[TickHandler]')


class AbstractTickHandler():
    def __init__(self, events_queue, subscribe_tickers, subscribe_fields):
        self.subscribe_tickers = subscribe_tickers
        self.subscribe_fields = subscribe_fields
        self.events_queue = events_queue

        self._iteration_end = False



    # ------------------------------------------------------------------------
    def _subscribe_ticker(self): 
        """
        订阅股票
        """
        if self.subscribe_tickers is not None:
            self.subscribe_tickers = list(self.subscribe_tickers)
        log.info('subscribe_ticker %s' %self.subscribe_tickers)
        return



    # ------------------------------------------------------------------------
    def _init_ticker(self):
        self.ticker_names = self.subscribe_tickers 




    # ------------------------------------------------------------------------
    def _init_tick(self):
        """
        初始化tick_dict
        """
        self.tick_ticker_dict = {}
        for ticker in self.ticker_names:
            self.tick_ticker_dict[ticker] = {}
            for field in self.subscribe_fields['TAQ'] + self.subscribe_fields['TRADE']:
                self.tick_ticker_dict[ticker].update({field: 0})


    # ------------------------------------------------------------------------
    def _update_timestamp(self, event):
        self.timestamp = event.timestamp
        self.previous_timestamp = event.previous_timestamp



    # ------------------------------------------------------------------------
    def _update_event(self):
        """
        更新事件到队列
        """
        tick_event = TickEvent(timestamp=self.timestamp,
                            ticker_names=self.ticker_names,
                            field_dict=self.tick_field_dict)
        self.events_queue.put(tick_event)


    # ------------------------------------------------------------------------
    def _update_price(self):
        self.sell_price_01 = self.tick_field_dict['SellPrice01']
        self.buy_price_01 = self.tick_field_dict['BuyPrice01']
        return


    # ------------------------------------------------------------------------
    def get_buy_price_01(self):
        return self.buy_price_01

    def get_sell_price_01(self):
        return self.sell_price_01

    def get_last_timestamp(self):
        return self.timestamp

    def get_ticker_names(self):
        return self.ticker_names






