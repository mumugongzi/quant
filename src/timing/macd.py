# coding: utf-8

from common.Functions import *
import talib

from tool.plot import plot_back_line, plot_bar_xy
from tool.progress import print_progress
import numpy as np
import matplotlib.pyplot as plt

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


def macd_back_test(stock_code, start_date, end_date, stock_type='股票'):
    columns = ['交易日期', '收盘价', '涨跌幅']
    if stock_type == '指数':
        # columns.append('指数代码')
        stock_data = import_index_data(stock_code, columns=columns)
        # stock_data = stock_data.rename(columns={"指数代码": "股票代码"})
    else:
        # columns.append('股票代码')
        stock_data = import_stock_data(stock_code, columns=columns)

    stock_data = stock_data[(stock_data['交易日期'] >= start_date) & (stock_data['交易日期'] <= end_date)]

    stock_data.dropna(subset=['收盘价'], inplace=True)
    if len(stock_data) < 50:
        return pd.DataFrame()

    price = stock_data['收盘价'].values
    if stock_type == '股票':
        price = cal_right_price(stock_data, price_columns=['收盘价'])['收盘价'].values

    # fast_period = 5
    # slow_period = 15
    # signal_period = 7

    fast_period = 12
    slow_period = 26
    signal_period = 9
    stock_data['macd'] = talib.MACD(price, fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)[
        -1]

    stock_data['macd'] = stock_data['macd'].shift(1)

    fast_sum = str(fast_period) + 'sum'
    slow_sum = str(slow_period) + 'sum'
    stock_data[fast_sum] = stock_data['macd'].rolling(fast_period, min_periods=fast_period).sum()
    stock_data[slow_sum] = stock_data['macd'].rolling(slow_period, min_periods=slow_period).sum()

    stock_data.reset_index(inplace=True, drop=True)

    # row = stock_data[stock_data['交易日期'] == '2008-08-21']
    #
    # macd_v = row['macd'].values[0]
    # fast_v = row[fast_sum].values[0]
    # slow_v = row[slow_sum].values[0]
    # print("MACD: {}, fast: {}, slow: {}".format(macd_v, fast_v, slow_v))
    #
    # print(((macd_v > 0) & ((slow_v - fast_v) > 0)))


    # 买入信号
    stock_data.loc[(stock_data['macd'] > 0) & ((stock_data[slow_sum] - stock_data[fast_sum]) > 0), '信号'] = 1

    stock_data.loc[(stock_data['macd'] <= 0) & (stock_data[fast_sum] > 0) & (
                (stock_data[slow_sum] - stock_data[fast_sum]) > 0), '信号'] = -1

    stock_data['信号'].fillna(method='ffill', inplace=True)

    stock_data.loc[stock_data['信号'] == -1, 'MACD涨跌幅'] = 0.0
    stock_data.loc[stock_data['信号'].isna(), 'MACD涨跌幅'] = 0.0

    # 实际情况无法真正满仓, 考虑仓位磨损
    stock_data.loc[stock_data['信号'] == 1, 'MACD涨跌幅'] = stock_data['涨跌幅'] * 0.99

    # print(stock_data)

    stock_data.set_index('交易日期', inplace=True)

    res = pd.DataFrame(
        {
            "策略累计收益率": (stock_data['MACD涨跌幅'] + 1).cumprod(),
            "策略涨跌幅": stock_data['MACD涨跌幅'],
            "基准累计收益率": (stock_data['涨跌幅'] + 1).cumprod(),
            "基准涨跌幅": stock_data['涨跌幅'],
        }
    )

    return res


# 指数择时
def index_timing():
    res = macd_back_test('sh000001', '2008-01-01', '2020-03-01', stock_type='指数')

    plot_back_line(res, save_path=config.output_data_path, title="上证指数MACD择时", show=True)

    res = macd_back_test('sz399001', '2008-01-01', '2020-03-01', stock_type='指数')

    plot_back_line(res, save_path=config.output_data_path, title="深圳成指MACD择时", show=True)

    res = macd_back_test('sz399006', '2010-04-01', '2020-03-01', stock_type='指数')

    plot_back_line(res, save_path=config.output_data_path, title="创业板指MACD择时", show=True)


