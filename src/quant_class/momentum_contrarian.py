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
from common.indicator import *
import os
import pandas as pd
from math import floor

from common import config, Functions
plt.rcParams['font.family'] = ['SimHei']

# 获取股票数据
def get_stock_data():
    # 遍历数据文件夹中所有股票文件的文件名，得到股票代码列表
    stock_code_list = Functions.get_stock_code_list()

    all_stock = pd.DataFrame()

    for code in stock_code_list:
        # 此处为股票数据文件的本地路径，请自行修改
        stock_data = Functions.import_stock_data(code, columns=['股票代码', '交易日期', '开盘价', '收盘价', '涨跌幅'])
        stock_data = stock_data.sort_values(by='交易日期')
        stock_data.reset_index(drop=True, inplace=True)
        # 计算复权价
        stock_data[['开盘价', '收盘价']] = Functions.cal_right_price(stock_data, right_type='后复权', price_columns=['开盘价', '收盘价'])
        # 判断每天开盘是否涨停
        stock_data.loc[stock_data['开盘价'] > stock_data['收盘价'].shift(1) * 1.097, '涨停'] = 1
        stock_data['涨停'].fillna(0, inplace=True)

        all_stock = all_stock.append(stock_data, ignore_index=True)

    return all_stock[['股票代码', '交易日期', '涨跌幅', '涨停']]


def momentum_and_contrarian(all_stock, start_date, end_date, window=3):
    """
    :param all_stock: 所有股票的数据集
    :param start_date: 起始日期（包含排名期）
    :param end_date: 结束日期
    :param window: 排名期的月份数，默认为3个月
    :return: 返回动量策略和反转策略的收益率和资金曲线
    """
    # 取出指数数据作为交易天数的参考标准, 此处为指数数据文件的本地路径，请自行修改
    index_data = Functions.import_index_data('sh000001')
    index_data.set_index('交易日期', inplace=True)
    index_data.sort_index(inplace=True)
    index_data = index_data[start_date:end_date]
    # 转换成月度数据
    by_month = index_data[['收盘价']].resample('M').last()
    by_month.reset_index(inplace=True)

    momentum_portfolio_all = pd.DataFrame()
    contrarian_portfolio_all = pd.DataFrame()

    for i in range(window, len(by_month) - 1):
        start_month = by_month['交易日期'].iloc[i - window]  # 排名期第一个月
        end_month = by_month['交易日期'].iloc[i]  # 排名期最后一个月

        # 取出在排名期内的数据
        stock_temp = all_stock[(all_stock['交易日期'] > start_month) & (all_stock['交易日期'] <= end_month)]

        # 将指数在这段时间的数据取出作为交易日天数的标准
        index_temp = index_data[start_month:end_month]

        # 统计每只股票在排名期的交易日天数
        trading_days = stock_temp['股票代码'].value_counts()
        # 剔除在排名期内累计停牌超过（5*月数）天的股票，即如果排名期为3个月，就剔除累计停牌超过15天的股票
        keep_list = trading_days[trading_days >= (len(index_temp) - 5 * window)].index
        stock_temp = stock_temp[stock_temp['股票代码'].isin(keep_list)]

        # 计算每只股票在排名期的累计收益率
        grouped = stock_temp.groupby('股票代码')['涨跌幅'].agg(rtn=lambda x: (x + 1).prod() - 1)
        # 将累计收益率排序
        grouped.sort_values(by='rtn', inplace=True)
        # 取排序后前5%的股票构造反转策略的组合，后5%的股票构造动量策略的组合
        num = floor(len(grouped) * 0.05)
        momentum_code_list = grouped.index[-num:]  # 动量组合的股票代码列表
        contrarian_code_list = grouped.index[0:num]  # 反转组合的股票代码列表

        # ============================动量组合============================
        # 取出动量组合内股票当月的数据
        momentum = all_stock[(all_stock['股票代码'].isin(momentum_code_list)) &
                             (all_stock['交易日期'] > end_month) & (all_stock['交易日期'] <= by_month['交易日期'].iloc[i + 1])]

        # 剔除动量组合里在当月第一个交易日涨停的股票
        temp = momentum.groupby('股票代码')['涨停'].first()
        hold_list = temp[temp == 0].index
        momentum = momentum[momentum['股票代码'].isin(hold_list)].reset_index(drop=True)
        # 动量组合
        momentum_portfolio = momentum.pivot('交易日期', '股票代码', '涨跌幅').fillna(0)

        # 计算动量组合的收益率
        num = momentum_portfolio.shape[1]
        weights = num * [1. / num]
        momentum_portfolio['pf_rtn'] = np.dot(np.array(momentum_portfolio), np.array(weights))
        momentum_portfolio.reset_index(inplace=True)

        # 将每个月的动量组合收益数据合并
        momentum_portfolio_all = momentum_portfolio_all.append(momentum_portfolio[['交易日期', 'pf_rtn']],
                                                               ignore_index=True)
        # 计算动量策略的资金曲线
        momentum_portfolio_all['资金曲线'] = (1 + momentum_portfolio_all['pf_rtn']).cumprod()

        # ============================反转组合=============================
        # 取出反转组合内股票当月的数据
        contrarian = all_stock[(all_stock['股票代码'].isin(contrarian_code_list)) &
                               (all_stock['交易日期'] > end_month) & (all_stock['交易日期'] <= by_month['交易日期'].iloc[i + 1])]

        # 剔除反转组合里在当月第一个交易日涨停的股票
        temp = contrarian.groupby('股票代码')['涨停'].first()
        hold_list = temp[temp == 0].index
        contrarian = contrarian[contrarian['股票代码'].isin(hold_list)].reset_index(drop=True)
        # 反转组合
        contrarian_portfolio = contrarian.pivot('交易日期', '股票代码', '涨跌幅').fillna(0)

        # 计算反转组合的收益率
        num = contrarian_portfolio.shape[1]
        weights = num * [1. / num]
        contrarian_portfolio['pf_rtn'] = np.dot(np.array(contrarian_portfolio), np.array(weights))
        contrarian_portfolio.reset_index(inplace=True)

        # 将每个月的反转组合收益合并
        contrarian_portfolio_all = contrarian_portfolio_all.append(contrarian_portfolio[['交易日期', 'pf_rtn']],
                                                                   ignore_index=True)
        # 计算反转策略的资金曲线
        contrarian_portfolio_all['资金曲线'] = (1 + contrarian_portfolio_all['pf_rtn']).cumprod()

    return momentum_portfolio_all, contrarian_portfolio_all


