# coding=utf-8
"""
本系列帖子“量化小讲堂”，通过实际案例教初学者使用python、pandas进行金融数据处理，希望能对大家有帮助。


必读文章《10年400倍策略分享-附视频逐行讲解代码》：http://bbs.pinggu.org/thread-5558776-1-1.html


所有系列文章汇总请见：http://bbs.pinggu.org/thread-3950124-1-1.html


想要快速、系统的学习量化知识，可以参与我与论坛合作开设的《python量化投资入门》视频课程：http://www.peixun.net/view/1028.html，我会亲自授课，随问随答。
参与课程还可以免费加入我的小密圈，我每天会在圈中分享量化的所见所思，圈子介绍：http://t.xiaomiquan.com/BEiqzVB


微信：xbx_laoshi，量化交流Q群(快满)：438143420，有问题欢迎交流。


文中用到的A股数据可在www.yucezhe.com下载，这里可以下载到所有股票、从上市日起的交易数据、财务数据、分钟数据、分笔数据、逐笔数据等。
"""
from __future__ import division

import pandas as pd
import warnings

from common.indicator import *
from common.Functions import *

warnings.filterwarnings("ignore")


# 获取指定股票对应的数据并按日期升序排序
def get_stock_data(stock_code):
    """
    :param stock_code: 股票代码
    :return: 返回股票数据集（代码，日期，开盘价，收盘价，涨跌幅）
    """
    # 此处为存放csv文件的本地路径，请自行改正地址
    stock_data = import_stock_data(stock_code, columns=['股票代码', '交易日期', '开盘价', '收盘价', '涨跌幅'])
    stock_data.sort_values(by='交易日期', inplace=True)
    stock_data.reset_index(drop=True, inplace=True)
    # 计算复权价
    stock_data[['开盘价', '收盘价']] = cal_right_price(stock_data, right_type='后复权', price_columns=['开盘价', '收盘价'])

    return stock_data

# 获取指定股票对应的数据并按日期升序排序
def get_index_data(index_code):
    """
    :param stock_code: 股票代码
    :return: 返回股票数据集（代码，日期，开盘价，收盘价，涨跌幅）
    """
    # 此处为存放csv文件的本地路径，请自行改正地址
    index_data = import_index_data(index_code, columns=['指数代码', '交易日期', '开盘价', '收盘价', '涨跌幅'])


    index_data = index_data.rename(columns={"指数代码": "股票代码"})
    index_data.sort_values(by='交易日期', inplace=True)
    index_data.reset_index(drop=True, inplace=True)

    return index_data


# 判断交易天数,如果不满足就不运行程序
def stock_trading_days(stock_data, trading_days=500):
    """
    :param stock_data: 股票数据集
    :param trading_days: 交易天数下限，默认为500
    :return: 判断股票的交易天数是否大于trading_days,如果不满足就退出程序
    """
    if len(stock_data) < trading_days:
        print('股票上市时间过短,不运行策略')
        exit(1)


# 简单均线策略,输出每天的仓位
def simple_ma(stock_data, window_short=5, window_long=60):
    """
    :param stock_data: 股票数据集
    :param window_short: 较短的窗口期
    :param window_long: 较长的窗口期
    :return: 当天收盘时持有该股票的仓位。

    最简单的均线策略。当天收盘后，短期均线上穿长期均线的时候，在第二天开盘买入。当短期均线下穿长期均线的时候，在第二天开盘卖出。每次都是全仓买卖.

    """
    # 计算短期和长期的移动平均线
    stock_data['ma_short'] = stock_data['收盘价'].rolling(window_short, min_periods=1).mean()
    stock_data['ma_long'] = stock_data['收盘价'].rolling(window_long, min_periods=1).mean()

    # 出现买入信号而且第二天开盘没有涨停
    stock_data.loc[(stock_data['ma_short'].shift(1) > stock_data['ma_long'].shift(1)) &
                  (stock_data['开盘价'] < stock_data['收盘价'].shift(1) * 1.097), 'position'] = 1
    # 出现卖出信号而且第二天开盘没有跌停
    stock_data.loc[(stock_data['ma_short'].shift(1) < stock_data['ma_long'].shift(1)) &
                  (stock_data['开盘价'] > stock_data['收盘价'].shift(1) * 0.903), 'position'] = 0

    stock_data['position'].fillna(method='ffill', inplace=True)
    stock_data['position'].fillna(0, inplace=True)

    return stock_data[['股票代码', '交易日期', '开盘价', '收盘价', '涨跌幅', 'position']]


