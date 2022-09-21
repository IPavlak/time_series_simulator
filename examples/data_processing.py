import pandas as pd
from time import time


#################################
print('# Benchmark getting data with integer as index')

# Reading from CSV

data = pd.read_csv('data/EURUSD/EURUSD1.csv',index_col=0,parse_dates=True)
data.index.name = 'Date'
data = data.reset_index(drop=False)

print('Data size: %d' % data.shape[0])

# Getting index from date
start = time()
index = data[data['Date'] == '2019-1-3 01:00'].index[0]
t = time() - start
print('Get index from date: %f (index=%d)' % (t, index))

# Getting date from index
start = time()
# date = data['Date'].iloc[130456]
# date = data.iloc[130456].Date
date = data.Date[130456]
# date = data.Date[130456:130457].index[0]
t = time() - start
print('Get date from index: %f' % t)

# Getting candle (close price) from date
start = time()
close = data[data['Date'] == '2019-1-3 01:00'].Close
t = time() - start
print('Get close price from date: %f (Close=%f)' % (t, close))

# Getting data frame from beginning to some index
start = time()
dataframe = data[600000:6124565]
t = time() - start
print('Get dataframe from beginning to some index: %f' % t)

print()
#################################
print('# Benchmark getting data with date as index')

# Reading from CSV

data = pd.read_csv('data/EURUSD/EURUSD1.csv',index_col=0,parse_dates=True)
data.index.name = 'Date'

print('Data size: %d' % data.shape[0])

# Getting index from date
start = time()
index = data.index.get_loc('2019-1-3 01:00')
t = time() - start
print('Get index from date: %f (index=%d)' % (t, index))

# Getting date from index
start = time()
date = data.index[130456]
t = time() - start
print('Get date from index: %f' % t)

# Getting candle (close price) from date
start = time()
close = data.loc['2019-1-3 01:00'].Close
t = time() - start
print('Get close price from date: %f (Close=%f)' % (t, close))

# Getting data frame from beginning to some date
start = time()
dataframe = data['2003-10-15 14:47:0':'2019-1-3 01:00']
# dataframe = data.iloc[600000:6124565]
t = time() - start
print('Get dataframe from beginning to some date: %f' % t)



################################
# CONCLUSION:
# Having integer (instead of date) as index is more efficient for most of use cases,
# of course it is less efficient when it comes to searching by dates.

# It is even more efficient at getting row index of some date, even though it has to search through date column 
# and when using date as index it should search index column which is, as noted and confirmed, much slower.
# I was using get_loc() method, maybe there is something faster.

# Also one big advantage of using integer as index is that selecting part of data frame is much faster.
# Even if selecting with iloc (when using date as index) it is nowhere near as fast as when using integer as index.
# This is probably the biggest downfall of using date as index.

# Note: it is about 4x faster to first select column and then search the rows than vise versa.