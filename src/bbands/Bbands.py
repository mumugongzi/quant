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

import os
import pandas as pd
import warnings

from common import config
from common import indicator

import matplotlib.pyplot as plt

plt.rcParams['font.family'] = ['SimHei']

warnings.filterwarnings("ignore")


# 计算复权价格
def cal_right_price(input_stock_data, type='前复权'):
    """
    :param input_stock_data: 标准股票数据，需要'收盘价', '涨跌幅'
    :param type: 确定是前复权还是后复权，分别为'后复权'，'前复权'
    :return: 新增一列'后复权价'/'前复权价'的stock_data
    """
    # 计算收盘复权价
    stock_data = input_stock_data.copy()
    num = {'后复权': 0, '前复权': -1}
    price1 = stock_data['close'].iloc[num[type]]
    stock_data['复权价_temp'] = (stock_data['change'] + 1.0).cumprod()
    price2 = stock_data['复权价_temp'].iloc[num[type]]
    stock_data['复权价'] = stock_data['复权价_temp'] * (price1 / price2)
    stock_data.pop('复权价_temp')

    # 计算开盘复权价
    stock_data['复权价_开盘'] = stock_data['复权价'] / (stock_data['close'] / stock_data['open'])
    stock_data['复权价_最高'] = stock_data['复权价'] / (stock_data['close'] / stock_data['high'])
    stock_data['复权价_最低'] = stock_data['复权价'] / (stock_data['close'] / stock_data['low'])

    return stock_data[['复权价_开盘', '复权价', '复权价_最高', '复权价_最低']]


# 获取指定股票对应的数据并按日期升序排序
def get_stock_data(stock_code):
    """
    :param stock_code: 股票代码
    :return: 返回股票数据集（代码，日期，开盘价，收盘价，涨跌幅）
    """
    # 此处为存放csv文件的本地路径，请自行改正地址
    stock_data = pd.read_csv(config.stock_data_path + str(stock_code) + '.csv', parse_dates=['date'], index_col='date')
    stock_data = stock_data[['code', 'open', 'close', 'high', 'low', 'change']]
    stock_data.sort_index(inplace=True)

    # 计算复权价
    stock_data[['open', 'close', 'high', 'low']] = cal_right_price(stock_data, type='后复权')

    stock_data = stock_data['2005-01-01':]

    return stock_data


# 计算布林带指标并得到信号和仓位
def bands(stock_data, n=14):
    df = stock_data.copy()

    # 计算布林带的中轨线、上轨线和下轨线
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3

    df['middle'] = df['tp'].rolling(n).mean()
    df['sd'] = df['tp'].rolling(n).std()

    df['up'] = df['middle'] + 2 * df['sd']
    df['down'] = df['middle'] - 2 * df['sd']

    df.dropna(inplace=True)

    # 当收盘价上穿上轨线，买入，信号为1
    df.loc[df['close'] > df['up'], 'signal'] = 1
    # 当收盘价下穿下轨线，卖空，信号为-1
    df.loc[df['close'] < df['down'], 'signal'] = -1

    df['signal'].fillna(method='ffill', inplace=True)

    # =====计算每天的仓位
    df.iloc[0]['position'] = 0
    # 出现买入信号而且第二天开盘没有涨停
    df.loc[(df['signal'].shift(1) == 1) & (df['open'] < df['close'].shift(1) * 1.097), 'position'] = 1
    # 出现卖出信号而且第二天开盘没有跌停
    df.loc[(df['signal'].shift(1) == -1) & (df['open'] > df['close'].shift(1) * 0.903), 'position'] = 0

    df['position'].fillna(method='ffill', inplace=True)

    return df


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
    df.loc[df['position'] > df['position'].shift(1), 'capital_rtn'] = (df['close'] / df['open'] - 1) * (
            1 - slippage - commision_rate) * (df['position'] - df['position'].shift(1)) + df['change'] * df[
                                                                          'position'].shift(1)
    # 当减仓时,计算当天资金曲线涨幅capital_rtn.capital_rtn = 今天开盘卖出的positipn在今天的涨幅(扣除手续费) + 还剩的position在今天的涨幅
    df.loc[df['position'] < df['position'].shift(1), 'capital_rtn'] = (df['open'] / df['close'].shift(1) - 1) * (
            1 - slippage - commision_rate) * (df['position'].shift(1) - df['position']) + df['change'] * df['position']
    # 当仓位不变时,当天的capital_rtn是当天的change * position
    df.loc[df['position'] == df['position'].shift(1), 'capital_rtn'] = df['change'] * df['position']
    return df


