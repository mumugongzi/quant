# coding: utf-8
from common.Functions import import_stock_data
import pandas as pd

# df = import_stock_data('sh600001', columns=['交易日期', '涨跌幅'])
# df.set_index('交易日期', inplace=True)
#
# print(df)
#
# df.reset_index(inplace=True)
#
# print(df)
#
# temp_df = df.copy()
# temp_df.set_index('交易日期', inplace=True)
# temp_df['标记'] = 1
# print("================")
# print(temp_df)
# print(df)
#
df1 = import_stock_data('sh600001', columns=['交易日期', '股票代码', '涨跌幅'])
df2 = import_stock_data('sh600002', columns=['交易日期', '股票代码', '涨跌幅'])
df1.set_index('交易日期', inplace=True)
df2.set_index('交易日期', inplace=True)

d3 = pd.DataFrame()

print(df1)

d3 = pd.concat([df1, df2])

print(d3)
