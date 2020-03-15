# -*- coding: utf-8 -*-
"""
邢不行量化小讲堂系列文章配套代码
文章标题：Python说：这个炒股指标是我见过最废的，没有之一
文章链接：https://mp.weixin.qq.com/s/3oXyBrWdAK2__u5-08qNag
作者：邢不行
微信：xingbx007
"""
from common import Functions
from common import config
import pandas as pd

import matplotlib.pyplot as plt

# from kdj import Functions

plt.rcParams['font.family'] = ['SimHei']

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行

# 得到所有股票的列表
code_list = Functions.get_stock_code_list_in_one_dir(config.stock_data_path)
# code_list = code_list[:10]

# 遍历所有股票
output = pd.DataFrame()
for code in code_list:
    # 导入数据
    data = Functions.import_stock_data(code)

    # 计算后复权价
    data[['开盘价', '最高价', '最低价', '收盘价']] = Functions.cal_fuquan_price(data)

    data = data.sort_values(by=['交易日期'], ascending=True)
    data.reset_index(inplace=True, drop=True)

    # 计算N天后涨跌幅
    for i in [1, 3, 5, 10]:
        data[str(i) + '天后涨跌幅'] = data['收盘价'].shift(-i) / data['收盘价'] - 1
    data = data[data['交易日期'] < pd.to_datetime('20170401')]
    if data.empty:
        continue

    # 计算KDJ指标
    low_list = data['最低价'].rolling(9, min_periods=1).min()
    high_list = data['最高价'].rolling(9, min_periods=1).max()
    rsv = (data['收盘价'] - low_list) / (high_list - low_list) * 100
    data['K'] = rsv.ewm(com=2).mean()
    data['D'] = data['K'].ewm(com=2).mean()
    data['J'] = 3 * data['K'] - 2 * data['D']

    # 计算KDJ指标金叉、死叉情况
    data['金叉死叉'] = None
    kdj_position = data['K'] > data['D']
    data.loc[kdj_position[(kdj_position == True) & (kdj_position.shift() == False)].index, '金叉死叉'] = '金叉'
    kdj_position = data['K'] < data['D']
    data.loc[kdj_position[(kdj_position == True) & (kdj_position.shift() == False)].index, '金叉死叉'] = '死叉'

    # 去除N天后涨跌幅为空的情况
    for i in [1, 3, 5, 10]:
        data = data[data[str(i) + '天后涨跌幅'].notnull()]

    # 合并数据
    output = output.append(data[data['金叉死叉'].notnull()], ignore_index=True)

# output.to_csv(config.output_data_path + '/kdj.csv', index=False)

condition1 = (output['D'] >= 80) & (output['金叉死叉'] == '死叉')
condition2 = (output['D'] <= 20) & (output['金叉死叉'] == '金叉')
output = output[condition1 | condition2]

gold_x = {}
dead_x = {}
for t, group in output.groupby('金叉死叉'):
    print(t)
    print(group[[str(i) + '天后涨跌幅' for i in (1, 3, 5, 10)]].describe())

    for i in (1, 3, 5, 10):
        if t == '金叉':
            gold_x[str(i) + '天后'] = float(group[group[str(i) + '天后涨跌幅'] > 0].shape[0]) / group.shape[0]
        elif t == '死叉':
            dead_x[str(i) + '天后'] = float(group[group[str(i) + '天后涨跌幅'] < 0].shape[0]) / group.shape[0]

plt.subplots(2, 1, figsize=(6, 8))
plt.subplot(2, 1, 1)
gold_bar = plt.bar(gold_x.keys(), gold_x.values(), width=0.3, label='金叉股票上涨比例', color="#D2B48C")
plt.title('低位金叉(D<=20)后股票上涨比例')
for b in gold_bar:
    plt.text(b.get_x() + b.get_width() / 2, b.get_height(), "%.2f%%" % b.get_height(), ha='center', va='bottom')

plt.subplot(2, 1, 2)
dead_bar = plt.bar(dead_x.keys(), dead_x.values(), width=0.3, label='死叉股票下跌比例', color="#D2B48C")
plt.title('高位死叉(D>=80)后股票下跌比例')

for b in dead_bar:
    plt.text(b.get_x() + b.get_width() / 2, b.get_height(), "%.2f%%" % b.get_height(), ha='center', va='bottom')
plt.show()
