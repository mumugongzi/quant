# coding: utf-8

import numpy as np

import statsmodels.api as sm
import pandas as pd

# Generate artificial data (2 regressors + constant)
nobs = 100

X = np.random.random(nobs)

Y = 3*X + 0.1 * np.random.random(nobs)

df = pd.DataFrame({"XX": X, "YY": Y})

print(df)

X = sm.add_constant(df["XX"])

# Fit regression model
results = sm.OLS(df["YY"], X).fit()

print(results.params)
