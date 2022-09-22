from ast import operator
from datetime import datetime
import pandas as pd
from time import time


#################################
print('# Benchmark getting data slices')

# # Reading from CSV

data = pd.read_csv('data/EURUSD/EURUSD1.csv',index_col=0,parse_dates=True)
data.index.name = 'Date'
data = data.reset_index(drop=False)

##############################################

# Get data slice with iloc

start = time()
data_slice = data.iloc[100000:150000]
t = time() - start
print("Slicing with iloc: %f" % t)

start = time()
data_slice = data[100000:150000]
t = time() - start
print("Slicing with []: %f" % t)

start = time()
date = data_slice.Date
t = time() - start
print("Getting Date from data frame range: %f" % t)

print()

start = time()
data_slice = data.iloc[100000]
t = time() - start
print("Single data frame with iloc: %f" % t)

start = time()
data_slice = data.iloc[100000:100001]
t = time() - start
print("Single data frame slice with iloc: %f" % t)

start = time()
data_slice = data[100000:100001]
t = time() - start
print("Single data frame slice with []: %f" % t)

start = time()
date = data_slice.Date
t = time() - start
print("Getting Date from single data frame: %f" % t)

####################################################
# CONCLUSION:
# Getting data slices is the same with iloc and using integer index with [] operator.
# [] operator is about 20% faster.
# Execution time is independent of data slice size