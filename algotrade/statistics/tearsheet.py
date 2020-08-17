from matplotlib.ticker import FuncFormatter
import numpy as np
from matplotlib import cm
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import seaborn as sns
import os
from ..utils import performance as perf


def plot_tearsheet(stats, periods, benchmark=None, title=None, rolling_sharpe=True, store_path=None):
    """
    Plot the Tearsheet
    """
    rc = {
        'lines.linewidth': 1.0,
        'axes.facecolor': '0.995',
        'figure.facecolor': '0.97',
        'font.family': 'serif',
        'font.serif': 'Ubuntu',
        'font.monospace': 'Ubuntu Mono',
        'font.size': 14,
        'axes.labelsize': 10,
        'axes.labelweight': 'bold',
        'axes.titlesize': 10,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 10,
        'figure.titlesize': 12
    }
    sns.set_context(rc)
    sns.set_style("whitegrid")
    sns.set_palette("deep", desat=.6)

    if rolling_sharpe:
        offset_index = 1
    else:
        offset_index = 0
    vertical_sections = 5 + offset_index
    fig = plt.figure(figsize=(13, vertical_sections * 3))
    #fig.suptitle(title, y=0.94, weight='bold')
    gs = gridspec.GridSpec(vertical_sections, 3, wspace=0.25, hspace=0.5)

    ax_equity = plt.subplot(gs[:2, :])
    if rolling_sharpe:
        ax_alpha = plt.subplot(gs[2, :])
    ax_drawdown = plt.subplot(gs[2 + offset_index, :])
    ax_bps_dist = plt.subplot(gs[3 + offset_index, 0])
    ax_daily_returns = plt.subplot(gs[3 + offset_index, 1])
    ax_txt_algo = plt.subplot(gs[3 + offset_index, 2])
    ax_txt_curve = plt.subplot(gs[4 + offset_index, 0])
    ax_txt_alpha= plt.subplot(gs[4 + offset_index, 1])
    ax_txt_trade = plt.subplot(gs[4 + offset_index, 2])

    _plot_equity(stats, benchmark=benchmark, ax=ax_equity)
    if rolling_sharpe:
        _plot_rolling_sharpe(stats, ax=ax_alpha)
    _plot_drawdown(stats, ax=ax_drawdown)
    _plot_bps_dist(stats, ax=ax_bps_dist)
    _plot_daily_returns(stats, ax=ax_daily_returns)
    _plot_txt_algo(stats, ax=ax_txt_algo)
    _plot_txt_curve(stats, benchmark=benchmark, periods=periods, ax=ax_txt_curve)
    _plot_txt_alpha(stats, ax=ax_txt_alpha)
    _plot_txt_trade(stats, ax=ax_txt_trade)
    #_plot_txt_time(stats, ax=ax_txt_time)

    # Plot the figure
    #plt.show(block=False)

    if store_path is not None:
        fig.savefig(os.path.join(store_path, 'tearsheet.jpg'))#, bbox_inches='tight')



def _plot_equity(stats, benchmark, log_scale=False, ax=None):
    """
    Plots cumulative rolling returns versus some benchmark.
    """
    def format_two_dec(x, pos):
        return '%s' %x

    equity = stats['PNL']
    if ax is None:
        ax = plt.gca()

    y_axis_formatter = FuncFormatter(format_two_dec)
    ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
    # ax.xaxis.set_tick_params(reset=True)
    ax.yaxis.grid(linestyle=':')
    # ax.xaxis.set_major_locator(mdates.YearLocator(1))
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.grid(linestyle=':')

    if benchmark is not None:
        stats['benchmark_PNL'].plot(
            lw=2, color='blue', label=benchmark, alpha=0.60,
            ax=ax
        )

    equity.plot(lw=2, color='green', alpha=0.6, x_compat=False,
                label='Trades', ax=ax)

    init_capital = equity.iloc[0]
    ax.axhline(init_capital, linestyle='--', color='black', lw=1)
    ax.set_ylabel('Cumulative returns')
    ax.legend(loc='best')
    ax.set_xlabel('')
    plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')

    if log_scale:
        ax.set_yscale('log')
    return ax


