# coding: utf-8

import tushare as ts

pro = ts.pro_api('')

df = pro.stock_basic()

print(df)
