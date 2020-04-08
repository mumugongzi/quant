# coding: utf-8
"""
计算量化策略相关指标
"""
from __future__ import division
import pandas as pd
from common import config
import numpy as np

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
    # capital_line = list(stock_data['adjust_price'])  # 账户价值序列
    # return_line = list(stock_data['change'])  # 收益率序列
    # indexreturn_line = list(benchmark['change'])  # 指数的变化率序列
    # index_line = list(benchmark['close'])  # 指数序列
    #
    date_line = benchmark.index.to_list()  # 日期序列
    # capital_line = stock_data['adjust_price']  # 账户价值序列
    # return_line = stock_data['change']  # 收益率序列
    # indexreturn_line = benchmark['change']  # 指数的变化率序列
    # index_line = benchmark['close']  # 指数序列

    # return date_line, capital_line, return_line, index_line, indexreturn_line

    # print(date_line)
    # print((stock_data['change'] + 1).cumprod().tolist())
    # print(stock_data['change'].tolist())
    # print(date_line)

    df = pd.DataFrame(
        {
            "交易日期": date_line,
            "策略累计收益率": (stock_data['change'] + 1).cumprod().tolist(),
            "策略涨跌幅": stock_data['change'].tolist(),
            "基准累计收益率": (benchmark['change'] + 1).cumprod().tolist(),
            "基准涨跌幅": benchmark['change'].tolist(),
        }
    )
    df.set_index("交易日期", inplace=True)
    df.sort_index(inplace=True)
    return df


# 计算年化收益率函数
def annual_return(back_df, type='策略'):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :param type: '策略': 计算策略平均年化收益率, '基准': 计算基准平均年化收益率
    :return: 输出在回测期间的年化收益率
    """
    # 考虑到股票停牌, 网上使用的交易日天数/250这种方式计算年化收益不太准确, 所以这里用自然日的天数/365

    if type not in ['策略', '基准']:
        raise Exception('invalid type ' + type)

    col_name = type + '累计收益率'
    annual = pow(back_df.iloc[len(back_df.index) - 1][col_name] / back_df.iloc[0][col_name],
                 250 / len(back_df.index)) - 1
    return annual


# 计算最大回撤函数
def max_drawdown(back_df):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出最大回撤及开始日期和结束日期
    """
    df = back_df.copy()
    df.reset_index(inplace=True)
    df['max2here'] = df['策略累计收益率'].cummax()  # 计算当日之前的账户最大价值
    df['dd2here'] = df['策略累计收益率'] / df['max2here'] - 1  # 计算当日的回撤



    # 计算最大回撤和结束时间
    temp = df.sort_values(by='dd2here').iloc[0][['交易日期', 'dd2here']]
    max_dd = temp['dd2here']
    end_date = temp['交易日期']

    # 计算开始时间
    df = df[df['交易日期'] <= end_date]
    start_date = df.sort_values(by='策略累计收益率', ascending=False).iloc[0]['交易日期']

    return max_dd, start_date, end_date


# 计算平均涨幅
def average_change(back_df):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出平均涨幅
    """
    ave = back_df['策略涨跌幅'].mean()
    return ave


# 计算最大连续上涨天数和最大连续下跌天数
def max_successive_up(back_df):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出最大连续上涨天数和最大连续下跌天数
    """
    # 新建一个全为空值的series,并作为dataframe新的一列

    df = back_df.copy()
    s = pd.Series(np.nan, index=df.index)
    s.name = '涨跌标记'
    df = pd.concat([df, s], axis=1)

    # 当收益率大于0时，up取1，小于0时，up取0，等于0时采用前向差值
    df.loc[df['策略涨跌幅'] > 0, '涨跌标记'] = 1
    df.loc[df['策略涨跌幅'] < 0, '涨跌标记'] = 0
    df['涨跌标记'].fillna(method='ffill', inplace=True)

    # 根据up这一列计算到某天为止连续上涨下跌的天数
    rtn_list = list(df['涨跌标记'])
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
    df['连续涨跌天数'] = successive_up_list
    # 分别在上涨和下跌的两个dataframe里按照'successive_up'的值排序并取最大值
    max_successive_up = df[df['涨跌标记'] == 1].sort_values(by='连续涨跌天数', ascending=False)['连续涨跌天数'].iloc[0]
    max_successive_down = df[df['涨跌标记'] == 0].sort_values(by='连续涨跌天数', ascending=False)['连续涨跌天数'].iloc[0]
    return max_successive_up, max_successive_down