def _plot_rolling_sharpe(stats, log_scale=False, ax=None):
    def format_two_dec(x, pos):
        return '%s' %x

    alpha_equity = stats['alpha_PNL']
    if ax is None:
        ax = plt.gca()

    y_axis_formatter = FuncFormatter(format_two_dec)
    ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
    # ax.xaxis.set_tick_params(reset=True)
    ax.yaxis.grid(linestyle=':')
    # ax.xaxis.set_major_locator(mdates.YearLocator(1))
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.grid(linestyle=':')

    alpha_equity.plot(lw=2, color='red', alpha=0.6, x_compat=False,
                label='Alpha', ax=ax)

    init_capital = alpha_equity.iloc[0]
    ax.axhline(init_capital, linestyle='--', color='black', lw=1)
    ax.set_ylabel('Cumulative returns')
    ax.legend(loc='best')
    ax.set_xlabel('')
    plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')

    if log_scale:
        ax.set_yscale('log')
    return ax


def _plot_drawdown(stats, ax=None):
    """
    Plots the underwater curve
    """
    def format_perc(x, pos):
        return '%.0f%%' % x

    drawdown = stats['alpha_drawdowns']

    if ax is None:
        ax = plt.gca()

    #y_axis_formatter = FuncFormatter(format_perc)
    #ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
    #ax.yaxis.grid(linestyle=':')
    # ax.xaxis.set_tick_params(reset=True)
    # ax.xaxis.set_major_locator(mdates.YearLocator(1))
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.grid(linestyle=':')

    drawdown.plot(ax=ax, lw=1, kind='area', color='red', alpha=0.3, label='alpha_drawdowns')
    ax.set_ylabel('')
    ax.set_xlabel('')
    plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')
    ax.set_title('Alpha Drawdown (%)', fontweight='bold')
    return ax


def _plot_daily_returns(stats, ax=None, **kwargs):
    """
    Plots a barplot of returns by daily.
    """
    def format_perc(x, pos):
        return '%.000f%%' % x

    returns = stats['alpha_returns']
    returns = returns.fillna(0)
    returns.name = 'alpha returns'
    #returns.index = pd.to_datetime(returns.index)

    if ax is None:
        ax = plt.gca()

    #y_axis_formatter = FuncFormatter(format_perc)
    #ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
    ax.yaxis.grid(linestyle=':')

    dly_ret = perf.aggregate_returns(returns, 'daily') #* 100.0
    dly_ret.plot(ax=ax, kind="bar")
    ax.set_title('Daily Alpha Returns (%)', fontweight='bold')
    ax.set_ylabel('')
    ax.set_xlabel('')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    ax.xaxis.grid(False)
    ax.axvline(x=7.5, linestyle=':', color='lightgrey', lw=1)  
    return ax


def _plot_bps_dist(stats, ax=None, **kwargs):
    """
    bps distribution
    """
    ax.set_title('Bps Distribution', fontweight='bold')
    stats['bps'].plot.hist(ax=ax, bins=50)
    #ax.set_ylabel('')
    return ax


