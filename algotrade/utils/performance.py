from itertools import groupby

import numpy as np
import pandas as pd
from scipy.stats import linregress


def aggregate_returns(returns, convert_to):
    """
    Aggregates returns by day, week, month, or year.
    """
    def cumulate_returns(x):
        return np.exp(np.log(1 + x).cumsum())[-1] - 1

    if convert_to == 'daily':
        s = returns.groupby(
            [lambda x: str(x)[-8:-3]]).apply(cumulate_returns)
        return s

    elif convert_to == 'weekly':
        return returns.groupby(
            [lambda x: x.year,
             #lambda x: x.month,
             lambda x: x.isocalendar()[2]]).apply(cumulate_returns)
    elif convert_to == 'monthly':
        return returns.groupby(
            [lambda x: x.year, lambda x: x.month]).apply(cumulate_returns)
    elif convert_to == 'yearly':
        return returns.groupby(
            [lambda x: x.year]).apply(cumulate_returns)
    else:
        ValueError('convert_to must be weekly, monthly or yearly')


def create_cagr(equity, periods):
    """
    Calculates the Compound Annual Growth Rate (CAGR)
    for the portfolio, by determining the number of years
    and then creating a compound annualised rate based
    on the total return.

    Parameters:
    equity - A pandas Series representing the equity curve.
    periods - Daily (252), Hourly (252*6.5), Minutely(252*6.5*60) etc.
    """
    years = equity.shape[0] / float(periods)
    return (equity.iloc[-1] ** (1.0 / years)) - 1.0


def create_sharpe_ratio(returns, periods):
    """
    Create the Sharpe ratio for the strategy, based on a
    benchmark of zero (i.e. no risk-free rate information).

    Parameters:
    returns - A pandas Series representing period percentage returns.
    periods - Daily (252), Hourly (252*6.5), Minutely(252*6.5*60) etc.
    """
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)


def create_sortino_ratio(returns, periods):
    """
    Create the Sortino ratio for the strategy, based on a
    benchmark of zero (i.e. no risk-free rate information).

    Parameters:
    returns - A pandas Series representing period percentage returns.
    periods - Daily (252), Hourly (252*6.5), Minutely(252*6.5*60) etc.
    """
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns[returns < 0])



def create_drawdowns(cpnl_df):
    cpnl = cpnl_df.T.values
    _cpnl = cpnl * np.ones((cpnl.shape[0], cpnl.shape[0]))
    _cpnl = np.tril(_cpnl)
    max_cpnl = np.nanmax(_cpnl, axis=1)
    drawdown = cpnl - max_cpnl
    max_drawdown = np.abs(np.min(drawdown))


    _cpnl = np.hstack((np.zeros((cpnl.shape[0],1)), _cpnl))
    max_cpnl = np.argmax(_cpnl, axis=1)
    drawdown_period = np.arange(len(cpnl)) - max_cpnl + 1
    duration = int(np.max(drawdown_period))
    return pd.DataFrame(drawdown, index=cpnl_df.index), max_drawdown, duration





def rsquared(x, y):
    """
    Return R^2 where x and y are array-like.
    """
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    return r_value**2



def create_drawdowns_2(returns):
    """
    Calculate the largest peak-to-trough drawdown of the equity curve
    as well as the duration of the drawdown. Requires that the
    pnl_returns is a pandas Series.

    Parameters:
    equity - A pandas Series representing period percentage returns.

    Returns:
    drawdown, drawdown_max, duration
    """
    # Calculate the cumulative returns curve
    # and set up the High Water Mark
    idx = returns.index
    hwm = np.zeros(len(idx))

    # Create the high water mark
   #print(returns)
    for t in range(1, len(idx)):
        #print(hwm[t - 1], returns.iloc[t])
        hwm[t] = max(hwm[t - 1], returns.iloc[t])

    # Calculate the drawdown and duration statistics
    perf = pd.DataFrame(index=idx)
    perf["Drawdown"] = (hwm - returns.values) / hwm
    perf["Drawdown"].iloc[0] = 0.0
    perf["DurationCheck"] = np.where(perf["Drawdown"] == 0, 0, 1)
    duration = max(
        sum(1 for i in g if i == 1)
        for k, g in groupby(perf["DurationCheck"])
    )
    return perf["Drawdown"], np.max(perf["Drawdown"]), duration

