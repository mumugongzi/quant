# coding: utf-8
import math
import os
import talib
import numpy as np
import pandas as pd
import datetime

# os.makedirs("a/b/c/d", exist_ok=True)

# print(str("2019-01-01").replace("-", "")[2:-2])

# print([i / 2 - 1 for i in [1, 2, 3]])

# print(np.random(10))
#
# print(talib.MACD(np.arange(1.0, 100.0, 1))[-1])
# print(talib.MACD(np.arange(2.0, 200.0, 2))[-1])
# talib.MACD()


# df = pd.DataFrame.from_dict(
#     {
#      'category': {0: 'Love', 1: 'Love', 2: 'Fashion', 3: 'Fashion', 4: 'Hair', 5: 'Movies', 6: 'Movies', 7: 'Health', 8: 'Health', 9: 'Celebs', 10: 'Celebs', 11: 'Travel', 12: 'Weightloss', 13: 'Diet', 14: 'Bags'},
#      'impressions': {0: 380, 1: 374242, 2: 197, 3: 13363, 4: 4, 5: 189, 6: 60632, 7: 269, 8: 40189, 9: 138, 10: 66590, 11: 2227, 12: 22668, 13: 21707, 14: 229},
#      'date': {0: '2013-11-04', 1: '2013-11-04', 2: '2013-11-04', 3: '2013-11-04', 4: '2013-11-05', 5: '2013-11-05', 6: '2013-11-05', 7: '2013-11-05', 8: '2013-11-06', 9: '2013-11-06', 10: '2013-11-06', 11: '2013-11-07', 12: '2013-11-07', 13: '2013-11-07', 14: '2013-11-07'}, 'cpc_cpm_revenue': {0: 0.36823, 1: 474.81522000000001, 2: 0.19434000000000001, 3: 18.264220000000002, 4: 0.00080000000000000004, 5: 0.23613000000000001, 6: 81.391139999999993, 7: 0.27171000000000001, 8: 51.258200000000002, 9: 0.11536, 10: 83.966859999999997, 11: 3.43248, 12: 31.695889999999999, 13: 28.459320000000002, 14: 0.43524000000000002}, 'clicks': {0: 0, 1: 183, 2: 0, 3: 9, 4: 0, 5: 1, 6: 20, 7: 0, 8: 21, 9: 0, 10: 32, 11: 1, 12: 12, 13: 9, 14: 2}, 'size': {0: '300x250', 1: '300x250', 2: '300x250', 3: '300x250', 4: '300x250', 5: '300x250', 6: '300x250', 7: '300x250', 8: '300x250', 9: '300x250', 10: '300x250', 11: '300x250', 12: '300x250', 13: '300x250', 14: '300x250'}
#     }
# )
#
# print(df)
#
# print(df)
# df.set_index(['date', 'category'], inplace=True)
#
# print(df)
# group = df.groupby(level=[0]).apply(lambda x: x.iloc[-1]['impressions'] / x.iloc[-1]['impressions'] -1)
# print(group)
# df = pd.DataFrame({'A': ['foo', 'bar', 'foo', 'bar',
#                          'foo', 'bar'],
#                    'B': [1, 2, 3, 4, 5, 6],
#                    'C': [2.0, 5., 8., 1., 2., 9.]})
#
# print(df)
# grouped = df.groupby('A')
# print(grouped.apply(lambda x: print(x)))
# print(grouped.apply(lambda x: x[x['C'] < 3]['B'].sum()))

# a = {}
# print(a['b'])

# d1 = datetime.datetime(year=2020, month=4, day=1)
# d2 = datetime.date(year=2020, month=4, day=1)
#
# d3 = datetime.datetime(year=d2.year, )
# print(d1 <= d2)

# df = pd.DataFrame([[1, 2, 3], [4, 5, 6]], columns=['A', 'B', 'C'])
# # df.loc[df["A"] < 2, "D"] = 'a'
#
# # print(pd.isnull(df.iloc[-1]['D']))
#
# # print(df)
#
# # df["E"] = 1 / (1 + np.exp(-df["A"].values))
# df["E"] = 1 / (1 + np.exp(-df["A"].values))
# # df["E"] = math.exp(df["A"])
#
# df["L"] = np.log((df["A"].values))
#
# # print(np.exp(np.array([1,2,3])))
#
# print(df)
#
# print(1e7)

a = 0.01 / 3
print(a)

b = 1.0
for i in range(1, 500):
    b = b * (1.0 + a)

print(b)
