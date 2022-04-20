#!/usr/bin/env python3

from time import sleep, time
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

# Animate graph

fig = mpf.figure(style='charles')
ax = fig.add_subplot(1,1,1)

start = 0
def animate(i):
    global start
    if i == 0: start=time()
    if i == 50: print(time()-start)
    if (10+i) > len(data):
        print('No more data to plot')
        # ani.event_source.stop()
        return
    d = data.iloc[i:(10+i)]
    ax.clear()
    mpf.plot(d, ax=ax, type='candle')

ani = animation.FuncAnimation(fig, animate, range(55), interval=0)

mpf.show()