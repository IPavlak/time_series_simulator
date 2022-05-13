from time import sleep

import numpy as np
import pandas as pd

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

from animation_handler import *


class DataSourceInteraface:
    def get_latest_data(self, n: int) -> list:
        """Get latest data """



class Visualization(FigureCanvas):
    def __init__(self, data):
        self.fig = Figure() #figsize=(20,10)) #, dpi=100
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        #define width of candlestick elements
        self.width_oc = 0.8 #.02
        self.width_hl = 0.1 #.002

        # define colors to use
        self.color_up = 'green'
        self.color_down = 'red'

        # Data
        self.data = data
        self.data_frame = data[0:10]
        self.frame_size = 10  # TODO: depends on window size

        # Control variables
        self.frame_idx = 0 #last frame idx
        self.make_update = False
        self.running = True

        # User defined plots
        self.plots = []
        
        # self.plot_ref = self.axes.plot(self.data.index, self.data.Close)
        self.bars_oc = self.axes.bar([], [], self.width_oc, \
                                     bottom=[], color=self.color_up)
        self.bars_hl = self.axes.bar([], [], self.width_hl, \
                                     bottom=[], color=self.color_up)
        self.plot2_ref = self.axes.plot([], [])#self.data_frame.index, self.data_frame.Close)

        # self.animation = animation.FuncAnimation(self.fig, self._animate, self._frame_idx_generator, interval=0, blit=True, repeat=False)
        self.animation = AnimationHandler(self.fig, self._animate, init_func=self._init_draw)


    def _animate(self, i):
        self.frame_idx = i
        self.data_frame = self.data[i-self.frame_size+1:i+1]
        
        self._draw_candles(self.data_frame)

        # User defined plots
        for plot, data_source in self.plots:
            plot.set_data(np.linspace(0,9,10), data_source.get_data(10))

        self.plot2_ref[0].set_data(np.linspace(0,9,10), self.data_frame.Close) # NaN for not existing values

        # draw periodically to update y-labels and x-labels
        self.axes.set_ylim(min(self.data_frame.Low), max(self.data_frame.High))
        # self.axes.set_xlim(i, i+10)
        # self.fig.canvas.draw()

        self.make_update = False
        print("draw_func", i, self.bars_hl.patches[0]._animated)
        return self.bars_oc.patches + self.bars_hl.patches + self.plot2_ref

    def _init_draw(self):
        print("_init_func", self.data_frame.Date.iloc[0], self.data_frame.Open.iloc[2] < self.data_frame.Close.iloc[2])

        self.axes.cla()
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

        self.axes.set_ylim(min(self.data_frame.Low), max(self.data_frame.High))
        
        return self.bars_oc.patches + self.bars_hl.patches


    def stop_sim(self):
        self.animation.event_source.stop()
        self.running = False

    def start_sim(self):
        self.make_update = False
        self.animation.event_source.start()
        self.running = True

    def is_running(self):
        return self.running


    def add_plot(self, data_source, **kwargs):
        plot_ref, = self.axes.plot([], [], **kwargs)
        self.plots.append((plot_ref, data_source))

    def set_data(self, data):
        self.data = data

    
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
        

if __name__ == '__main__':
    vis = Visualization(None)
    print("her")