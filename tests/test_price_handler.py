import unittest
from dali.queue import sim_queue


class TestPriceHandler(unittest.TestCase):
    """
    使用一些列子来测试PriceHandler对象
    检查：
        数据格式是否正确
        函数是否正确返回
        意外情况的捕获
    """
    def setUp(self):

        eq = sim_queue.SimQueue()

        from dali.price_handler import sim_bar_handler
        self.barObj = sim_bar_handler.SimBarHandler('/Users/Hans/Desktop/Dali/data/zz500_15min', eq,
                                    start_date='2019-08-11', end_date='2019-11-01', look_back=40,
                                    store_path='/Users/Hans/Desktop/Dali/account/test/',
                                    fill_nan=True,
                                    init_tickers=['000006','000008','000009','000012','000021','000025',
                                                '000027','000028','000031','000039','000050','000060',
                                                '000061','000062','000066','000078','000089','000090',
                                                '000156','000158'])
        for i in range(50):
            self.barObj.update_bar()


    # def test_price_is_not_nan(self):
    #     """
    #     测试bar_event的价格是否为nan值
    #     """
    #     pass


    def test_close_price(self):
        self.assertEqual(self.barObj.history_price_df.loc['2019-08-12 09:30:00', '000008'], 3.50)
        self.assertEqual(self.barObj.history_price_df.loc['2019-08-12 09:45:00', '000008'], 3.49)



if __name__ == '__main__':
    unittest.main()