def stock_rnt_distribute():
    stock_code_list = get_stock_code_list()

    start_date = '2008-01-01'
    end_date = '2020-03-01'
    res_df = pd.DataFrame()
    for stock_code in stock_code_list:
        print_progress(len(stock_code_list), step=0.01)

        rtn_df = macd_back_test(stock_code, start_date, end_date)
        if len(rtn_df) <= 0:
            continue

        res_df = res_df.append({
            "股票代码": stock_code,
            "基准收益": rtn_df.iloc[-1]['基准累计收益率'],
            "策略收益": rtn_df.iloc[-1]['策略累计收益率'],
            "超额收益": rtn_df.iloc[-1]['策略累计收益率'] - rtn_df.iloc[-1]['基准累计收益率']
        }, ignore_index=True)

        # print(rtn_df[-40:])
        #
        # print("绝对收益: {}, 相对收益: {}".format(abs_rtn, relative_rtn))

    x_ticks = []
    abs_quantile_list = []
    relative_quantile_list = []

    # print(res_df)
    for q in np.linspace(0.1, 0.9, 9):
        # print("计算{}分位值".format(q * 100))

        # x_ticks.append("{}分位".format())
        abs_q = res_df['策略收益'].quantile(q)
        abs_quantile_list.append(abs_q)

        relative_q = res_df['超额收益'].quantile(q)
        relative_quantile_list.append(relative_q)

        print("{}分位, 策略收益: {}, 超额收益: {}".format(int(q * 100), abs_q, relative_q))

    # print(abs_quantile_list)
    # print(relative_quantile_list)

    res_df.to_csv(config.output_data_path + "MACD策略收益" + start_date + "_" + end_date + ".csv", index=None)

    """
    验证结果:
    MACD(5, 15, 7):
        信号条件:
        10分位, 策略收益: 0.5044983475666386, 超额收益: -3.076422849948771
        20分位, 策略收益: 0.6810689403368495, 超额收益: -1.6119578622219897
        30分位, 策略收益: 0.840881638854911, 超额收益: -1.0166233833845584
        40分位, 策略收益: 0.9890013855659865, 超额收益: -0.5919694901942444
        50分位, 策略收益: 1.1562110634817966, 超额收益: -0.2708740968410566
        60分位, 策略收益: 1.3885123307084326, 超额收益: 0.057528536063105984
        70分位, 策略收益: 1.7167415204486431, 超额收益: 0.3990461385844936
        80分位, 策略收益: 2.282351220925749, 超额收益: 0.8479537582623341
        90分位, 策略收益: 3.445404595227647, 超额收益: 1.8432082156423606
        
        
        
    MACD(12, 26, 9):
        信号条件:
        stock_data.loc[(stock_data['macd'] > 0) & (stock_data[slow_sum] - stock_data[fast_sum]) > 0, '信号'] = "买入"
        stock_data.loc[(stock_data[fast_sum] > 0) & ((stock_data[slow_sum] - stock_data[fast_sum]) > 0), '信号'] = "卖出"
    
    
        10分位, 策略收益: 0.8456867203056416, 超额收益: -2.3560355368573256
        20分位, 策略收益: 1.0461430744319473, 超额收益: -1.0656442735305267
        30分位, 策略收益: 1.3277063053714615, 超额收益: -0.4283054673475579
        40分位, 策略收益: 1.695867494924019, 超额收益: 0.08469958981163286
        50分位, 策略收益: 2.294324264305844, 超额收益: 0.701006466993134
        60分位, 策略收益: 3.1835083618851714, 超额收益: 1.602405322073158
        70分位, 策略收益: 4.509278009474464, 超额收益: 2.8297707061919137
        80分位, 策略收益: 6.299098451588755, 超额收益: 4.715451145450981
        90分位, 策略收益: 10.2658700496928, 超额收益: 8.456840001948365
        
        信号条件:
        stock_data.loc[(stock_data['macd'] > 0) & (stock_data[slow_sum] - stock_data[fast_sum]) > 0, '信号'] = "买入"
        stock_data.loc[(stock_data['macd'] <= 0) & (stock_data[fast_sum] > 0) & ((stock_data[slow_sum] - stock_data[fast_sum]) > 0), '信号'] = "卖出"
        
        10分位, 策略收益: 1.1542464316484806, 超额收益: -1.1347547211025442
        20分位, 策略收益: 1.7379660427723178, 超额收益: -0.21604236842887609
        30分位, 策略收益: 3.129882524863988, 超额收益: 0.8046528187270677
        40分位, 策略收益: 6.673347057334242, 超额收益: 5.019418839388572
        50分位, 策略收益: 11.209840763014755, 超额收益: 9.550298973526788
        60分位, 策略收益: 16.76034046535455, 超额收益: 15.023706119677636
        70分位, 策略收益: 25.629589119037867, 超额收益: 23.994179184661593
        80分位, 策略收益: 39.45000365405899, 超额收益: 37.17093533620145
        90分位, 策略收益: 69.49645087577125, 超额收益: 67.30230542059215
    """


# print(np.linspace(0.1, 0.9, 9))
stock_rnt_distribute()

# res = macd_back_test('sz002156', '2008-01-01', '2020-03-01')

# plot_back_line(res, save_path=config.output_data_path, title="平安银行MACD择时", show=True)

# index_timing()