# 根据每日仓位计算总资产的日收益率
def account(df, slippage=1.0 / 1000, commision_rate=2.0 / 1000):
    """
    :param df: 股票账户数据集
    :param slippage: 买卖滑点 默认为1.0 / 1000
    :param commision_rate: 手续费 默认为2.0 / 1000
    :return: 返回账户资产的日收益率和日累计收益率的数据集
    """
    df.iloc[0]['capital_rtn'] = 0
    # 当加仓时,计算当天资金曲线涨幅capital_rtn.capital_rtn = 昨天的position在今天涨幅 + 今天开盘新买入的position在今天的涨幅(扣除手续费)
    df.loc[df['position'] > df['position'].shift(1), 'capital_rtn'] = (df['收盘价'] / df['开盘价'] - 1) * (
            1 - slippage - commision_rate) * (df['position'] - df['position'].shift(1)) + df['涨跌幅'] * df[
                                                                          'position'].shift(1)
    # 当减仓时,计算当天资金曲线涨幅capital_rtn.capital_rtn = 今天开盘卖出的positipn在今天的涨幅(扣除手续费) + 还剩的position在今天的涨幅
    df.loc[df['position'] < df['position'].shift(1), 'capital_rtn'] = (df['开盘价'] / df['收盘价'].shift(1) - 1) * (
            1 - slippage - commision_rate) * (df['position'].shift(1) - df['position']) + df['涨跌幅'] * df['position']
    # 当仓位不变时,当天的capital_rtn是当天的change * position
    df.loc[df['position'] == df['position'].shift(1), 'capital_rtn'] = df['涨跌幅'] * df['position']
    return df


# 选取时间段,来计算资金曲线.
def select_date_range(stock_data, start_date=pd.to_datetime('20060101'), trading_days=250):
    """
    :param stock_data:
    :param start_date:
    :param trading_days:
    :return: 对于一个指定的股票,计算它回测资金曲线的时候,从它上市交易了trading_days天之后才开始计算,并且最早不早于start_date.
    """
    stock_data = stock_data[trading_days:]
    stock_data = stock_data[stock_data['交易日期'] >= start_date]
    stock_data.reset_index(inplace=True, drop=True)
    return stock_data


