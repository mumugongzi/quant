# coding: utf-8

from common.Functions import *
from tool.plot import plot_back_line

# index_code = "sh000300"
# start = "20120901"
# long = 90
# short = 80
# column = "收盘价"


index_code = "sh000016"
start = "20120901"
long = 70
short = 40
column = "收盘价"

name_map = {
    'sh000001': "上证指数",
    'sh000016': "上证50",
    'sh000300': "沪深300",
    'sh000905': "中证500",
}

index_df = import_index_data(index_code=index_code)
index_df.set_index("交易日期", inplace=True)
index_df.sort_index()

index_df = index_df[index_df.index > start]

index_df[column + "快线"] = index_df[column].rolling(window=short).mean()
index_df[column + "慢线"] = index_df[column].rolling(window=long).mean()

index_df.loc[index_df[column + "快线"] > index_df[column + "慢线"], "position"] = 1

index_df["position"] = index_df["position"].fillna(0)
index_df["择时涨跌幅"] = index_df["涨跌幅"] * index_df["position"].shift(1)

index_df["策略累计收益率"] = (index_df['择时涨跌幅'] + 1).cumprod()
index_df["策略涨跌幅"] = index_df['择时涨跌幅']
index_df["基准累计收益率"] = (index_df['涨跌幅'] + 1).cumprod()
index_df["基准涨跌幅"] = index_df['涨跌幅']

plot_back_line(index_df, save_path=config.output_data_path + "双均线择时/".format(name_map[index_code]),
               title=name_map[index_code], show=True)
