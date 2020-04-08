# coding: utf-8
import os
from datetime import timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import mplfinance as mpf
import numpy as np

from tool.indicator import period_return

plt.rcParams['font.family'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_year_return(back_df, title='', save_path='', show=False):
    rtn_series = period_return(back_df, period='A')
    # plt.figure(figsize=(9, 6))
    # plt.bar(rtn_series.index.year, rtn_series.values, width=0.3, label='', color="#D2B48C")
    #
    # if title is None or title == '':
    #     title = '周期收益率'
    # plt.title(title)
    #
    # min_rtn = rtn_series.min()
    # max_rtn = rtn_series.max()
    #
    # num = 10
    # step = (max_rtn - min_rtn) / num
    #
    # start = min_rtn - step
    # end = max_rtn + step
    #
    # if step > 0:
    #     plt.yticks(np.arange(start, end, step))
    #
    # plt.grid(True, ls='--')
    #
    # plt.savefig(os.path.join(save_path, title))
    #
    # if show:
    #     plt.show()

    if title is None or title == '':
        title = '周期收益率'
    plot_bar_xy(rtn_series.index.year, rtn_series.values, title=title, save_path=save_path, show=show)


def plot_bar_xy(x, y, title='', save_path='', show=False):
    plt.figure(figsize=(9, 6))
    plt.bar(x, y, width=0.3, label='', color="#D2B48C")

    if title is None or title == '':
        title = '无标题'
    plt.title(title)

    min_rtn = np.min(y)
    max_rtn = np.max(y)

    num = 10
    step = (max_rtn - min_rtn) / num

    start = min_rtn - step
    end = max_rtn + step

    if step > 0:
        plt.yticks(np.arange(start, end, step))

    plt.grid(True, ls='--')

    plt.savefig(os.path.join(save_path, title))

    if show:
        plt.show()


# 绘制回测曲线
def plot_back_line(back_df, title='', save_path='', show=False):
    """
    :param back_df: 包含3列数据, 交易日期/策略收益/基准收益
    :param title:
    :param save_path:
    :param show:
    :return:
    """
    years = max(len(set(back_df.index.year)), 9)

    plt.figure(figsize=(years, 6))

    if title is None or title == '':
        title = '回测曲线'

    plt.plot(back_df.index, back_df['策略累计收益率'], label='策略收益')
    plt.plot(back_df.index, back_df['基准累计收益率'], label='基准收益')
    plt.title(title)
    plt.xlabel(u"交易日期")
    plt.ylabel(u"收益率")

    start_date = back_df.index[0] + timedelta(days=-100)
    end_date = back_df.index[len(back_df.index) - 1] + timedelta(days=100)
    plt.xticks(pd.date_range(start=start_date, end=end_date, freq="3M"),
               rotation=60)

    min_value = min(back_df['策略累计收益率'].min(), back_df['基准累计收益率'].min())
    max_value = max(back_df['策略累计收益率'].max(), back_df['基准累计收益率'].max())

    num = 10
    step = (max_value - min_value) / num

    start = min_value - step
    end = max_value + step

    if step > 0:
        plt.yticks(np.arange(start, end, step))

    plt.grid(True, ls='--')
    # 将legend放到左上角
    plt.legend(loc='upper left')

    plt.savefig(os.path.join(save_path, title))

    if show:
        plt.show()


def plot_kline(stock_data, volume=False, mav=(5, 10)):
    rename_map = {
        "交易日期": "Date",
        "开盘价": "Open",
        "收盘价": "Close",
        "最高价": "High",
        "最低价": "Low",
        "成交量": "Volume",
    }

    stock_data = stock_data.rename(columns=rename_map)
    stock_data = stock_data[list(rename_map.values())]
    stock_data.set_index('Date', inplace=True)

    print(stock_data)

    """
    up: 设置上涨K线的颜色
    down: 设置下跌K线的颜色
    edge=inherit: K线图边缘和主题颜色保持一致
    volume=in: 成交量bar的颜色继承K线颜色
    wick=in: 上下引线颜色继承K线颜色
    """
    mc = mpf.make_marketcolors(up='r', down='g', volume='in', edge='inherit', wick='in')
    s = mpf.make_mpf_style(marketcolors=mc)
    mpf.plot(stock_data, type='candle', style=s, volume=volume, mav=mav, figratio=(9, 6), figscale=2)
