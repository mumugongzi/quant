# coding: utf-8
"""
计算量化策略相关指标
"""
from __future__ import division

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common import config

# 获取数据函数
from tool.plot import *


def get_stock_data(stock_code, index_code, start_date, end_date):
    """
    :param stock_code: 股票代码，例如‘sz000002’
    :param index_code: 指数代码，例如‘sh000001’
    :param start_date: 回测开始日期，例如‘1991-1-30'
    :param end_date: 回测结束日期，例如‘2015-12-31’
    :return: 函数返回其他函数的各参数序列
    """
    # 此处为存放csv文件的本地路径，请自行改正地址.注意windows和mac系统,斜杠的方向不一样
    stock_data = pd.read_csv(config.stock_data_path + str(stock_code) + '.csv', parse_dates=['date'])
    benchmark = pd.read_csv(config.index_data_path + str(index_code) + '.csv', parse_dates=['date'])
    date = pd.date_range(start_date, end_date)  # 生成日期序列

    # 选取在日期范围内的股票数据序列并按日期排序
    stock_data = stock_data.loc[stock_data['date'].isin(date), ['date', 'change', 'adjust_price']]
    stock_data.sort_values(by='date', inplace=True)

    # 选取在日期范围内的指数数据序列并按日期排序
    date_list = list(stock_data['date'])

    benchmark = benchmark.loc[benchmark['date'].isin(date_list), ['date', 'change', 'close']]

    benchmark.sort_values(by='date', inplace=True)
    benchmark.set_index('date', inplace=True)

    # 将回测要用到的各个数据序列转成list格式
    # date_line = list(benchmark.index.strftime('%Y-%m-%d'))  # 日期序列
    capital_line = list(stock_data['adjust_price'])  # 账户价值序列
    return_line = list(stock_data['change'])  # 收益率序列
    indexreturn_line = list(benchmark['change'])  # 指数的变化率序列
    index_line = list(benchmark['close'])  # 指数序列

    date_line = list(benchmark.index)  # 日期序列
    # capital_line = stock_data['adjust_price']  # 账户价值序列
    # return_line = stock_data['change']  # 收益率序列
    # indexreturn_line = benchmark['change']  # 指数的变化率序列
    # index_line = benchmark['close']  # 指数序列

    return date_line, capital_line, return_line, index_line, indexreturn_line