# 计算最近250天的股票,策略累计涨跌幅.以及每年（月，周）股票和策略收益
def period_return(stock_data, days=250, if_print=False):
    """
    :param stock_data: 包含日期、股票涨跌幅和总资产涨跌幅的数据集
    :param days: 最近250天
    :return: 输出最近250天的股票和策略累计涨跌幅以及每年的股票收益和策略收益
    """
    df = stock_data[['股票代码', '交易日期', '涨跌幅', 'capital_rtn']]

    # 计算每一年(月,周)股票,资金曲线的收益
    year_rtn = df.set_index('交易日期')[['涨跌幅', 'capital_rtn']].resample('A').apply(lambda x: (x + 1.0).prod() - 1.0)
    month_rtn = df.set_index('交易日期')[['涨跌幅', 'capital_rtn']].resample('M').apply(lambda x: (x + 1.0).prod() - 1.0)
    week_rtn = df.set_index('交易日期')[['涨跌幅', 'capital_rtn']].resample('W').apply(lambda x: (x + 1.0).prod() - 1.0)

    year_rtn.dropna(inplace=True)
    month_rtn.dropna(inplace=True)
    week_rtn.dropna(inplace=True)

    # 计算策略的年（月，周）胜率
    yearly_win_rate = len(year_rtn[year_rtn['capital_rtn'] > 0]) / len(year_rtn[year_rtn['capital_rtn'] != 0])
    monthly_win_rate = len(month_rtn[month_rtn['capital_rtn'] > 0]) / len(month_rtn[month_rtn['capital_rtn'] != 0])
    weekly_win_rate = len(week_rtn[week_rtn['capital_rtn'] > 0]) / len(week_rtn[week_rtn['capital_rtn'] != 0])

    # 计算股票的年（月，周）胜率
    yearly_win_rates = len(year_rtn[year_rtn['涨跌幅'] > 0]) / len(year_rtn[year_rtn['涨跌幅'] != 0])
    monthly_win_rates = len(month_rtn[month_rtn['涨跌幅'] > 0]) / len(month_rtn[month_rtn['涨跌幅'] != 0])
    weekly_win_rates = len(week_rtn[week_rtn['涨跌幅'] > 0]) / len(week_rtn[week_rtn['涨跌幅'] != 0])

    # 计算最近days的累计涨幅
    df = df.iloc[-days:]
    recent_rtn_line = df[['交易日期']]
    recent_rtn_line['stock_rtn_line'] = (df['涨跌幅'] + 1).cumprod() - 1
    recent_rtn_line['strategy_rtn_line'] = (df['capital_rtn'] + 1).cumprod() - 1
    recent_rtn_line.reset_index(drop=True, inplace=True)

    # 输出
    if if_print:
        # print('\n最近' + str(days) + '天股票和策略的累计涨幅:')
        # print(recent_rtn_line)
        # print('\n过去每一年股票和策略的收益:')
        # print(year_rtn)
        print('策略年胜率为：%f' % yearly_win_rate)
        print('股票年胜率为：%f' % yearly_win_rates)
        # print('\n过去每一月股票和策略的收益:')
        # print(month_rtn)
        print('策略月胜率为：%f' % monthly_win_rate)
        print('股票月胜率为：%f' % monthly_win_rates)
        # print('\n过去每一周股票和策略的收益:')
        # print(week_rtn)
        print('策略周胜率为：%f' % weekly_win_rate)
        print('股票周胜率为：%f' % weekly_win_rates)

    return year_rtn, month_rtn, week_rtn, recent_rtn_line


