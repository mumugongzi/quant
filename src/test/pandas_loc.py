# coding: utf-8
import pandas as pd
import numpy as np

df = pd.DataFrame(np.arange(20).reshape(4, 5), index=['ind0', 'ind1', 'ind2', 'ind3'],
                  columns=["col0", "col1", "col2", "col3", "col4"])
# df=pd.DataFrame({"a":[1,2,3], "b":[4,5,6]})
print(df)

print(df.iloc[1:]['col1'])

print(df.mean())

print(10 * [1, 2, 3])

# print(df.iloc[0, "a"])
# print(df.loc[0, "col0"])