# 计算年化收益率函数
def annual_return(date_line, capital_line):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :return: 输出在回测期间的年化收益率
    """
    # 将数据序列合并成dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line})
    df.sort_values(by='date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    # rng = pd.period_range(df['date'].iloc[0], df['date'].iloc[-1], freq='D')
    # 计算年化收益率

    # 考虑到股票停牌, 网上使用的交易日天数/250这种方式计算年化收益不太准确, 所以这里用自然日的天数/365
    annual = pow(df.loc[len(df.index) - 1, 'capital'] / df.loc[0, 'capital'], 250 / len(df.index)) - 1
    return annual


# 计算最大回撤函数
def max_drawdown(date_line, capital_line):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :return: 输出最大回撤及开始日期和结束日期
    """
    # 将数据序列合并为一个dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line})
    df.sort_values(by='date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    df['max2here'] = df['capital'].cummax()  # 计算当日之前的账户最大价值
    df['dd2here'] = df['capital'] / df['max2here'] - 1  # 计算当日的回撤

    # 计算最大回撤和结束时间
    temp = df.sort_values(by='dd2here').iloc[0][['date', 'dd2here']]
    max_dd = temp['dd2here']
    end_date = temp['date']

    # 计算开始时间
    df = df[df['date'] <= end_date]
    start_date = df.sort_values(by='capital', ascending=False).iloc[0]['date']

    return max_dd, start_date, end_date


# 计算平均涨幅
def average_change(date_line, return_line):
    """
    :param date_line: 日期序列
    :param return_line: 账户日收益率序列
    :return: 输出平均涨幅
    """
    df = pd.DataFrame({'date': date_line, 'rtn': return_line})
    ave = df['rtn'].mean()
    return ave


# 计算上涨概率
def prob_up(date_line, return_line):
    """
    :param date_line: 日期序列
    :param return_line: 账户日收益率序列
    :return: 输出上涨概率
    """
    df = pd.DataFrame({'date': date_line, 'rtn': return_line})
    df.loc[df['rtn'] > 0, 'rtn'] = 1  # 收益率大于0的记为1
    df.loc[df['rtn'] <= 0, 'rtn'] = 0  # 收益率小于等于0的记为0
    # 统计1和0各出现的次数
    count = df['rtn'].value_counts()
    p_up = count.loc[1] / len(df.index)
    return p_up


# 计算最大连续上涨天数和最大连续下跌天数
def max_successive_up(date_line, return_line):
    """
    :param date_line: 日期序列
    :param return_line: 账户日收益率序列
    :return: 输出最大连续上涨天数和最大连续下跌天数
    """
    df = pd.DataFrame({'date': date_line, 'rtn': return_line})
    # 新建一个全为空值的series,并作为dataframe新的一列
    s = pd.Series(np.nan, index=df.index)
    s.name = 'up'
    df = pd.concat([df, s], axis=1)

    # 当收益率大于0时，up取1，小于0时，up取0，等于0时采用前向差值
    df.loc[df['rtn'] > 0, 'up'] = 1
    df.loc[df['rtn'] < 0, 'up'] = 0
    df['up'].fillna(method='ffill', inplace=True)

    # 根据up这一列计算到某天为止连续上涨下跌的天数
    rtn_list = list(df['up'])
    successive_up_list = []
    num = 1
    for i in range(len(rtn_list)):
        if i == 0:
            successive_up_list.append(num)
        else:
            if (rtn_list[i] == rtn_list[i - 1] == 1) or (rtn_list[i] == rtn_list[i - 1] == 0):
                num += 1
            else:
                num = 1
            successive_up_list.append(num)
    # 将计算结果赋给新的一列'successive_up'
    df['successive_up'] = successive_up_list
    # 分别在上涨和下跌的两个dataframe里按照'successive_up'的值排序并取最大值
    max_successive_up = df[df['up'] == 1].sort_values(by='successive_up', ascending=False)['successive_up'].iloc[0]
    max_successive_down = df[df['up'] == 0].sort_values(by='successive_up', ascending=False)['successive_up'].iloc[0]
    return max_successive_up, max_successive_down


# 计算最大单周期涨幅和最大单周期跌幅
def max_period_return(date_line, return_line):
    """
    :param date_line: 日期序列
    :param return_line: 账户日收益率序列
    :return: 输出最大单周期涨幅和最大单周期跌幅
    """
    df = pd.DataFrame({'date': date_line, 'rtn': return_line})
    # 分别计算日收益率的最大值和最小值
    max_return = df['rtn'].max()
    min_return = df['rtn'].min()
    return max_return, min_return


# 计算收益波动率的函数
def volatility(date_line, return_line):
    """
    :param date_line: 日期序列
    :param return_line: 账户日收益率序列
    :return: 输出回测期间的收益波动率
    """
    from math import sqrt
    df = pd.DataFrame({'date': date_line, 'rtn': return_line})
    # 计算波动率
    vol = df['rtn'].std() * sqrt(250)
    return vol


# 计算贝塔的函数
def beta(date_line, return_line, indexreturn_line):
    """
    :param date_line: 日期序列
    :param return_line: 账户日收益率序列
    :param indexreturn_line: 指数的收益率序列
    :return: 输出beta值
    """
    df = pd.DataFrame({'date': date_line, 'rtn': return_line, 'benchmark_rtn': indexreturn_line})
    # 账户收益和基准收益的协方差除以基准收益的方差
    b = df['rtn'].cov(df['benchmark_rtn']) / df['benchmark_rtn'].var()
    return b


# 计算alpha的函数
def alpha(date_line, capital_line, index_line, return_line, indexreturn_line, rf=0.0284):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :param index_line: 指数序列
    :param return_line: 账户日收益率序列
    :param indexreturn_line: 指数的收益率序列
    :param rf: 无风险利率取10年期国债的到期年化收益率
    :return: 输出alpha值
    """
    # 将数据序列合并成dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line, 'benchmark': index_line, 'rtn': return_line,
                       'benchmark_rtn': indexreturn_line})
    df.sort_values(by='date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    annual_stock = pow(df.loc[len(df.index) - 1, 'capital'] / df.loc[0, 'capital'], 250 / len(df.index)) - 1  # 账户年化收益
    annual_index = pow(df.loc[len(df.index) - 1, 'benchmark'] / df.loc[0, 'benchmark'],
                       250 / len(df.index)) - 1  # 基准年化收益

    beta = df['rtn'].cov(df['benchmark_rtn']) / df['benchmark_rtn'].var()  # 计算贝塔值
    a = (annual_stock - rf) - beta * (annual_index - rf)  # 计算alpha值
    return a


# 计算夏普比函数
def sharpe_ratio(date_line, capital_line, return_line, rf=0.0284):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :param return_line: 账户日收益率序列
    :param rf, 无风险利率, 默认值为10年期国债的到期年化收益率
    :return: 输出夏普比率
    """
    from math import sqrt
    # 将数据序列合并为一个dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line, 'rtn': return_line})
    df.sort_values(by='date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    # rng = pd.period_range(df['date'].iloc[0], df['date'].iloc[-1], freq='D')
    # 账户年化收益
    annual_stock = pow(df.loc[len(df.index) - 1, 'capital'] / df.loc[0, 'capital'], 250 / len(df.index)) - 1
    # 计算收益波动率
    volatility = df['rtn'].std() * sqrt(250)
    # 计算夏普比
    sharpe = (annual_stock - rf) / volatility
    return sharpe


# 计算信息比率函数
def info_ratio(date_line, return_line, indexreturn_line):
    """
    :param date_line: 日期序列
    :param return_line: 账户日收益率序列
    :param indexreturn_line: 指数的收益率序列
    :return: 输出信息比率
    """
    from math import sqrt
    df = pd.DataFrame({'date': date_line, 'rtn': return_line, 'benchmark_rtn': indexreturn_line})
    df['diff'] = df['rtn'] - df['benchmark_rtn']
    annual_mean = df['diff'].mean() * 250
    annual_std = df['diff'].std() * sqrt(250)
    info_ratio = annual_mean / annual_std
    return info_ratio


# 计算股票和基准在回测期间的累计收益率并画图
def cumulative_return(date_line, return_line, indexreturn_line):
    """
    :param date_line: 日期序列
    :param return_line: 账户日收益率序列
    :param indexreturn_line: 指数日收益率序列
    :return: 画出股票和基准在回测期间的累计收益率的折线图
    """
    df = pd.DataFrame({'date': date_line, 'rtn': return_line, 'benchmark_rtn': indexreturn_line})
    df['stock_cumret'] = (df['rtn'] + 1).cumprod()
    df['benchmark_cumret'] = (df['benchmark_rtn'] + 1).cumprod()
    # 画出股票和基准在回测期间的累计收益率的折线图
    df['stock_cumret'].plot(style='b-', figsize=(12, 5))
    df['benchmark_cumret'].plot(style='r-', figsize=(12, 5))
    plt.show()


def period_win_rate(date_line, change_line, period='M'):
    """
    :param date_line: 日期序列
    :param change_line: 账户每日收益序列, 每日涨跌幅
    :param period: 指定计算胜率的周期, A: 计算年度胜率, M: 计算月度胜率, W: 计算周度胜率
    :return:
    """

    df = pd.DataFrame({'交易日期': date_line, '涨跌幅': change_line})
    df.set_index('交易日期', inplace=True)

    period_rtn = period_return(date_line, change_line, period)
    return len(period_rtn[period_rtn['涨跌幅'] > 0]) * 1.0 / len(period_rtn)


def period_return(date_line, change_line, period='M'):
    """
    :param date_line: 日期序列
    :param change_line: 账户每日收益序列, 每日涨跌幅
    :param period: 指定计算胜率的周期, A: 计算年度胜率, M: 计算月度胜率, W: 计算周度胜率
    :return: 返回指定周期内的回报率
    """

    df = pd.DataFrame({'交易日期': date_line, '涨跌幅': change_line})
    df.set_index('交易日期', inplace=True)

    print(df["2015-12-31":"2016-12-31"])

    # pandas的采样不是按周、月、年等间隔采样, 而是按照自然周、年、月的起始时间分割数据
    return df.resample(period).apply(lambda x: (x + 1.0).prod() - 1.0)


# 测试指标计算函数
if __name__ == '__main__':
    # 调用get_stock_data函数读取数据
    date_line, capital_line, return_line, index_line, indexreturn_line = get_stock_data('sz000002', 'sh000001',
                                                                                        '2006-01-01',
                                                                                        '2019-12-31')

    # 年化收益率
    print("年化收益: %.2f" % annual_return(date_line, capital_line))
    # 最大回撤
    print("最大回撤: %.2f, 最大回撤开始时间: %s, 最大回撤结束时间: %s" % max_drawdown(date_line, capital_line))
    # 平均涨幅
    print("平均涨幅: %.2f" % average_change(date_line, return_line))
    # 上涨概率
    print("上涨概率: %.2f" % prob_up(date_line, return_line))
    # 最大连续上涨天数和最大连续下跌天数
    print("最大连续上涨天数: %d, 最大连续下跌天数: %d" % max_successive_up(date_line, return_line))
    # 最大单周期涨幅和最大单周期跌幅
    print("单日最大涨幅: %.2f, 单日最大跌幅: %.2f" % max_period_return(date_line, return_line))
    # 收益波动率
    print("波动收益率: %.2f" % volatility(date_line, return_line))
    # beta值
    print("beta值: %.2f" % beta(date_line, return_line, indexreturn_line))
    # alpha值
    print("alpha值: %.2f" % alpha(date_line, capital_line, index_line, return_line, indexreturn_line))
    # 夏普比率
    print("夏普比率: %.2f" % sharpe_ratio(date_line, capital_line, return_line))
    # 信息比率
    print("信息比率: %.2f" % info_ratio(date_line, return_line, indexreturn_line))
    # 画出累积收益率曲线图
    cumulative_return(date_line, return_line, indexreturn_line)

    # benchmark = pd.read_csv(config.index_data_path + 'sh000001' + '.csv', parse_dates=['date'])
    #
    # benchmark = benchmark[benchmark['date'] >= '2015-01-01']
    # benchmark.set_index('date', inplace=True)
    #
    # year_win_rate = period_win_rate(list(benchmark.index), benchmark['change'], period='A')
    # year_rtn = period_return(list(benchmark.index), benchmark['change'], period='A')
    #
    # print(year_win_rate)
    # print(year_rtn)
    #
    # plot_year_return(year_rtn, show=True)
    #
    # print(list(year_rtn.index.year))
    # print(list(year_rtn['涨跌幅']))

    # plot_back_line(pd.DataFrame({
    #     "交易日期": date_line,
    #     "策略收益": [elem / capital_line[0] - 1 for elem in capital_line],
    #     "基准收益": [elem / index_line[0] - 1 for elem in index_line],
    # }), show=True)