# 读取股票数据
all_stock = get_stock_data()

# 从2011年1月开始形成排名期，排名期3个月，每月初根据前3个月的排名换仓
m, c = momentum_and_contrarian(all_stock, '2006-01-01', '2019-12-31', window=3)

date_line = list(m['交易日期'])
capital_line = list(m['资金曲线'])
return_line = list(m['pf_rtn'])
print('\n=====================动量策略主要回测指标=====================')
print("平均年化收益: %.2f" % annual_return(date_line, capital_line))
print("最大回撤: %.2f, 开始时间: %s, 结束时间: %s" % max_drawdown(date_line, capital_line))
print("夏普比例: %.2f" % sharpe_ratio(date_line, capital_line, return_line))

date_line = list(c['交易日期'])
capital_line = list(c['资金曲线'])
return_line = list(c['pf_rtn'])
print('\n=====================反转策略主要回测指标=====================')
print("平均年化收益: %.2f" % annual_return(date_line, capital_line))
print("最大回撤: %.2f, 开始时间: %s, 结束时间: %s" % max_drawdown(date_line, capital_line))
print("夏普比例: %.2f" % sharpe_ratio(date_line, capital_line, return_line))

# 同期大盘的相关指标
index_data = Functions.import_index_data('sh000001')
index_data.sort_values(by='交易日期', inplace=True)
index_data = index_data[index_data['交易日期'].isin(date_line)]
capital_line = list(index_data['收盘价'])
return_line = list(index_data['涨跌幅'])
print('\n=====================同期上证指数主要回测指标=====================')
print("平均年化收益: %.2f" % annual_return(date_line, capital_line))
print("最大回撤: %.2f, 开始时间: %s, 结束时间: %s" % max_drawdown(date_line, capital_line))
print("夏普比例: %.2f" % sharpe_ratio(date_line, capital_line, return_line))

plt.figure(figsize=(14, 7))
m.set_index('交易日期', inplace=True)
c.set_index('交易日期', inplace=True)
index_data['大盘收益'] = (index_data['涨跌幅'] + 1).cumprod() - 1
index_data.set_index('交易日期', inplace=True)

(m['资金曲线'] - 1).plot()
(c['资金曲线'] - 1).plot()
index_data['大盘收益'].plot()
plt.title('累计收益')
plt.legend(['动量策略', '反转策略', '大盘收益'], loc='best')
plt.grid()
plt.savefig(config.output_data_path + "动量反转策略验证.png")
plt.show()
