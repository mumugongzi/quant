# -*- coding: utf-8 -*-

"""
代码原作者@邢不行实现的简易版的海龟交易法则, 但其实只是一个简单的突破系统验证
"""

"""
作者：邢不行

本系列帖子“量化小讲堂”，通过实际案例教初学者使用python、pandas进行金融数据处理，希望能对大家有帮助。

必读文章《10年400倍策略分享-附视频逐行讲解代码》：http://bbs.pinggu.org/thread-5558776-1-1.html

所有系列文章汇总请见：http://bbs.pinggu.org/thread-3950124-1-1.html

想要快速、系统的学习量化知识，可以参与我与论坛合作开设的《python量化投资入门》视频课程：http://www.peixun.net/view/1028.html，我会亲自授课，随问随答。
参与课程还可以免费加入我的小密圈，我每天会在圈中分享量化的所见所思，圈子介绍：http://t.xiaomiquan.com/BEiqzVB

微信：xbx_laoshi，量化交流Q群(快满)：438143420，有问题欢迎交流。

文中用到的A股数据可在www.yucezhe.com下载，这里可以下载到所有股票、从上市日起的交易数据、财务数据、分钟数据、分笔数据、逐笔数据等。
"""
import pandas as pd
from common.Functions import import_index_data
from common import config
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = ['SimHei']

# ==========导入上证指数的原始数据
# 注意：这里请填写数据文件在您电脑中的路径，并注意路径中斜杠的方向

columns=['交易日期', '指数代码', '最高价', '最低价', '开盘价', '收盘价', '涨跌幅']
# index_data = import_index_data('sh000001', columns=columns)
index_data = import_index_data('sz399001', columns=columns)
# 对数据按照【date】交易日期从小到大排序
index_data.sort_values('交易日期', inplace=True)
index_data = index_data[index_data['交易日期'] > '20060101']

# ==========计算海龟交易法则的买卖点
# 设定海龟交易法则的两个参数，当收盘价大于最近N1天的最高价时买入，当收盘价低于最近N2天的最低价时卖出
# 这两个参数可以自行调整大小，但是一般N1 > N2
N1 = 20
N2 = 10

# 通过rolling_max方法计算最近N1个交易日的最高价
index_data['最近N1个交易日的最高点'] = index_data['最高价'].rolling(N1, min_periods=1).max()
# 对于上市不足N1天的数据，取上市至今的最高价
# index_data['最近N1个交易日的最高点'].fillna(value=index_data['最高价'].cummax(), inplace=True)

# 通过相似的方法计算最近N2个交易日的最低价
index_data['最近N2个交易日的最低点'] = index_data['最低价'].rolling(N1, min_periods=1).min()
# index_data['最近N2个交易日的最低点'].fillna(value=index_data['最低价'].cummin(), inplace=True)

# 当当天的【close】> 昨天的【最近N1个交易日的最高点】时，将【收盘发出的信号】设定为1
buy_index = index_data[index_data['收盘价'] > index_data['最近N1个交易日的最高点'].shift(1)].index
index_data.loc[buy_index, '收盘发出的信号'] = 1
# 当当天的【close】< 昨天的【最近N2个交易日的最低点】时，将【收盘发出的信号】设定为0
sell_index = index_data[index_data['收盘价'] < index_data['最近N2个交易日的最低点'].shift(1)].index
index_data.loc[sell_index, '收盘发出的信号'] = 0

# 计算每天的仓位，当天持有上证指数时，仓位为1，当天不持有上证指数时，仓位为0
index_data['当天的仓位'] = index_data['收盘发出的信号'].shift(1)
index_data['当天的仓位'].fillna(method='ffill', inplace=True)

# 取1992年之后的数据，排出较早的数据
index_data = index_data[index_data['交易日期'] >= pd.to_datetime('19930101')]

# 当仓位为1时，买入上证指数，当仓位为0时，空仓。计算从19920101至今的资金指数
index_data['资金指数'] = (index_data['涨跌幅'] * index_data['当天的仓位'] + 1.0).cumprod()
initial_idx = index_data.iloc[0]['收盘价'] / (1 + index_data.iloc[0]['涨跌幅'])
index_data['资金指数'] *= initial_idx

# 输出数据到指定文件
index_data[['交易日期', '最高价', '最低价', '收盘价', '涨跌幅', '最近N1个交易日的最高点',
            '最近N2个交易日的最低点', '当天的仓位', '资金指数']].to_csv(config.output_data_path + '高低价突破.csv', index=False, encoding='utf8')

# ==========计算每年指数的收益以及海龟交易法则的收益
index_data['高低突破每日涨跌幅'] = index_data['涨跌幅'] * index_data['当天的仓位']
year_rtn = index_data.set_index('交易日期')[['涨跌幅', '高低突破每日涨跌幅']]. \
               resample('A').apply(lambda x: (x + 1.0).prod() - 1.0) * 100

plt.figure(figsize=(16, 8))
plt.plot(index_data['交易日期'], index_data['收盘价'] / initial_idx, label='原始指数')
plt.plot(index_data['交易日期'], index_data['资金指数'] / initial_idx, label='高低突破系统')
plt.plot(index_data['交易日期'], (index_data['资金指数'] - index_data['收盘价'])/initial_idx, label='净差')
plt.title(u"高低价突破系统验证")
plt.xlabel(u"交易日期")
plt.ylabel(u"指数值")
# plt.yticks(np.arange(0, max_pe, 10))
# plt.xticks(pd.date_range(start=date_list[0], end=date_list[len(date_list) - 1], freq="6M"), rotation=60)
plt.grid(True, ls='--')
plt.legend()

# savefig函数必须在show函数之前调用, 否则保存的图片是空白的
plt.savefig(config.output_data_path + "高低价突破验证.png")
plt.show()
print(year_rtn)