# 根据每次买入的结果,计算相关指标
def trade_describe(df):
    """
    :param df: 包含日期、仓位和总资产的数据集
    :return: 输出账户交易各项指标
    """
    # 计算资金曲线
    df['capital'] = (df['capital_rtn'] + 1).cumprod()
    # 记录买入或者加仓时的日期和初始资产
    df.loc[df['position'] > df['position'].shift(1), 'start_date'] = df['交易日期']
    df.loc[df['position'] > df['position'].shift(1), 'start_capital'] = df['capital'].shift(1)
    df.loc[df['position'] > df['position'].shift(1), 'start_stock'] = df['收盘价'].shift(1)
    # 记录卖出时的日期和当天的资产
    df.loc[df['position'] < df['position'].shift(1), 'end_date'] = df['交易日期']
    df.loc[df['position'] < df['position'].shift(1), 'end_capital'] = df['capital']
    df.loc[df['position'] < df['position'].shift(1), 'end_stock'] = df['收盘价']
    # 将买卖当天的信息合并成一个dataframe
    df_temp = df[df['start_date'].notnull() | df['end_date'].notnull()]

    df_temp['end_date'] = df_temp['end_date'].shift(-1)
    df_temp['end_capital'] = df_temp['end_capital'].shift(-1)
    df_temp['end_stock'] = df_temp['end_stock'].shift(-1)

    # 构建账户交易情况dataframe：'hold_time'持有天数，'trade_return'该次交易盈亏,'stock_return'同期股票涨跌幅
    trade = df_temp.loc[df_temp['end_date'].notnull(), ['start_date', 'start_capital', 'start_stock',
                                                       'end_date', 'end_capital', 'end_stock']]
    trade.reset_index(drop=True, inplace=True)
    trade['hold_time'] = (trade['end_date'] - trade['start_date']).dt.days
    trade['trade_return'] = trade['end_capital'] / trade['start_capital'] - 1
    trade['stock_return'] = trade['end_stock'] / trade['start_stock'] - 1

    trade_num = len(trade)  # 计算交易次数
    max_holdtime = trade['hold_time'].max()  # 计算最长持有天数
    average_change = trade['trade_return'].mean()  # 计算每次平均涨幅
    max_gain = trade['trade_return'].max()  # 计算单笔最大盈利
    max_loss = trade['trade_return'].min()  # 计算单笔最大亏损
    total_years = (trade['end_date'].iloc[-1] - trade['start_date'].iloc[0]).days / 365
    trade_per_year = trade_num / total_years  # 计算年均买卖次数

    # 计算连续盈利亏损的次数
    trade.loc[trade['trade_return'] > 0, 'gain'] = 1
    trade.loc[trade['trade_return'] < 0, 'gain'] = 0
    trade['gain'].fillna(method='ffill', inplace=True)
    # 根据gain这一列计算连续盈利亏损的次数
    rtn_list = list(trade['gain'])
    successive_gain_list = []
    num = 1
    for i in range(len(rtn_list)):
        if i == 0:
            successive_gain_list.append(num)
        else:
            if (rtn_list[i] == rtn_list[i - 1] == 1) or (rtn_list[i] == rtn_list[i - 1] == 0):
                num += 1
            else:
                num = 1
            successive_gain_list.append(num)
    # 将计算结果赋给新的一列'successive_gain'
    trade['successive_gain'] = successive_gain_list
    # 分别在盈利和亏损的两个dataframe里按照'successive_gain'的值排序并取最大值
    max_successive_gain = \
        trade[trade['gain'] == 1].sort_values(by='successive_gain', ascending=False)['successive_gain'].iloc[0]
    max_successive_loss = \
        trade[trade['gain'] == 0].sort_values(by='successive_gain', ascending=False)['successive_gain'].iloc[0]

    #  输出账户交易各项指标
    # print('\n==============每笔交易收益率及同期股票涨跌幅===============')
    # print(trade[['start_date', 'end_date', 'trade_return', 'stock_return']])
    print('\n====================账户交易的各项指标=====================')
    print('交易次数为：%d   最长持有天数为：%d' % (trade_num, max_holdtime))
    print('每次平均涨幅为：%f' % average_change)
    print('单次最大盈利为：%f  单次最大亏损为：%f' % (max_gain, max_loss))
    print('年均买卖次数为：%f' % trade_per_year)
    print('最大连续盈利次数为：%d  最大连续亏损次数为：%d' % (max_successive_gain, max_successive_loss))
    return trade


# =====读取数据
# 读取数据
# stock_data = get_stock_data('sh601857')
stock_data = get_index_data('sh000001')
# 判断交易天数是否满足要求
stock_trading_days(stock_data, trading_days=500)

# =====根据策略,计算仓位,资金曲线等
# 计算买卖信号
stock_data = simple_ma(stock_data, window_short=30, window_long=120)
# 计算策略每天涨幅
stock_data = account(stock_data, slippage=0.1 / 1000, commision_rate=0.2 / 1000)
# 选取时间段
return_data = select_date_range(stock_data, start_date=pd.to_datetime('20060101'), trading_days=250)
return_data['capital'] = (return_data['capital_rtn'] + 1).cumprod()

# =====根据策略结果,计算评价指标
# 计算最近250天的股票,策略累计涨跌幅.以及每年（月，周）股票和策略收益
period_return(return_data, days=250, if_print=True)

# 根据每次买卖的结果,计算相关指标
trade_describe(stock_data)

# =====根据资金曲线,计算相关评价指标
date_line = list(return_data['交易日期'])
capital_line = list(return_data['capital'])
stock_line = list(return_data['收盘价'])
print('股票的年化收益为：%.4f' % annual_return(date_line, stock_line))
print('策略的年化收益为：%.4f' % annual_return(date_line, capital_line))
print("股票最大回撤: %.2f, 开始时间: %s, 结束时间: %s" % max_drawdown(date_line, stock_line))
print('策略最大回撤: %.2f, 开始时间: %s, 结束时间: %s' % max_drawdown(date_line, capital_line))
