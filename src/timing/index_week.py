# coding: utf-8

"""
验证指数是否隔周开盘下跌的概率比较大
"""
from common import config
from common.Functions import import_index_data
import datetime

from tool.plot import plot_back_line
import pandas as pd

index_code = "sz399006"
start = "20120901"

sample_period = 'w'
name_map = {
    'sh000001': "上证指数",
    'sh000016': "上证50",
    'sh000300': "沪深300",
    'sh000905': "中证500",
    'sz399001': "深圳成指",
    'sz399006': "创业板指",
}

index_df = import_index_data(index_code=index_code)
index_df = index_df[index_df['交易日期'] > '20060101']

index_df.reset_index(inplace=True, drop=True)

print(index_df)

trade_date_list = index_df['交易日期']

# print(type(trade_date_list[0]))

open_day_list = []
for i in range(1, len(trade_date_list)):
    before_day = trade_date_list[i] + datetime.timedelta(days=-1)
    if before_day != trade_date_list[i - 1]:
        open_day_list.append(trade_date_list[i])

index_df.set_index("交易日期", inplace=True)
index_df["昨日收盘价"] = index_df["收盘价"].shift()
index_df['开盘涨跌幅'] = index_df['涨跌幅']

index_df.loc[index_df.index.isin(open_day_list), "开盘涨跌幅"] = index_df['收盘价'] / index_df['开盘价'] - 1

# print(index_df[['开盘价', '收盘价', '涨跌幅', '开盘涨跌幅']])
#
# print(index_df[index_df['开盘价'] < index_df['昨日收盘价']])


res = pd.DataFrame(
        {
            "策略累计收益率": (index_df['开盘涨跌幅'] + 1).cumprod(),
            "策略涨跌幅": index_df['开盘涨跌幅'],
            "基准累计收益率": (index_df['涨跌幅'] + 1).cumprod(),
            "基准涨跌幅": index_df['涨跌幅'],
        }
    )

print(res)

plot_back_line(res, save_path=config.output_data_path, title="验证{}周五卖周一买.png".format(name_map[index_code]), show=True)



# print(index_df.resample(sample_period).apply(lambda x: print(x)))
