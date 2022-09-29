from copy import deepcopy
import pandas as pd
from time import time


#################################
print('# Benchmark getting data with integer as index')

# Reading from CSV

data_orig = pd.read_csv('data/EURUSD/EURUSD1.csv',index_col=0,parse_dates=True)
data_orig.index.name = 'Date'
data_orig = data_orig.reset_index(drop=False)

print('Data size: %d' % data_orig.shape[0])

# Getting index from date
data = deepcopy(data_orig)
start = time()
index = data[data['Date'] == '2019-1-3 01:00'].index[0]
t = time() - start
print('Get index from date: %f (index=%d)' % (t, index))
del data, index


# Getting date from index
data = deepcopy(data_orig) # pandas is doing caching and test before can optimize test after
start = time()
# date = data['Date'].iloc[130456]
# date = data.iloc[130456].Date
date = data.Date[130456]            # this somehow works 30% faster with data_orig
# date = data.Date[130456:130457].index[0]
t = time() - start
print('Get date from index: %f' % t)
del data, date

# Getting candle (close price) from date
data = deepcopy(data_orig)
start = time()
close = data[data['Date'] == '2019-1-3 01:00'].Close
t = time() - start
print('Get close price from date: %f (Close=%f)' % (t, close))
del data, close

# Getting data frame from beginning to some index
data = deepcopy(data_orig)
start = time()
dataframe = data[600000:6124565]
t = time() - start
print('Get dataframe from beginning to some index: %f' % t)
del data, dataframe

print()
#################################
print('# Benchmark getting data with date as index')

# Reading from CSV

del data_orig
data_orig = pd.read_csv('data/EURUSD/EURUSD1.csv',index_col=0,parse_dates=True)
data_orig.index.name = 'Date'

print('Data size: %d' % data_orig.shape[0])

# Getting index from date
data = deepcopy(data_orig)
start = time()
index = data.index.get_loc('2019-1-3 01:00')
t = time() - start
print('Get index from date: %f (index=%d)' % (t, index))
del data, index

# Getting date from index
data = deepcopy(data_orig)
start = time()
date = data.index[130456]
t = time() - start
print('Get date from index: %f' % t)
del data, date

# Getting candle (close price) from date
data = deepcopy(data_orig)
start = time()
close = data.loc['2019-1-3 01:00'].Close
t = time() - start
print('Get close price from date: %f (Close=%f)' % (t, close))
del data, close

# Getting data frame from beginning to some date
data = deepcopy(data_orig)
start = time()
dataframe = data['2003-10-15 14:47:0':'2019-1-3 01:00']
# dataframe = data.iloc[600000:6124565]
t = time() - start
print('Get dataframe from beginning to some date: %f' % t)
del data, dataframe



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