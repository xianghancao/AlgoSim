# encoding='utf-8'
import unittest

from dali.signal_handler.base import SignalHandler
from dali.signal_handler.operators import *
from dali.utils.signal_process import *


class Signal_test(SignalHandler):

    def __init__(self, events_queue, store_path):
        self.signal_name = 'Signal_test'
        self.events_queue = events_queue
        self.look_back = 40
        self.store_path = store_path
        super().__init__()


    def calculate_signal(self):
        ClosePrice = self.close_price    
        five_ma = ma(ClosePrice, 5)   
        ten_ma = ma(ClosePrice, 10)

        s = (five_ma-ten_ma)/ten_ma
        s = np.abs(s[-1])
        #return -1 * sort_quintiles(scale_one(s), 0, 10)  + sort_quintiles(scale_one(s), 90, 100)
        return s #sort_quintiles(scale_one(s), 90, 100)





                          
class TestSignalHandler(unittest.TestCase):
    """
    使用一些列子来测试SignalHandler对象
    检查：
        数据格式是否正确
        函数是否正确返回
        意外情况的捕获
    """
    def setUp(self):
        from dali.queue import sim_queue
        eq = sim_queue.SimQueue()

        from dali.price_handler import sim_bar_handler
        self.barObj = sim_bar_handler.SimBarHandler('/Users/Hans/Desktop/Dali/data/zz500_15min', eq,
                                    start_date='2019-08-13', end_date='2019-08-20', look_back=10,
                                    store_path='/Users/Hans/Desktop/Dali/account/test/',
                                    fill_nan=True,
                                    init_tickers=['000008','000009','000012','000021','000025',
                                                '000027','000028','000031','000039','000050','000060',
                                                '000061','000062','000066','000078','000089','000090',
                                                '000156','000158'])

        self.signal = Signal_test(eq, '/Users/Hans/Desktop/Dali/account/test/')


        eq.register('BAR', self.signal)


        while not self.barObj.is_iteration_end():
            self.barObj.update_bar()
            eq.run()
        eq.unregister('BAR', self.signal)




    def test_signal(self):
        self.assertEqual(round(self.signal.scaled_signal_df.loc['2019-08-13 09:30:00', '000008'], 6), 0.007516)
        self.assertEqual(round(self.signal.scaled_signal_df.loc['2019-08-13 09:45:00', '000008'], 6), 0.003332)
        self.assertEqual(round(self.signal.scaled_signal_df.loc['2019-08-13 10:45:00', '000009'], 6), 0.015334)


    


if __name__ == '__main__':
    unittest.main()
