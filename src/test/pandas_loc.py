# coding: utf-8
import pandas as pd
import numpy as np

# df = pd.DataFrame(np.arange(20).reshape(4, 5), index=['ind0', 'ind1', 'ind2', 'ind3'],
#                   columns=["col0", "col1", "col2", "col3", "col4"])
# # df=pd.DataFrame({"a":[1,2,3], "b":[4,5,6]})
# print(df)
#
# print(df.iloc[1:]['col1'])
#
# print(df.mean())
#
# print(10 * [1, 2, 3])
#
# # print(df.iloc[0, "a"])
# # print(df.loc[0, "col0"])
#
#
# df = pd.DataFrame({'one': ['a', 'a', 'b', 'c'], 'two': [3, 1, 2, 3], 'three': ['C', 'B', 'C', 'A']})
# print(df)
#
# df.loc[df['two'] == 2, 'four'] = 'x'  # 修改列"one"的值，推荐使用.loc
# print(df)

# df = pd.DataFrame()
#
# df = df.append({"a": 0, "b": 1}, ignore_index=True)
# df = df.append({"a": 1, "b": 2}, ignore_index=True)
# print(df)
#
# a=None
# if len(a) <= 0:
#     print("a")
# else:
#     print("b")

df = pd.DataFrame([[4, 1, 7],
                   [5, 2, 8],
                   [6, 3, 9],
                   [np.nan, np.nan, np.nan]],

                  columns=['A', 'B', 'C'])

df.fillna(0, inplace=True)
print(df)

print("===")

print(df.iloc[-1]['A'])


# series = df.agg(lambda x: (x+1).prod(), axis="rows")
# series.sort_values(ascending=False, inplace=True)
# print(series)
# print(series[:2].index)