# 计算最大单周期涨幅和最大单周期跌幅
def max_period_change(back_df, period='M'):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出平均涨幅
    :return: 输出最大单周期涨幅和最大单周期跌幅
    """
    # 分别计算日收益率的最大值和最小值
    max_return = back_df['策略涨跌幅'].resample(period).max()
    min_return = back_df['策略涨跌幅'].resample(period).min()
    return max_return, min_return


# 计算收益波动率的函数
def volatility(back_df):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出回测期间的收益波动率
    """
    from math import sqrt
    # 计算波动率
    vol = back_df['策略涨跌幅'].std() * sqrt(250)
    return vol


# 计算贝塔的函数
def beta(back_df):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出beta值
    """

    # 账户收益和基准收益的协方差除以基准收益的方差
    return back_df['策略涨跌幅'].cov(back_df['基准涨跌幅']) / back_df['基准涨跌幅'].var()


# 计算alpha的函数
def alpha(back_df, rf=0.0284):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出alpha值
    """

    annual_strategy = pow(back_df.iloc[len(back_df.index) - 1]['策略累计收益率'] / back_df.iloc[0]['策略累计收益率'],
                          250 / len(back_df.index)) - 1  # 策略平均年化收益
    annual_benchmark = pow(back_df.iloc[len(back_df.index) - 1]['基准累计收益率'] / back_df.iloc[0]['基准累计收益率'],
                           250 / len(back_df.index)) - 1  # 基准平均年化收益

    b = beta(back_df)
    a = (annual_strategy - rf) - b * (annual_benchmark - rf)  # 计算alpha值
    return a


# 计算夏普比函数
def sharpe_ratio(back_df, rf=0.0284):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出夏普比率
    """
    annual_stock = annual_return(back_df)
    # 计算收益波动率
    v = volatility(back_df)
    # 计算夏普比
    sharpe = (annual_stock - rf) / v
    return sharpe


# 计算信息比率函数
def info_ratio(back_df):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 输出信息比率
    """

    from math import sqrt
    df = back_df.copy()
    df['diff'] = df['策略涨跌幅'] - df['基准涨跌幅']
    annual_mean = df['diff'].mean() * 250
    annual_std = df['diff'].std() * sqrt(250)
    return annual_mean / annual_std


def period_win_rate(back_df, period='M'):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 指定时间周期的胜率
    """
    period_rtn = period_return(back_df, period)
    return len(period_rtn[period_rtn.ge(0)]) * 1.0 / len(period_rtn)


def period_return(back_df, period='M'):
    """
    :param back_df: 索引为交易日期, 按时间升序排列, 包含策略累计收益率, 基准累计收益率, 策略涨跌幅, 基准涨跌幅,
                    策略累计收益率/基准累计收益率: 回测开始到对应日期的累计收益率
                    策略涨跌幅/基准涨跌幅: 当日盈亏除上一日策略总资金
    :return: 返回指定周期内的回报率
    """

    # pandas的采样不是按周、月、年等间隔采样, 而是按照自然周、年、月的起始时间分割数据
    return back_df['策略涨跌幅'].resample(period).apply(lambda x: (x + 1.0).prod() - 1.0)


# 测试指标计算函数
if __name__ == '__main__':
    # 调用get_stock_data函数读取数据
    back_df = get_stock_data('sz000002', 'sh000001', '2006-01-01', '2019-12-31')

    # 年化收益率
    print("年化收益: %.2f" % annual_return(back_df))
    # 最大回撤
    print("最大回撤: %.2f, 最大回撤开始时间: %s, 最大回撤结束时间: %s" % max_drawdown(back_df))
    # 平均涨幅
    print("平均涨幅: %.2f" % average_change(back_df))
    # 上涨概率
    print("上涨概率: %.2f" % period_win_rate(back_df, 'M'))
    # 最大连续上涨天数和最大连续下跌天数
    print("最大连续上涨天数: %d, 最大连续下跌天数: %d" % max_successive_up(back_df))
    # 最大单周期涨幅和最大单周期跌幅
    # print("单日最大涨幅: %.2f, 单日最大跌幅: %.2f" % max_period_return(date_line, return_line))
    # 收益波动率
    print("波动收益率: %.2f" % volatility(back_df))
    # beta值
    print("beta值: %.2f" % beta(back_df))
    # alpha值
    print("alpha值: %.2f" % alpha(back_df))
    # 夏普比率
    print("夏普比率: %.2f" % sharpe_ratio(back_df))
    # 信息比率
    print("信息比率: %.2f" % info_ratio(back_df))

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
    # plot_year_return(back_df)

    # plot_back_line(back_df, show=True)
