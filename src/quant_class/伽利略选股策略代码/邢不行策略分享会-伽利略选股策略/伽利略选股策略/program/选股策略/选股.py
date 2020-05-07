"""
邢不行策略分享会
微信：xbx9025
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from program.选股策略.Functions import *
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

# ===参数设定
select_stock_num = 3  # 选股数量
c_rate = 1.5 / 10000  # 手续费
t_rate = 1 / 1000  # 印花税

# ===导入数据
# 从hdf文件中读取整理好的所有股票数据
df = pd.read_hdf('/Users/xingbuxingx/Desktop/策略分享会直播/191108- 伽利略选股策略_资金流选股策略/伽利略选股策略/data/选股策略/all_stock_data_W.h5', 'df')
df.dropna(subset=['下周期每天涨跌幅'], inplace=True)

# ===选股
# 删除下个交易日不交易、开盘涨停的股票，因为这些股票在下个交易日开盘时不能买入。
df = df[df['下日_是否交易'] == 1]
df = df[df['下日_开盘涨停'] == False]
df = df[df['下日_是否ST'] == False]
df = df[df['下日_是否退市'] == False]

# ****************************以下内容可以改动****************************
# ===常见因子
# df['因子'] = df['量价相关系数_1_10']  # 量价相关策略
# df['因子'] = df['总市值']  # 小市值策略
# df['因子'] = df['收盘价']  # 低价股策略。用最低价代替，不会更好？
# df['因子'] = df['成交额'] / df['流通市值']  # 换手率
# 还有很多其他的策略在开发中，展示隐藏策略页面

# ===技术指标因子
# bias指标
# df['因子'] = df['bias_20']  # 反转因子
# # kdj
# df['因子'] = df['K']  # 根据某个指标的值来，单调性很差。不一定这么用，之后会讲其他改进方法。

# ===财务数据因子：展示正在为大家准备的财务数据


# ===先筛选一部分股票
# df = df[df['上市至今交易天数'] > 250]
# df = df[df['bias_20'] < 0.05]

# ===策略组合
# 组合方式1：相乘。当几个因子都有效，可以将其相乘，然后组合起来
# df['因子'] = df['总市值'] * df['收盘价'] * df['成交额']
# 不是相乘就会变得更好
# df['因子'] = df['总市值'] * df['收盘价']
# 有的不能直接相乘，比如'量价相关系数_1_10'有负数
# df['因子'] = df['总市值'] * df['收盘价'] * df['成交额'] * df['量价相关系数_1_10']

# 组合方式2：排名相加
df['总市值_排名'] = df.groupby('交易日期')['总市值'].rank()
df['收盘价_排名'] = df.groupby('交易日期')['收盘价'].rank()
df['成交额_排名'] = df.groupby('交易日期')['成交额'].rank()
df['量价相关系数_1_10_排名'] = df.groupby('交易日期')['量价相关系数_1_10'].rank()
df['bias_20'] = df.groupby('交易日期')['bias_20'].rank()
df['因子'] = df['总市值_排名'] + df['收盘价_排名'] + df['成交额_排名'] + df['量价相关系数_1_10_排名'] + df['bias_20']

# 组合方式3：排名相加，代表各个因子对最终结果的权重是一样的，那么我希望不一样怎么办？
# 因子之间有相关性怎么办？
# 多因子模型

# 组合方式4：有这么多的因子，自己人工组合好累，能不能让程序自动帮我组合？
# 机器学习

# 根据选股因子对股票进行排名
# 计算排名绝对值
df['排名'] = df.groupby('交易日期')['因子'].rank()
# 计算排名百分比
# df['排名_百分比'] = df.groupby('交易日期')['因子'].rank(pct=True)

# 选取排名靠前的股票
df = df[df['排名'] <= select_stock_num]
# df = df[df['排名_百分比'] < 0.1]

# ****************************以上内容可以改动****************************

# 按照开盘买入的方式，修正选中股票在下周期每天的涨跌幅。
# 即将下周期每天的涨跌幅中第一天的涨跌幅，改成由开盘买入的涨跌幅
df['下日_开盘买入涨跌幅'] = df['下日_开盘买入涨跌幅'].apply(lambda x: [x])
df['下周期每天涨跌幅'] = df['下周期每天涨跌幅'].apply(lambda x: x[1:])
df['下周期每天涨跌幅'] = df['下日_开盘买入涨跌幅'] + df['下周期每天涨跌幅']
print(df[['交易日期', '股票名称', '下日_开盘买入涨跌幅', '下周期每天涨跌幅']].tail(6))

# ===整理选中股票数据
# 挑选出选中股票
df['股票代码'] += ' '
df['股票名称'] += ' '
group = df.groupby('交易日期')
select_stock = pd.DataFrame()
select_stock['买入股票代码'] = group['股票代码'].sum()
select_stock['买入股票名称'] = group['股票名称'].sum()

# 计算下周期每天的资金曲线
select_stock['选股下周期每天资金曲线'] = group['下周期每天涨跌幅'].apply(lambda x: np.cumprod(np.array(list(x))+1, axis=1).mean(axis=0))

# 扣除买入手续费
select_stock['选股下周期每天资金曲线'] = select_stock['选股下周期每天资金曲线'] * (1 - c_rate)  # 计算有不精准的地方
# 扣除卖出手续费、印花税。最后一天的资金曲线值，扣除印花税、手续费
select_stock['选股下周期每天资金曲线'] = select_stock['选股下周期每天资金曲线'].apply(lambda x: list(x[:-1]) + [x[-1] * (1 - c_rate - t_rate)])

# 计算下周期整体涨跌幅
select_stock['选股下周期涨跌幅'] = select_stock['选股下周期每天资金曲线'].apply(lambda x: x[-1] - 1)
# 计算下周期每天的涨跌幅
select_stock['选股下周期每天涨跌幅'] = select_stock['选股下周期每天资金曲线'].apply(lambda x: list(pd.DataFrame([1] + x).pct_change()[0].iloc[1:]))
del select_stock['选股下周期每天资金曲线']

# 计算整体资金曲线
select_stock.reset_index(inplace=True)
select_stock['资金曲线'] = (select_stock['选股下周期涨跌幅'] + 1).cumprod()
print(select_stock)

# ===计算选中股票每天的资金曲线
# 计算每日资金曲线
index_data = import_index_data('/Users/xingbuxingx/Desktop/策略分享会直播/191011- 若干选股策略说明及如何简单组合策略/如何简单组合策略/data/选股策略/sh000001.csv')
equity = pd.merge(left=index_data, right=select_stock[['交易日期', '买入股票代码']], on=['交易日期'],
                  how='left', sort=True)  # 将选股结果和大盘指数合并

equity['持有股票代码'] = equity['买入股票代码'].shift()
equity['持有股票代码'].fillna(method='ffill', inplace=True)
equity.dropna(subset=['持有股票代码'], inplace=True)
del equity['买入股票代码']

equity['涨跌幅'] = select_stock['选股下周期每天涨跌幅'].sum()
equity['equity_curve'] = (equity['涨跌幅'] + 1).cumprod()
equity['benchmark'] = (equity['指数涨跌幅'] + 1).cumprod()


# ===画图
equity.set_index('交易日期', inplace=True)
plt.plot(equity['equity_curve'])
plt.plot(equity['benchmark'])
plt.legend(loc='best')
plt.show()
