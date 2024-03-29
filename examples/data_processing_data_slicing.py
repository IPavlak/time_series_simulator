from copy import deepcopy
import pandas as pd
from time import time


#################################
print('# Benchmark getting data slices')

# # Reading from CSV

data_orig = pd.read_csv('data/EURUSD/EURUSD1.csv',index_col=0,parse_dates=True)
data_orig.index.name = 'Date'
data_orig = data_orig.reset_index(drop=False)

##############################################

# Get data slice with iloc

data = deepcopy(data_orig)
start = time()
data_slice = data.iloc[100000:150000]
t = time() - start
print("Slicing with iloc: %f" % t)
del data, data_slice

data = deepcopy(data_orig)
start = time()
data_slice = data[100000:150000]
t = time() - start
print("Slicing with []: %f" % t)
del data

data = deepcopy(data_orig)
start = time()
# date = data.Date[130456]        # this somehow works 30% faster with data_orig
date = data_slice.Date[130456]    # this takes same time as using data.Date[130456]
t = time() - start
print("Getting Date from data frame range: %f" % t)
# print(type(date))
del data, date, data_slice

print()

data = deepcopy(data_orig)
start = time()
data_slice = data.iloc[100000]
t = time() - start
print("Single data frame with iloc: %f" % t)
del data, data_slice

data = deepcopy(data_orig)
start = time()
data_slice = data.iloc[100000:100001]
t = time() - start
print("Single data frame slice with iloc: %f" % t)
del data, data_slice

data = deepcopy(data_orig)
start = time()
data_slice = data[100000:100001]
t = time() - start
print("Single data frame slice with []: %f" % t)
del data

data = deepcopy(data_orig)
start = time()
date = data_slice.Date.values[0]
t = time() - start
print("Getting Date from single data frame: %f" % t)
# print(type(date))
del data, date, data_slice

print()

data = deepcopy(data_orig)
start = time()
data_slice = data.Date[100000:150000]
t = time() - start
print("Getting column and then rows: %f" % t)
del data, data_slice

data = deepcopy(data_orig)
start = time()
data_slice = data[100000:150000].Date
t = time() - start
print("Getting rows and then column: %f" % t)
del data, data_slice

print()

# Reversing the data

data = deepcopy(data_orig)
start = time()
data_slice = data.iloc[::-1]
t = time() - start
print("Reversing with iloc: %f" % t)
del data, data_slice

data = deepcopy(data_orig)
start = time()
data_slice = data[::-1]
t = time() - start
print("Reversing with []: %f" % t)
del data, data_slice

data = deepcopy(data_orig)
data_slice = data[::-1]
start = time()
data_slice = data_slice.reset_index(drop=True)
t = time() - start
print("Resetting the index: %f" % t)
del data, data_slice

data = deepcopy(data_orig)
data_slice = data[::-1]
start = time()
data_slice = data_slice.reindex(index=data_slice.index[::-1])
t = time() - start
print("Reindexing: %f" % t)
del data, data_slice

data = deepcopy(data_orig)
data_slice = data[::-1]
start = time()
data_slice.reset_index(inplace=True, drop=True)
t = time() - start
print("Resetting the index inplace: %f" % t)
# print(data_slice)
del data, data_slice


####################################################
# CONCLUSION:
# Getting data slices is the same with iloc and using integer index with [] operator.
# Execution time is independent of data slice size

# It is about 3x faster to first select rows and then select column than vise versa when getting ranges !!!

# Resetting the index is fastest to do inplace - 1000x faster !!!
# Reindexing and reiturning data frame with new index (not inplace) is very expensive