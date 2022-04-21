import sys
from time import sleep

import numpy as np
import pandas as pd

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

class Visualization(FigureCanvas):
    def __init__(self, data):
        self.fig = Figure() #figsize=(20,10), dpi=100
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
        # self.plot_ref = self.axes.plot(self.data.index, self.data.Close)
        self.bars_oc = self.axes.bar(self.data_frame.index, self.data_frame.Close-self.data_frame.Open, self.width_oc, \
                                     bottom=self.data_frame.Open, color=self.color_up)
        self.bars_hl = self.axes.bar(self.data_frame.index, self.data_frame.High-self.data_frame.Low, self.width_hl, \
                                     bottom=self.data_frame.Low, color=self.color_up)
        self.plot2_ref = self.axes.plot(self.data_frame.index, self.data_frame.Close)

        self.ani = animation.FuncAnimation(self.fig, self.animate, range(55), interval=0, blit=True)

    def animate(self, i):
        sleep(0.2)
        self.data_frame = self.data[i:i+10]
        
        self._draw_candles(self.data_frame)

        self.plot2_ref[0].set_data(np.linspace(0,9,10), self.data_frame.Close)

        # draw periodically to update y-labels and x-labels
        self.axes.set_ylim(min(self.data_frame.Low), max(self.data_frame.High))
        # self.axes.set_xlim(i, i+10)
        # self.fig.canvas.draw()
       
        return self.bars_oc.patches + self.bars_hl.patches + self.plot2_ref



    
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
        