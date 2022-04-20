#!/usr/bin/env python3

from ctypes import resize
from time import sleep, time
from tracemalloc import stop
import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.animation as animation

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

# Animate matplotlib graph

x = np.linspace(1, 100, 100)
y = np.linspace(1, 200, 100)

fig, ax = plt.subplots(1,1)
plt.show(block=False)

line = ax.plot([], [])[0]
ax.set_xlim(0, 100)
ax.set_ylim(0,200)

def animate(i):
    xf = x[i:i+10]
    yf = y[i:i+10]
    line.set_data(xf, yf)

for i in range(80):
    animate(i)
    plt.pause(0.1)
    # sleep(0.1)

plt.show()

# CONCLUSION: For animating matplotlib plot without Animation library you need to 
#             take care of running GUI event loop - plt.pause()