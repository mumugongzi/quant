# coding: utf-8

import pandas as pd

df1 = pd.DataFrame([[1, 3], [2, 4]], columns=['A', 'B'])
df2 = pd.DataFrame([[11, 31], [12, 14]], columns=['A', 'B'])

print(2 * df1)
print(df2)

print(df1 + df2)

print(pd.Series({"a": 1, "b": 2}))
print(pd.Series({"a": 1, "b": 2}).index)

import datetime

print(datetime.date(year=2019, month=1, day=1) + datetime.timedelta(days=-30))
