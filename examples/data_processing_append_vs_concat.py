from datetime import datetime
import pandas as pd
from time import time


#################################
print('# Benchmark appending and concatenating selected frames with reset indexes')

# # Reading from CSV

data = pd.read_csv('data/EURUSD/EURUSD1.csv',index_col=0,parse_dates=True)
data.index.name = 'Date'
data = data.reset_index(drop=False)

##############################################

# Appending single data frame

base_data = data.iloc[100000:110000]
# print(data_slice)
data_to_append = pd.DataFrame({'Date': pd.Timestamp('2022-02-26 00:00'), 'Open': 0.8777, 'High': 8.8888, 'Low':0.8666, 'Close': 0.86767}, index=[103])

print('Data size: %d | Appending data size: %d' % (base_data.shape[0], data_to_append.shape[0]))

start = time()
appended_data = base_data.append(data_to_append, ignore_index=True)
t = time() - start
# print(appended_data)
print("Appending: %f" % t)

start = time()
concated_data = pd.concat([base_data, data_to_append], ignore_index=True)
t = time() - start
# print(concated_data)
print("Concatenating: %f" % t)

##############################################

# Appending large data

base_data = data.iloc[100000:110000]
# print(base_data)
data_to_append = data.iloc[200000:210000]
# print(data_to_append.tail(3))

print('Data size: %d | Appending data size: %d' % (base_data.shape[0], data_to_append.shape[0]))

start = time()
appended_data = base_data.append(data_to_append, ignore_index=True)
t = time() - start
# print(appended_data)
print("Appending: %f" % t)

start = time()
concated_data = pd.concat([base_data, data_to_append], ignore_index=True)
t = time() - start
# print(concated_data)
print("Concatenating: %f" % t)

##############################################

# Appending large data to single data frame

base_data = pd.DataFrame({'Date': pd.Timestamp('2022-02-26 00:00'), 'Open': 0.8777, 'High': 8.8888, 'Low':0.8666, 'Close': 0.86767}, index=[103])
# print(base_data)
data_to_append = data.iloc[200000:210000]
# print(data_to_append.head(3))

print('Data size: %d | Appending data size: %d' % (base_data.shape[0], data_to_append.shape[0]))

start = time()
appended_data = base_data.append(data_to_append, ignore_index=True)
t = time() - start
# print(appended_data)
print("Appending: %f" % t)

start = time()
concated_data = pd.concat([base_data, data_to_append], ignore_index=True)
t = time() - start
# print(concated_data)
print("Concatenating: %f" % t)



##############################################
# CONCLUSION:
# Concatenating is faster in every case and does exactly the same thing (at least for this purpose).
# Use pd.concat()