#!/usr/bin/env python3

import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

########################################

# Reading from CSV

all_data = pd.read_csv('data/EURUSD/EURUSD60.csv',index_col=0,parse_dates=True)
all_data.index.name = 'Date'
# print(daily.shape)
# print(daily.tail(3))

########################################

# Select data you want to use
data = all_data.loc['2019-1-1 00:00' : '2019-1-7 00:00']

########################################

# Plot data with MPLFinance
mpf.plot(data, type='candle')
mpf.show()