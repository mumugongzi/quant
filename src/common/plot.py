# coding: utf-8

# 导入需要的库
import mplfinance as mpf
from common import Functions

stock_data = Functions.import_stock_data('sh600000')

rename_map = {
    "交易日期": "Date",
    "开盘价": "Open",
    "收盘价": "Close",
    "最高价": "High",
    "最低价": "Low",
    "成交量": "Volume",
}

def plot_kline(stock_data, volume=False, mav=(5, 10)):
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
