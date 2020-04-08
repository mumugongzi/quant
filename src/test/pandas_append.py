# coding: utf-8
import pandas as pd

# df = pd.DataFrame()
#
# df = df.append({
#     "交易日期": 0,
#     "股票代码": 1,
#     "成交价": 2,
#     "成交量": 3,
#     "成交方向": 4,
#     "佣金": 5,
#     "印花税": 6,
# }, ignore_index=True, )
#
# df = df.append({
#     "交易日期": 10,
#     "股票代码": 11,
#     "成交价": 12,
#     "成交量": 13,
#     "成交方向": 14,
#     "佣金": 15,
#     "印花税": 16,
# }, ignore_index=True, )
#
# print(df['交易日期'].cummax())

df = pd.DataFrame([[1, 2], [3, 4]], columns=['c1', 'c2'])
print(df)

df2 = pd.DataFrame()
df2['交易'] = [1, 2]
df2['测试'] = df['c1']

print(df['c1'])

print(df2)
