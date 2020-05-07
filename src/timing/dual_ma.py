# coding: utf-8

"""
双均线择时验证
"""
import math

from common.Functions import *
import datetime
from common.config import *

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)

name_map = {
    'sh000001': "上证指数",
    'sh000016': "上证50",
    'sh000300': "沪深300",
    'sh000905': "中证500",
}

start_end_list = [
    {
        "start": "20050101",
        "end": "20090101",
    },
    {
        "start": "20090101",
        "end": "20130101",
    },
    {
        "start": "20130101",
        "end": "20170101",
    },
]

for index_code in name_map.keys():

    index_df = import_index_data(index_code=index_code)
    index_df.set_index("交易日期", inplace=True)
    index_df.sort_index()

    res = pd.DataFrame()

    for long in range(20, 260, 10):
        for short in range(10, long, 10):
            for method in ["开盘价", "收盘价", "最高价", "最低价", "成交量", "收盘价-成交量"]:

                print("慢线: {}, 快线: {}, 择时因素: {}".format(long, short, method))

                row = {
                    "快线": short,
                    "慢线": long,
                    "择时变量": method,
                }
                for start_end in start_end_list:
                    start = start_end['start']
                    end = start_end['end']

                    df = index_df.copy()

                    columns = ["开盘价", "收盘价", "最高价", "最低价", "成交量"]

                    for column in columns:
                        df[column + "快线"] = df[column].rolling(window=short).mean()
                        df[column + "慢线"] = df[column].rolling(window=long).mean()

                    df = df[(df.index >= start) & (df.index < end)]

                    if method in ["开盘价", "收盘价", "最高价", "最低价"]:
                        df.loc[df[method + "快线"] > df[method + "慢线"], "position"] = 1
                    else:
                        df["position"] = 0
                        for column in ["收盘价", "成交量"]:
                            df.loc[df[column + "快线"] > df[column + "慢线"], "position"] += 1.0 / 2

                    df["position"] = df["position"].fillna(0)
                    df["择时涨跌幅"] = df["涨跌幅"] * df["position"].shift(1)

                    rtn = (df["择时涨跌幅"] + 1).prod()
                    row[start + "_" + end + "收益"] = rtn
                    row[start + "_" + end + "收益sigmod"] = 1 / (1 + math.exp(1 - rtn))
                res = res.append(row, ignore_index=True)

    sigmod_name_list = []
    for start_end in start_end_list:
        start = start_end['start']
        end = start_end['end']
        sigmod_name_list.append(start + "_" + end + "收益sigmod")

    res["sigmod乘积"] = res[sigmod_name_list].prod(axis=1)
    res.drop(sigmod_name_list, axis=1, inplace=True)

    res.sort_values(by="sigmod乘积", ascending=False, inplace=True)
    res.reset_index(inplace=True, drop=True)

    # print(res)
    res.to_csv(output_data_path + "/双均线择时/{}.csv".format(name_map[index_code]), mode="w", index=False)