# 计算年化收益率函数
def annual_return(date_line, capital_line):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :return: 输出在回测期间的年化收益率
    """
    # 将数据序列合并成dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line})
    df = df[df['capital'].notnull()]

    # 计算年化收益率
    annual = (df['capital'].iloc[-1] / df['capital'].iloc[0]) ** (250 / len(df)) - 1

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

    df['max2here'] = pd.expanding_max(df['capital'])  # 计算当日之前的账户最大价值
    df['dd2here'] = df['capital'] / df['max2here'] - 1  # 计算当日的回撤
    #  计算最大回撤和结束时间
    temp = df.sort_values(by='dd2here').iloc[0][['date', 'dd2here']]
    max_dd = temp['dd2here']

    return max_dd


# 遍历数据文件夹中所有股票文件的文件名，得到股票代码列表
stock_code_list = []
# 此处为股票数据文件的本地路径，请自行修改
for root, dirs, files in os.walk(config.stock_data_path):
    if files:
        for f in files:
            if '.csv' in f:
                stock_code_list.append(f.split('.csv')[0])

# stock_code_list = stock_code_list[3900:]
progress = 0

re = pd.DataFrame(
    columns=['code', 'start', 'param', 'stock_rtn', 'stock_md', 'stock_md_start', 'stock_md_end', 'strategy_rtn',
             'strategy_md', 'strategy_md_start', 'strategy_md_end', 'excessive_rtn'])

param_list = range(10, 31, 2)
i = 0
for code in stock_code_list:
    progress = progress + 1
    print("progress: %d/%d" % (progress, len(stock_code_list)))

    stock_data = get_stock_data(code)

    # 剔除上市不到1年半的股票
    if len(stock_data) < 360:
        continue

    for p in param_list:
        df = bands(stock_data, n=p)
        # 计算策略每天涨幅
        df = account(df, slippage=0, commision_rate=0)
        # 计算资金曲线
        df['capital'] = (df['capital_rtn'] + 1).cumprod()

        # =====根据资金曲线,计算相关评价指标
        df = df['2006-01-01':]
        date_line = list(df.index)
        capital_line = list(df['capital'])
        stock_line = list(df['close'])
        # 股票的年化收益
        stock_rtn = annual_return(date_line, stock_line)

        # 策略的年化收益
        strategy_rtn = annual_return(date_line, capital_line)
        # 股票最大回撤
        stock_md, stock_md_start, stock_md_end = indicator.max_drawdown(date_line, stock_line)
        # 策略最大回撤
        strategy_md, strategy_md_start, strategy_md_end = indicator.max_drawdown(date_line, capital_line)

        re.loc[i, 'code'] = df['code'].iloc[0]
        re.loc[i, 'start'] = df.index[0].strftime('%Y-%m-%d')
        re.loc[i, 'param'] = p
        re.loc[i, 'stock_rtn'] = stock_rtn
        re.loc[i, 'stock_md'] = stock_md
        re.loc[i, 'stock_md_start'] = stock_md_start.strftime('%Y-%m-%d')
        re.loc[i, 'stock_md_end'] = stock_md_end.strftime('%Y-%m-%d')
        re.loc[i, 'strategy_rtn'] = strategy_rtn
        re.loc[i, 'strategy_md'] = strategy_md
        re.loc[i, 'strategy_md_start'] = strategy_md_start.strftime('%Y-%m-%d')
        re.loc[i, 'strategy_md_end'] = strategy_md_end.strftime('%Y-%m-%d')
        re.loc[i, 'excessive_rtn'] = strategy_rtn - stock_rtn

        i += 1

    # re.sort_values(by='excessive_rtn', ascending=False, inplace=True)

statis_df = pd.DataFrame(columns=['param', 'stock_rtn', 'strategy_rtn', 'excessive_rtn', 'excessive_ratio'])
for p in param_list:
    re_p = re[re['param'] == p]

    idx = len(statis_df)
    statis_df.loc[idx, 'param'] = p
    statis_df.loc[idx, 'stock_rtn'] = re_p['stock_rtn'].mean()
    statis_df.loc[idx, 'strategy_rtn'] = re_p['strategy_rtn'].mean()
    statis_df.loc[idx, 'excessive_rtn'] = re_p['excessive_rtn'].mean()
    statis_df.loc[idx, 'excessive_ratio'] = len(re_p[re_p['excessive_rtn'] > 0]) * 1.0 / len(re_p)



re.to_csv(config.output_data_path + "bbands.csv", mode='w', index=False)

plt.subplot(2, 1, 1)
plt.plot(statis_df['param'], statis_df['stock_rtn'], label='股票平均收益')
plt.plot(statis_df['param'], statis_df['strategy_rtn'], label='策略收益')
plt.plot(statis_df['param'], statis_df['excessive_rtn'], label='超额收益')
plt.xlabel('布林通道参数')
plt.ylabel('收益')
plt.title('策略收益对比')
plt.legend()

plt.subplot(2, 1, 2)
plt.plot(statis_df['param'], statis_df['excessive_ratio'])
plt.xlabel('布林通道参数')
plt.ylabel('比例')
plt.title('超额收益大于0股票占比')

plt.show()
