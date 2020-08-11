
import pandas as pd
import os
from ..utils.performance import *
import yaml
from .tearsheet import plot_tearsheet
import pdb


class Profiling(object):
    def __init__(self, benchmark, periods=252*16, account_path=None):
        self.account_path = account_path
        self.stats = {}
        self.config = {}
        self.periods = periods
        self.benchmark = benchmark
        print('[Statistics][Profiling] init ...')

    def run(self):
        self.load_price()

        self.load_books()
        self.cal_datetime()
        self.cal_PNL()
        self.cal_returns()
        self.cal_fee()
        self.cal_drawdowns()
        self.cal_sharpe()
        self.cal_cagr()
        self.cal_sortino()
        self.cal_rsq()

        self.cal_benchmark_PNL()
        self.load_benchmark()
        self.cal_benchmark_sharpe()
        self.cal_benchmark_drawdowns()
        self.cal_benchmark_cagr()
        self.cal_benchmark_sortino()
        self.cal_benchmark_rsq()

        self.cal_alpha_PNL()
        self.cal_alpha_sharpe()
        self.cal_alpha_drawdowns()
        self.cal_alpha_cagr()
        self.cal_alpha_sortino()
        self.cal_alpha_rsq()

        self.load_trades()
        self.load_algo()

        self.store_profiles()

        plot_tearsheet(self.stats, self.periods, benchmark=self.benchmark, 
                     rolling_sharpe=True, store_path=self.account_path)

    def load_price(self):
        self.price = pd.read_csv(os.path.join(self.account_path, 'price', 'BuyPrice01.csv'), index_col=0)
        # self.price = self.price.loc[np.in1d(self.price.index.values,
        #                             self.marker['bar_marker'].index.values[self.marker['bar_marker'].values != 'LOOKBACK'])]


    def load_books(self):
        setattr(self, 'book', pd.read_csv(os.path.join(self.account_path, 'position', 'history_book.csv'), index_col=0))
        #self.book = self.book.loc[self.price.index.values]
        self.book['现金'] = self.book['现金'].fillna(method='ffill')
        self.book['股票资产'] = self.book['股票资产'].fillna(method='ffill')
        self.book['手续费'] = self.book['手续费'].fillna(0)
        self.book['总资产'] = self.book['总资产'].fillna(method='ffill')

    def cal_datetime(self):
        df = self.book.copy()
        self.config['start'] = df.index.values[0]
        self.config['end'] = df.index.values[-1]
        df.index = pd.to_datetime(df.index)
        tmp = df.groupby([lambda x:x.year, lambda x:x.month, lambda x:x.day]).sum()
        self.config['length'] = '%s days' %tmp.shape[0]


    def cal_PNL(self):
        self.stats['PNL'] = self.book['总资产']
        self.stats['total_capital'] = self.stats['PNL'].iloc[-1]
        self.stats['init_capital'] = self.stats['PNL'].iloc[0]

    def cal_returns(self):
        df = self.stats['PNL'] - self.stats['PNL'].iloc[0] - self.book['手续费'].iloc[0]
        self.stats['returns'] = (df - df.shift(1))/self.stats['PNL'].iloc[0]
        self.stats['returns'] = self.stats['returns'].fillna(0)
        self.stats['returns'].replace([np.inf, -np.inf], np.nan, inplace=True)
        self.stats['cum_returns'] = self.stats['returns'].cumsum(skipna=True)
        self.stats['total_returns'] = self.stats['cum_returns'].iloc[-1]
        #import pdb; pdb.set_trace()

    def cal_fee(self):
        self.book['手续费'].replace([np.inf, -np.inf], np.nan, inplace=True)
        self.stats['total_fee'] = self.book['手续费'].cumsum(skipna=True)[-1]
        

    def cal_drawdowns(self):
        self.stats['drawdowns'], self.stats['max_drawdowns'], self.stats['max_drawdowns_duration'] =\
                         create_drawdowns(self.stats['cum_returns'])


    def cal_sharpe(self):
        self.stats['sharpe'] = create_sharpe_ratio(self.stats['returns'], self.periods)


    def cal_cagr(self):
        #self.stats['cagr'] = create_cagr(self.stats['cum_returns'], self.periods)
        self.stats['cagr'] = np.nan


    def cal_sortino(self):
        self.stats['sortino'] = create_sortino_ratio(self.stats['returns'], self.periods)


    def cal_rsq(self):
        self.stats['rsquared'] = rsquared(range(self.stats['cum_returns'].shape[0]), self.stats['cum_returns'])


    # benchmark -----------------------------------------------------------------------------------------------------------
    def load_benchmark(self):
        self.stats['benchmark_returns'] = (self.stats['benchmark_PNL'] - self.stats['benchmark_PNL'].shift(1))/self.stats['benchmark_PNL'].iloc[0]
        self.stats['benchmark_returns'] = self.stats['benchmark_returns'].fillna(0)
        self.stats['benchmark_returns'].replace([np.inf, -np.inf], np.nan, inplace=True)
        self.stats['benchmark_cum_returns'] = self.stats['benchmark_returns'].cumsum(skipna=True)


    def cal_benchmark_PNL(self):
        self.stats['benchmark_PNL'] = self.book['初始持仓资产']
        self.stats['benchmark_total_capital'] = self.stats['benchmark_PNL'].iloc[-1]


    def cal_benchmark_drawdowns(self):
        self.stats['benchmark_drawdowns'], self.stats['benchmark_max_drawdowns'], self.stats['benchmark_max_drawdowns_duration'] =\
                         create_drawdowns(self.stats['benchmark_cum_returns'])


    def cal_benchmark_sharpe(self):
        self.stats['benchmark_sharpe'] = create_sharpe_ratio(self.stats['benchmark_returns'], self.periods)


    def cal_benchmark_cagr(self):
        #self.stats['benchmark_cagr'] = create_cagr(self.stats['benchmark_cum_returns'], self.periods)
        self.stats['benchmark_cagr'] = np.nan


    def cal_benchmark_sortino(self):
        self.stats['benchmark_sortino'] = create_sortino_ratio(self.stats['benchmark_returns'], self.periods)


    def cal_benchmark_rsq(self):
        self.stats['benchmark_rsquared'] = rsquared(range(self.stats['benchmark_cum_returns'].shape[0]), self.stats['benchmark_cum_returns'])

    # alpha -----------------------------------------------------------------------------------------------------------
    def cal_alpha_PNL(self):
        self.stats["alpha_PNL"] = self.stats['PNL'] - self.stats['benchmark_PNL']
        self.stats['alpha_returns'] = self.stats['returns'] - self.stats['benchmark_returns']
        self.stats['alpha_returns'].replace([np.inf, -np.inf], np.nan, inplace=True)
        self.stats['alpha_cum_returns'] = self.stats['alpha_returns'].cumsum(skipna=True)
        self.stats['alpha_capital'] = self.stats['alpha_PNL'].iloc[-1]


    def cal_alpha_sharpe(self):
        self.stats["alpha_sharpe"] = create_sharpe_ratio(self.stats['alpha_returns'], self.periods) 


    def cal_alpha_drawdowns(self):
        self.stats['alpha_drawdowns'], self.stats['alpha_max_drawdowns'], self.stats['alpha_max_drawdowns_duration'] =\
                         create_drawdowns(self.stats['alpha_cum_returns'])


    def cal_alpha_cagr(self):
        #self.stats['alpha_cagr'] = create_cagr(self.stats['alpha_cum_returns'], self.periods)
        self.stats['alpha_cagr'] = np.nan


    def cal_alpha_sortino(self):
        self.stats['alpha_sortino'] = create_sortino_ratio(self.stats['alpha_returns'], self.periods)


    def cal_alpha_rsq(self):
        self.stats['alpha_rsquared'] = rsquared(range(self.stats['alpha_cum_returns'].shape[0]), self.stats['alpha_cum_returns'])


    # trades -----------------------------------------------------------------------------------------------------------
    def load_trades(self):
        with open(os.path.join(self.account_path, 'statistics', 'trades.yaml'), 'r') as f:
            loader = yaml.load(f, Loader=yaml.FullLoader)
        self.stats.update(loader)
        
        df = pd.read_csv(os.path.join(self.account_path, 'statistics', 'bps.csv'), index_col=0)
        self.stats['bps'] = df['bps']
        self.stats['bps'].replace([np.inf, -np.inf], np.nan, inplace=True)
        self.stats['avg_bps'] = self.stats['bps'].mean()
        
    # algo -----------------------------------------------------------------------------------------------------------
    def load_algo(self):
        df = pd.read_csv(os.path.join(self.account_path, 'algo', 'algo.csv'), index_col=0)
        self.stats['buy_open'] = df[(df['买卖方向'] == '买') & (df['开平仓'] == '开仓')].shape[0]
        self.stats['sell_open'] = df[(df['买卖方向'] == '卖') & (df['开平仓'] == '开仓')].shape[0]
        self.stats['sell_close'] = df[(df['买卖方向'] == '卖') & (df['开平仓'] == '平仓')].shape[0]
        self.stats['buy_close'] = df[(df['买卖方向'] == '买') & (df['开平仓'] == '平仓')].shape[0]

        
        
    # store -----------------------------------------------------------------------------------------------------------
    def store_profiles(self):
        self.profiles = {}
        self.profiles.update(self.config)
        for i in self.stats:
            if type(self.stats[i]) != np.ndarray and type(self.stats[i]) != pd.core.frame.DataFrame and\
                                                type(self.stats[i]) != pd.core.series.Series:
                self.profiles.update({i:round(float(self.stats[i]), 2)})
        with open(os.path.join(self.account_path, 'profiles.yaml').replace(':', '-'), 'w') as f:
            yaml.dump(self.profiles, f, encoding='unicode', sort_keys=False)



if __name__ == '__main__':
    pro = Profiling(account_path='/Users/Hans/Desktop/Dali/account/', benchmark='equal_wgts_benchmark')
    pro.run()