def _plot_txt_algo(stats, ax):
    def format_perc(x, pos):
        return '%.0f%%' % x

    if ax is None:
        ax = plt.gca()

    y_axis_formatter = FuncFormatter(format_perc)
    ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

    right = 9.75

    ax.text(0.25, 8.9, 'Sell Open', fontsize=10)
    ax.text(right, 8.9, '{:.0f}'.format(stats['sell_open']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 7.9, 'Buy Close', fontsize=10)
    ax.text(right, 7.9, '{:.0f}'.format(stats['buy_close']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 6.9, 'Buy Open', fontsize=10)
    ax.text(right, 6.9, '{:.0f}'.format(stats['buy_open']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 5.9, 'Sell Close', fontsize=10)
    ax.text(right, 5.9, '{:.0f}'.format(stats['sell_close']), fontweight='bold', horizontalalignment='right', fontsize=10)

    
    ax.text(0.25, 4.9, 'Total Nums', fontsize=10)
    ax.text(right, 4.9, '{:.0f}'.format(stats['algo_nums']), fontweight='bold', horizontalalignment='right', fontsize=10)


    ax.set_title('Algo', fontweight='bold')

    ax.grid(False)
    ax.spines['top'].set_linewidth(2.0)
    ax.spines['bottom'].set_linewidth(2.0)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.set_ylabel('')
    ax.set_xlabel('')

    ax.axis([0, 10, 0, 10])
    return ax
    
def _plot_txt_curve(stats, periods, benchmark=None, ax=None):
    """
    Outputs the statistics for the equity curve.
    """
    def format_perc(x, pos):
        return '%.0f%%' % x

    if ax is None:
        ax = plt.gca()

    y_axis_formatter = FuncFormatter(format_perc)
    ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

    if benchmark is None:
        left = 9.75
    else:
        left = 6.50
        right = 9.75
    ax.text(0.25, 8.9, 'Total Return', fontsize=10)
    ax.text(left, 8.9, '{:.2%}'.format(stats['total_returns']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 7.9, 'Total Capital', fontsize=10)
    ax.text(left, 7.9, '{:.0f}'.format(stats['total_capital']), horizontalalignment='right', fontsize=10)

    ax.text(0.25, 6.9, 'Sharpe Ratio', fontsize=10)
    ax.text(left, 6.9, '{:.2f}'.format(stats['sharpe']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 5.9, 'Sortino Ratio', fontsize=10)
    ax.text(left, 5.9, '{:.2f}'.format(stats['sortino']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 4.9, 'Annual Volatility', fontsize=10)
    ax.text(left, 4.9, '{:.2%}'.format(stats['returns'].std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 3.9, 'R-Squared', fontsize=10)
    ax.text(left, 3.9, '{:.2f}'.format(stats['rsquared']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 2.9, 'Max Drawdown', fontsize=10)
    ax.text(left, 2.9, '{:.2%}'.format(stats['max_drawdowns']), color='red', fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 1.9, 'MDD Duration', fontsize=10)
    ax.text(left, 1.9, '{:.0f}'.format(stats['max_drawdowns_duration']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.set_title('Curve', fontweight='bold')

    if benchmark is not None:
        returns_b = stats['benchmark_returns'].values
        equity_b = stats['benchmark_cum_returns'].values
        tot_ret_b = equity_b[-1]
        tot_cap_b = stats['benchmark_total_capital']
        #cagr_b = perf.create_cagr(equity_b)
        sharpe_b = stats['benchmark_sharpe']
        sortino_b = stats['benchmark_sortino']
        rsq_b = stats['benchmark_rsquared']
        dd_b, dd_max_b, dd_dur_b = stats['benchmark_drawdowns'], stats['benchmark_max_drawdowns'], stats['benchmark_max_drawdowns_duration']

        ax.text(right, 8.9, '{:.2%}'.format(tot_ret_b), fontweight='bold', horizontalalignment='right', fontsize=10)
        ax.text(right, 7.9, '{:.0f}'.format(tot_cap_b), horizontalalignment='right', fontsize=10)
        ax.text(right, 6.9, '{:.2f}'.format(sharpe_b), fontweight='bold', horizontalalignment='right', fontsize=10)
        ax.text(right, 5.9, '{:.2f}'.format(sortino_b), fontweight='bold', horizontalalignment='right', fontsize=10)
        ax.text(right, 4.9, '{:.2%}'.format(returns_b.std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=10)
        ax.text(right, 3.9, '{:.2f}'.format(rsq_b), fontweight='bold', horizontalalignment='right', fontsize=10)
        ax.text(right, 2.9, '{:.2%}'.format(dd_max_b), color='red', fontweight='bold', horizontalalignment='right', fontsize=10)
        ax.text(right, 1.9, '{:.0f}'.format(dd_dur_b), fontweight='bold', horizontalalignment='right', fontsize=10)

        ax.set_title('Curve vs. Benchmark', fontweight='bold')


    ax.grid(False)
    ax.spines['top'].set_linewidth(2.0)
    ax.spines['bottom'].set_linewidth(2.0)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.set_ylabel('')
    ax.set_xlabel('')

    ax.axis([0, 10, 0, 10])
    return ax


def _plot_txt_alpha(stats, ax=None):
    """
    Outputs the statistics for the equity curve.
    """
    def format_perc(x, pos):
        return '%.0f%%' % x

    if ax is None:
        ax = plt.gca()

    y_axis_formatter = FuncFormatter(format_perc)
    ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

    right = 9.75
    ax.text(0.25, 8.9, 'Alpha Return', fontsize=10)
    ax.text(right, 8.9, '{:.2%}'.format(stats['alpha_cum_returns'].iloc[-1]), color='red', fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 7.9, 'Alpha Capital', fontsize=10)
    ax.text(right, 7.9, '{:.0f}'.format(stats['alpha_capital']), color='red', fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 6.9, 'Alpha Sharpe Ratio', fontsize=10)
    ax.text(right, 6.9, '{:.2f}'.format(stats['alpha_sharpe']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 5.9, 'Alpha Sortino Ratio', fontsize=10)
    ax.text(right, 5.9, '{:.2f}'.format(stats['alpha_sortino']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 4.9, 'Alpha Annual Volatility', fontsize=10)
    ax.text(right, 4.9, '{:.2%}'.format(stats['alpha_returns'].std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 3.9, 'Alpha R-Squared', fontsize=10)
    ax.text(right, 3.9, '{:.2f}'.format(stats['alpha_rsquared']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 2.9, 'Alpha Max Drawdown', fontsize=10)
    ax.text(right, 2.9, '{:.2%}'.format(stats['alpha_max_drawdowns']), color='red', fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 1.9, 'Alpha Max Drawdown Duration', fontsize=10)
    ax.text(right, 1.9, '{:.0f}'.format(stats['alpha_max_drawdowns_duration']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.set_title('Alpha', fontweight='bold')


    ax.grid(False)
    ax.spines['top'].set_linewidth(2.0)
    ax.spines['bottom'].set_linewidth(2.0)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.set_ylabel('')
    ax.set_xlabel('')

    ax.axis([0, 10, 0, 10])
    return ax


def _plot_txt_trade(stats, ax=None):
    """
    Outputs the statistics for the equity curve.
    """
    def format_perc(x, pos):
        return '%.0f%%' % x

    if ax is None:
        ax = plt.gca()

    y_axis_formatter = FuncFormatter(format_perc)
    ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

    right = 9.75
    ax.text(0.25, 8.9, 'Total Trades Amount', fontsize=10)
    ax.text(right, 8.9, '{:.0f}'.format(stats['daily_trades_amount']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 7.9, 'Total Buy Amount', fontsize=10)
    ax.text(right, 7.9, '{:.0f}'.format(stats['daily_buy_trades_amount']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 6.9, 'Total Sell Amount', fontsize=10)
    ax.text(right, 6.9, '{:.0f}'.format(stats['daily_sell_trades_amount']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 5.9, 'Total Fee', fontsize=10)
    ax.text(right, 5.9, '{:.0f}'.format(stats['total_fee']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 4.9, 'Total Trades Nums', fontsize=10)
    ax.text(right, 4.9, '{:.0f}'.format(stats['total_trades_nums']), color='red', fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 3.9, 'Trade Stock Nums', fontsize=10)
    ax.text(right, 3.9, '{:.0f}'.format(stats['trade_stock_nums']), color='red', fontweight='bold', horizontalalignment='right', fontsize=10)


    ax.text(0.25, 2.9, 'Avg Bps', fontsize=10)
    ax.text(right, 2.9, '{:.0f}'.format(stats['avg_bps']), color='red', fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.set_title('Trades', fontweight='bold')


    ax.grid(False)
    ax.spines['top'].set_linewidth(2.0)
    ax.spines['bottom'].set_linewidth(2.0)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.set_ylabel('')
    ax.set_xlabel('')

    ax.axis([0, 10, 0, 10])
    return ax


def _plot_txt_times(stats, ax=None):
    """
    Outputs the statistics for the equity curve.
    """
    def format_perc(x, pos):
        return '%.0f%%' % x

    if ax is None:
        ax = plt.gca()

    y_axis_formatter = FuncFormatter(format_perc)
    ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

    right = 9.75
    ax.text(0.25, 8.9, 'day numbers', fontsize=10)
    ax.text(right, 8.9, '{:.1%}'.format(stats['daily_sell_trades']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.text(0.25, 7.9, 'dialy buy trades', fontsize=10)
    ax.text(right, 7.9, '{:.0f}'.format(stats['daily_buy_trades']), fontweight='bold', horizontalalignment='right', fontsize=10)

    ax.set_title('Trades', fontweight='bold')


    ax.grid(False)
    ax.spines['top'].set_linewidth(2.0)
    ax.spines['bottom'].set_linewidth(2.0)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.set_ylabel('')
    ax.set_xlabel('')

    ax.axis([0, 10, 0, 10])
    return ax