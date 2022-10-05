from time import sleep

import numpy as np
import pandas as pd

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import Formatter

import data_manager as dm
from animation_handler import *
from utils import *


class DataSourceInteraface:
    def get_data(self, time, n: int) -> list:
        """ Get data which corresponds to time and (n-1) previous data samples (n data samples in total) """


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


class Visualization(FigureCanvas):
    def __init__(self):
        self.fig = Figure() #figsize=(20,10)) #, dpi=100
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        #define width of candlestick elements
        self.width_oc = 0.8 #.02
        self.width_hl = 0.1 #.002

        # define colors to use
        self.color_up = 'green'
        self.color_down = 'red'

        # define x,y margins
        self.x_margin = self.width_oc
        self.y_margin = 0.1

        # define how often to show x label - i.e. 4 means every fourth candle will have x label
        self.x_tick_rate = 4

        # Data
        self.data = dm.data
        self.data_frame = None
        self.frame_size = 10  # TODO: depends on window size

        # Control variables
        self.frame_idx = 9 #last frame idx
        self.make_update = False
        self.running = True

        # User defined plots
        self.plots = []
        
        # self.plot_ref = self.axes.plot(self.data.index, self.data.Close)
        self.bars_oc = self.axes.bar([], [], self.width_oc, \
                                     bottom=[], color=self.color_up)
        self.bars_hl = self.axes.bar([], [], self.width_hl, \
                                     bottom=[], color=self.color_up)

        # self.animation = animation.FuncAnimation(self.fig, self._animate, self._frame_idx_generator, interval=0, blit=True, repeat=False)
        self.animation = AnimationHandler(self.fig, self._animate, init_func=self._init_draw)


    def _animate(self, framedata):
        new_frame = self.frame_idx != framedata.core_data_idx
        self.frame_idx = framedata.core_data_idx
        self.data_frame = self.data[self.frame_idx-self.frame_size+1 : self.frame_idx+1]

        self._set_xticks()  # TODO: check why here and how long does it take

        # User defined plots
        user_plot_artists = []
        for plot, data_source in self.plots:
            plot.set_data(self.data_frame.index, data_source.get_data(self.data.Date[self.frame_idx], self.frame_size)) # NaN for not existing values
            user_plot_artists.append(plot)

        # Candles
        if framedata.curr_candle is None or new_frame:
            self._draw_candles(self.data_frame)

        if framedata.curr_candle is not None and new_frame:
            self._draw_current_candle(framedata.curr_candle)
            print("draw tick", framedata.time, framedata.curr_candle.Date)
        elif framedata.curr_candle is not None:
            self._draw_current_candle(framedata.curr_candle)
            print("draw tick", framedata.time, framedata.curr_candle.Date)
            return [self.bars_oc.patches[-1], self.bars_hl.patches[-1]] + user_plot_artists


        # draw periodically to update y-labels and x-labels
        
        self.axes.set_ylim(min(self.data_frame.Low), max(self.data_frame.High))
        self.axes.set_xlim(self.data_frame.index[0]-self.x_margin, self.data_frame.index[-1]+self.x_margin)
        # self.fig.canvas.draw()

        print("draw_func", framedata.core_data_idx)
        print("draw time", time()-start)
        return self.bars_oc.patches + self.bars_hl.patches + user_plot_artists

    def _init_draw(self):
        if self.data_frame is None:
            raise Exception("[Visualization] Init data frame was not set")
        print("_init_func", self.data_frame.Date.iloc[0], self.data_frame.Open.iloc[2] < self.data_frame.Close.iloc[2])

        self.axes.cla()
        self._setup_x_labels()
        # self._setup_mouse_coord_label()

        self.bars_oc = self.axes.bar(self.data_frame.index, self.data_frame.Close-self.data_frame.Open, self.width_oc, \
                                     bottom=self.data_frame.Open, color=self.color_up)
        self.bars_hl = self.axes.bar(self.data_frame.index, self.data_frame.High-self.data_frame.Low, self.width_hl, \
                                     bottom=self.data_frame.Low, color=self.color_up)

        for rect, candle in zip(self.bars_oc, self.data_frame.iloc):
            if candle.Open < candle.Close: rect.set_color(self.color_up)
            else: rect.set_color(self.color_down)
        
        for rect, candle in zip(self.bars_hl, self.data_frame.iloc):
            if candle.Open < candle.Close: rect.set_color(self.color_up)
            else: rect.set_color(self.color_down)

        # User defined plots
        user_plot_artists = []
        for i in range(len(self.plots)):
            plot_ref, = self.axes.plot(self.data_frame.index, self.plots[i][1].get_data(self.data.Date[self.frame_idx], self.frame_size))
            self.plots[i] = (plot_ref, self.plots[i][1])
            user_plot_artists.append(plot_ref)

        self.axes.set_ylim(min(self.data_frame.Low), max(self.data_frame.High))

        return self.bars_oc.patches + self.bars_hl.patches + user_plot_artists


    def stop(self):
        self.animation.event_source.stop()

    def start(self):
        self.animation.event_source.start()

    def is_running(self):
        return self.animation.event_source.is_running()


    def add_plot(self, data_source, **kwargs):
        plot_ref, = self.axes.plot([], [], **kwargs)
        self.plots.append((plot_ref, data_source))

    def set_init_frame(self, data_frame):
        if not self.is_running():
            self.frame_idx = data_frame.core_data_idx
            self.data_frame = self.data[self.frame_idx-self.frame_size+1 : self.frame_idx+1]

    def _setup_x_labels(self):
        self.axes.xaxis.set_major_formatter(MyFormatter(self.data['Date'], '%Y-%m-%d %H:%M')) # TODO: initialize formatter only once
        self._set_xticks()
        # format x-axis dates
        self.fig.autofmt_xdate(bottom=0.1, rotation=0, ha='center')

    def _set_xticks(self):
        locs = range(self.data_frame.index[0], self.data_frame.index[-1]+1, self.x_tick_rate)
        self.axes.set_xticks(locs)
    
    # TODO: Optimize this code -> iloc taking most of the time (use data_frame.Close[idx] instead])
    def _draw_candles(self, data_frame):
        for rect, candle in zip(self.bars_oc, data_frame.iloc):
            rect.set_height( abs(candle.Close-candle.Open) )
            rect.set_y( min(candle.Open, candle.Close) )
            if candle.Open < candle.Close: rect.set_color(self.color_up)
            else: rect.set_color(self.color_down)
        
        for rect, candle in zip(self.bars_hl, data_frame.iloc):
            rect.set_height( abs(candle.High-candle.Low) )
            rect.set_y( min(candle.Low, candle.High) )
            if candle.Open < candle.Close: rect.set_color(self.color_up)
            else: rect.set_color(self.color_down)

        for i in range(len(data_frame.index)):
            self.bars_oc.patches[i].set_x(data_frame.index[i] - self.width_oc/2)
            self.bars_hl.patches[i].set_x(data_frame.index[i] - self.width_hl/2)


    def _draw_current_candle(self, candle):
        rect_oc = self.bars_oc.patches[-1]
        rect_hl = self.bars_hl.patches[-1]

        rect_oc.set_height( abs(candle.Close-candle.Open) )
        rect_hl.set_height( abs(candle.High-candle.Low) )

        rect_oc.set_y( min(candle.Open, candle.Close) )
        rect_hl.set_y( min(candle.Low, candle.High) )

        if candle.Open < candle.Close: 
            rect_oc.set_color(self.color_up)
            rect_hl.set_color(self.color_up)
        else: 
            rect_oc.set_color(self.color_down)
            rect_hl.set_color(self.color_down)

        

if __name__ == '__main__':
    vis = Visualization(None)
    print("her")