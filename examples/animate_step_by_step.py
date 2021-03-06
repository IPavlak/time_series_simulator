#!/usr/bin/env python3

from ctypes import resize
from time import sleep, time
from tracemalloc import stop
import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import Formatter
import mpl_toolkits.axes_grid1
import matplotlib.widgets

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

# Animate graph step-by-step

class Player(animation.FuncAnimation):
    def __init__(self, fig, func, frames=None, init_func=None, fargs=None,
                 save_count=None, mini=0, maxi=100, pos=(0.125, 0.92), **kwargs):
        self.i = 0
        self.min=mini
        self.max=maxi
        self.runs = True
        self.forwards = True
        self.fig = fig
        self.func = func
        self.setup(pos)
        animation.FuncAnimation.__init__(self,self.fig, self.func, frames=self.play(), 
                                           init_func=init_func, fargs=fargs, repeat=True,
                                           save_count=save_count, interval=0, blit=True, **kwargs )    

    def play(self):
        while self.runs:
            self.i = self.i+self.forwards-(not self.forwards)
            if self.i > self.min and self.i < self.max:
                yield self.i
            else:
                # self.stop()
                self.i = 0
                yield self.i

    def start(self):
        # this part is to support blitting
        for a in self._drawn_artists:
            a.set_animated(True)

        self.runs=True
        self.event_source.start()

    def stop(self, event=None):
        #this part is to support blitting
        for a in self._drawn_artists:
            a.set_animated(False)

        # self.runs = False
        self.event_source.stop()

    def forward(self, event=None):
        self.forwards = True
        self.start()
    def backward(self, event=None):
        self.forwards = False
        self.start()
    def oneforward(self, event=None):
        self.forwards = True
        self.onestep()
    def onebackward(self, event=None):
        self.forwards = False
        self.onestep()

    def onestep(self):
        if self.i > self.min and self.i < self.max:
            self.i = self.i+self.forwards-(not self.forwards)
        elif self.i == self.min and self.forwards:
            self.i+=1
        elif self.i == self.max and not self.forwards:
            self.i-=1
        self.func(self.i)
        self.fig.canvas.draw_idle()

    def setup(self, pos):
        playerax = self.fig.add_axes([pos[0],pos[1], 0.22, 0.04])
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(playerax)
        bax = divider.append_axes("right", size="80%", pad=0.05)
        sax = divider.append_axes("right", size="80%", pad=0.05)
        fax = divider.append_axes("right", size="80%", pad=0.05)
        ofax = divider.append_axes("right", size="100%", pad=0.05)
        self.button_oneback = matplotlib.widgets.Button(playerax, label=u'$\u29CF$')
        self.button_back = matplotlib.widgets.Button(bax, label=u'$\u25C0$')
        self.button_stop = matplotlib.widgets.Button(sax, label=u'$\u25A0$')
        self.button_forward = matplotlib.widgets.Button(fax, label=u'$\u25B6$')
        self.button_oneforward = matplotlib.widgets.Button(ofax, label=u'$\u29D0$')
        self.button_oneback.on_clicked(self.onebackward)
        self.button_back.on_clicked(self.backward)
        self.button_stop.on_clicked(self.stop)
        self.button_forward.on_clicked(self.forward)
        self.button_oneforward.on_clicked(self.oneforward)

### using this class is as easy as using FuncAnimation:            

fig, ax = plt.subplots()
x = np.linspace(0,6*np.pi, num=100)
y = np.sin(x)

ax.plot(x,y)
point, = ax.plot([],[], marker="o", color="crimson", ms=15)

start = 0; stop = 0
def update(i):
    global start, stop
    # sleep(0.001)  ->  here we will implement wait until calculated ( CONCLUSION )
    if i == 0: start = time()
    if i == 98: print("%d -> %f" % (i, time()-start))
    point.set_data(x[i],y[i])
    return (point,)

ani = Player(fig, update, maxi=len(y)-1)

plt.show()
