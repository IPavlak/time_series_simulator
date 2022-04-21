#!/usr/bin/env python3

from ctypes import resize
from time import sleep, time
import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import Formatter

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

# Draw candles with pure Matplotlib (no mplfinance since it does not support blitting)

class MyFormatter(Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        """Return the label for time x at position pos."""
        ind = int(round(x))
        if ind >= len(self.dates) or ind < 0:
            return ''
        return self.dates[ind].strftime(self.fmt)


#define width of candlestick elements
width = 0.8 #.02
width2 = 0.1 #.002

# index by integer, not by date; do not drop date column
data = data.reset_index(drop=False)

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(MyFormatter(data['Date'], '%Y-%m-%d %H:%M'))

# format x-axis dates
fig.autofmt_xdate()

#rotate x-axis tick labels
locs = [1, 20, 40, 60]
plt.xticks(locs, rotation=0, ha='center')

#define up and down prices
up = data[data.Close>=data.Open]
down = data[data.Close<data.Open]

#define colors to use
col1 = 'green'
col2 = 'red'

# Animate plot

ax1 = ax.bar(data[1:11].index,data[1:11].Close-data[1:11].Open,width,bottom=data[1:11].Open,color=col1)
start = 0
def animate(i):
    global start
    if i == 0: start = time()
    if i == 50: print(time()-start)
    data_frame = data[i:i+10]

    # plot data
    for rect, candle in zip(ax1.patches, data_frame.iloc):
        rect.set_height(abs(candle.Close-candle.Open))
        rect.set_y(min(candle.Open, candle.Close))
        if candle.Open < candle.Close: rect.set_color(col1)
        else: rect.set_color(col2)
    ax.set_ylim(min(data_frame.Close), max(data_frame.Close))
    print(min(data_frame.Close))
    sleep(0.2)
    # fig.canvas.resize_event()
    # fig.canvas.draw()

    return ax1.patches
    

ani = animation.FuncAnimation(fig, animate, range(55), interval=0, blit=True)

#display candlestick chart
plt.show()