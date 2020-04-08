# coding: utf-8
import os
import talib
import numpy as np

# os.makedirs("a/b/c/d", exist_ok=True)

# print(str("2019-01-01").replace("-", "")[2:-2])

# print([i / 2 - 1 for i in [1, 2, 3]])

print(np.random(10))

print(talib.MACD(np.arange(1.0, 100.0, 1))[-1])
print(talib.MACD(np.arange(2.0, 200.0, 2))[-1])
# talib.MACD()
