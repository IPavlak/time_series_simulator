#!/usr/bin/env python3

from ctypes import resize
from time import sleep, time
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

class EventSource:
    def __init__(self):
        self.func = None
        self.running = False
    
    def add_callback(self, func):
        self.func = func
    
    def remove_callback(self, *args):
        self.func = None
    
    def start(self):
        self.running = True

    def stop(self):
        self.running = True

    def call(self, *args):
        if self.running and self.func is not None:
            self.func(args)

class Player(animation.Animation):
    def __init__(self, fig, func, frames, interval, init_func=None):
        self.i = 0
        self.runs = True
        self.forwards = True
        self.fig = fig
        self._func = func
        self._iter_gen = lambda: iter(range(frames))
        self._args = []
        self.event_source = EventSource()
        self.setup((0.125, 0.92))
        animation.Animation.__init__(self, self.fig, event_source=self.event_source, blit=True)

    def setup(self, pos):
        playerax = self.fig.add_axes([pos[0],pos[1], 0.22, 0.04])
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(playerax)
        # bax = divider.append_axes("right", size="80%", pad=0.05)
        # sax = divider.append_axes("right", size="80%", pad=0.05)
        # fax = divider.append_axes("right", size="80%", pad=0.05)
        ofax = divider.append_axes("right", size="100%", pad=0.05)
        # self.button_oneback = matplotlib.widgets.Button(playerax, label=u'$\u29CF$')
        # self.button_back = matplotlib.widgets.Button(bax, label=u'$\u25C0$')
        # self.button_stop = matplotlib.widgets.Button(sax, label=u'$\u25A0$')
        # self.button_forward = matplotlib.widgets.Button(fax, label=u'$\u25B6$')
        self.button_oneforward = matplotlib.widgets.Button(ofax, label=u'$\u29D0$')
        # self.button_oneback.on_clicked(self.onebackward)
        # self.button_back.on_clicked(self.backward)
        # self.button_stop.on_clicked(self.stop)
        # self.button_forward.on_clicked(self.forward)
        self.button_oneforward.on_clicked(self.event_source.call)

        
    def new_frame_seq(self):
        print("new frame")
        # Use the generating function to generate a new frame sequence
        return self._iter_gen()

    def _draw_frame(self, framedata):
        # if self._cache_frame_data:
            # Save the data for potential saving of movies.
            # self._save_seq.append(framedata)

        # Make sure to respect save_count (keep only the last save_count
        # around)
        # self._save_seq = self._save_seq[-self.save_count:]

        # Call the func with framedata and args. If blitting is desired,
        # func needs to return a sequence of any artists that were modified.
        print('draw', framedata)
        self._drawn_artists = self._func(framedata, *self._args)
        if self._blit:
            if self._drawn_artists is None:
                raise RuntimeError('The animation function must return a '
                                   'sequence of Artist objects.')
            self._drawn_artists = sorted(self._drawn_artists,
                                         key=lambda x: x.get_zorder())

            # if animated, artist is excluded from regular drawing with draw() or draw_idle()
            # you have to call Axes.draw_artist() or Figure.draw_artist() explicitly on an artist
            for a in self._drawn_artists:
                a.set_animated(self._blit)  
        # self.fig.canvas.draw_idle()
        # self._drawn_artists[0].axes.draw_artist(self._drawn_artists[0])
        # self._drawn_artists[0].axes.figure.canvas.blit(self._drawn_artists[0].axes.bbox)
        ### !!! I order to draw artists with draw_idle(), simply set animated to False !!! ###

    def _pre_draw(self, framedata, blit):
        # Perform any cleaning or whatnot before the drawing of the frame.
        # This default implementation allows blit to clear the frame.
        if blit:
            print("pre draw")
            self._blit_clear(self._drawn_artists)

    def _post_draw(self, framedata, blit):
        # After the frame is rendered, this handles the actual flushing of
        # the draw, which can be a direct draw_idle() or make use of the
        # blitting.
        if blit and self._drawn_artists:
            print("post draw")
            self._blit_draw(self._drawn_artists)
        else:
            self._fig.canvas.draw_idle()

    def _init_draw(self):
        print('init draw')
        # Initialize the drawing either using the given init_func or by
        # calling the draw function with the first item of the frame sequence.
        # For blitting, the init_func should return a sequence of modified
        # artists.
        # Used on resize !!!!
        self._draw_frame(next(self.new_frame_seq()))
        self.fig.canvas.draw_idle()


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
    if i == 54: print("%d -> %f" % (i, time()-start))
    point.set_data(x[i],y[i])
    print("update", i, x[i], y[i])
    return (point,)
ani = Player(fig, update, 55, 0.1)

plt.show()