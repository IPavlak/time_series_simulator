from time import sleep, time
from typing import List

import numpy as np
import pandas as pd

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import Formatter, LinearLocator
from matplotlib.pyplot import getp, setp

import data_manager as dm
from animation_handler import *
from utils import *


class DataSourceInteraface:
    def get_data(self, time, n: int) -> np.ndarray: # data is arranged in columns
        """ Get data which corresponds to time and (n-1) previous data samples (n data samples in total) """

class VisualizationParams:
    TYPE = 'Line'
    STYLE = 'Solid'
    COLOR = '#1f77b4'
    WIDTH = 2
    SIZE = 12
    subplot = False


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

class CustomLinearLocator:
    def __init__(self, numticks, offset=2):
        self.numticks = numticks
        self.offset = offset
    def __getitem__(self, pair):
        vmin = pair[0]
        vmax = pair[1]
        return range(int(vmax-self.offset), int(vmin+1), -int(self.numticks))
    def __contains__(self, item):
        return True


class Plotter:
    def __init__(self, axes, data_source, params):
        self.axes = axes
        self.data_source = data_source
        self.params = params
        self.plots = []
    
    def update_plots(self, x_values, time, n, replot=False):
        data = self.data_source.get_data(time, n)

        if replot:
            self.plots = []

        for i in range(data.shape[1]):
            if i < len(self.plots):
                self.plots[i].set_data(x_values, data[:,i])
            else:
                plot_ref, = self.axes.plot(x_values, data[:,i], **self.params[i%len(self.params)])
                self.plots.append(plot_ref)

        for i in range(data.shape[1], len(self.plots)):
            self.axes.lines.remove(self.plots[i])
        self.plots = self.plots[0:data.shape[1]]

    def get_plots(self):
        return self.plots
        

class Visualization(FigureCanvas):
    def __init__(self):
        self.fig = Figure() #figsize=(20,10)) #, dpi=100
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        self.fig.subplots_adjust(left=0.05, right=0.98, bottom=0.0, top=0.89)
        fig_size = self.fig.get_size_inches() * self.fig.dpi    # size in pixels
        self.bars_per_inch = 3
        self.xy_pos_text = self.fig.text(0.8, 0.9, "tu sam", fontsize=12)

        # define width of candlestick elements
        self.width_oc = 0.8 # absolute numbers because integers are used for x-axis, so 1 bar = 1 on x-axis
        self.width_hl = 0.1

        # define colors to use
        self.color_up = 'green'
        self.color_down = 'red'

        # define x,y margins
        self.x_margin = self.width_oc
        self.y_margin = 0.05

        # define how often to show x label - i.e. 4 means every fourth candle will have x label
        self.x_tick_rate = 10
        self.x_tick_offset = 2

        # Data
        self.data = dm.data
        self.data_frame = None
        self.frame_size = int( self.fig.get_size_inches()[0] * self.bars_per_inch )

        # Control variables
        self.frame_idx = 10


        # Event controls
        self.fig.canvas.mpl_connect('button_release_event', self.on_click)

        # User defined plots
        self.plotters = []
        
        # self.plot_ref = self.axes.plot(self.data.index, self.data.Close)
        self.bars_oc = self.axes.bar([], [], self.width_oc, \
                                     bottom=[], color=self.color_up)
        self.bars_hl = self.axes.bar([], [], self.width_hl, \
                                     bottom=[], color=self.color_up)

        # self.animation = animation.FuncAnimation(self.fig, self._animate, self._frame_idx_generator, interval=0, blit=True, repeat=False)
        self.animation = AnimationHandler(self.fig, self._animate, init_func=self._init_draw)


    def _animate(self, framedata):
        start = time()

        new_frame = self.frame_idx != framedata.core_data_idx
        self.frame_idx = framedata.core_data_idx
        self.data_frame = self.data[self.frame_idx-self.frame_size+1 : self.frame_idx+1]

        # User defined plots
        user_plot_artists = []
        for plotter in self.plotters:
            plotter.update_plots(self.data_frame.index, self.data.Date[self.frame_idx], self.frame_size)
            user_plot_artists += plotter.get_plots()

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

        
        self._set_plot_limits()

        # if redraw:
        #     self.fig.canvas.draw()
        

        print("draw_func", framedata.core_data_idx)
        print("draw time", time()-start)
        return self.bars_oc.patches + self.bars_hl.patches + user_plot_artists + [self.axes.get_xaxis(), self.axes.get_yaxis()]

    def _init_draw(self):
        if self.data_frame is None:
            print("[Visualization][_init_draw] Init data frame was not set")
            return [] # returning list of artists
        print("_init_func", self.data_frame.Date.iloc[0], self.data_frame.Open.iloc[2] < self.data_frame.Close.iloc[2])

        self.frame_size = int( self.fig.get_size_inches()[0] * self.bars_per_inch ) 
        self.data_frame = self.data[self.frame_idx-self.frame_size+1 : self.frame_idx+1]

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

        start=time()
        # User defined plots
        user_plot_artists = []
        for i in range(len(self.plotters)): # TODO: plotter in plotters
            self.plotters[i].update_plots(self.data_frame.index, self.data.Date[self.frame_idx], self.frame_size, replot=True)
            print(type(self.data_frame.index))
            print(self.data_frame.index.shape)
            user_plot_artists += self.plotters[i].get_plots()

        print("init draw timing", time()-start)
        self.axes.set_ylim(min(self.data_frame.Low), max(self.data_frame.High))
        self.axes.set_xlim(self.data_frame.index[0]-self.x_margin, self.data_frame.index[-1]+self.x_margin)

        return self.bars_oc.patches + self.bars_hl.patches + user_plot_artists + [self.axes.get_xaxis(), self.axes.get_yaxis()]


    def stop(self):
        self.animation.event_source.stop()

    def start(self):
        self.animation.event_source.start()

    def is_running(self):
        return self.animation.event_source.is_running()

    def on_click(self, event):
        print(event.xdata, event.ydata)
        print(self.data[int(event.xdata)])


    def add_plot(self, data_source, vis_params, **kwargs):
        params = self._vis_params_to_plot_params(vis_params)
        self.plotters.append(Plotter(self.axes, data_source, params))

    def set_init_frame(self, data_frame):
        if not self.is_running():
            self.frame_idx = data_frame.core_data_idx
            self.data_frame = self.data[self.frame_idx-self.frame_size+1 : self.frame_idx+1]

    def _setup_x_labels(self):
        self.axes.xaxis.set_major_formatter(MyFormatter(self.data['Date'], '%Y-%m-%d %H:%M')) # TODO: initialize formatter only once
        self.axes.xaxis.set_major_locator( 
            LinearLocator(numticks=self.x_tick_rate, presets=CustomLinearLocator(self.x_tick_rate, self.x_tick_offset)) )
        # format x-axis dates
        self.fig.autofmt_xdate(bottom=0.1, rotation=0, ha='center')

    def _set_xticks(self):
        locs = range(self.data_frame.index[0], self.data_frame.index[-1]+1, self.x_tick_rate)
        self.axes.set_xticks(locs)
    

    def _draw_candles(self, data_frame):
        for i in range(len(self.bars_oc)):
            idx = self.frame_idx - self.frame_size + 1 + i
            open = data_frame.Open[idx]
            high = data_frame.High[idx]
            low  = data_frame.Low[idx]
            close= data_frame.Close[idx]

            rect = self.bars_oc[i]
            rect.set_height( abs(close-open) )
            rect.set_y( min(open, close) )
            if open < close: rect.set_color(self.color_up)
            else: rect.set_color(self.color_down)

            rect = self.bars_hl[i]
            rect.set_height( abs(high-low) )
            rect.set_y( min(low, high) )
            if open < close: rect.set_color(self.color_up)
            else: rect.set_color(self.color_down)

        # TODO: possible optimization opportunity
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

    def _set_plot_limits(self):
        y_margin_abs = (max(self.data_frame.High) - min(self.data_frame.Low)) * self.y_margin
        self.axes.set_ylim(min(self.data_frame.Low)-y_margin_abs, max(self.data_frame.High)+y_margin_abs)
        self.axes.set_xlim(self.data_frame.index[0]-self.x_margin, self.data_frame.index[-1]+self.x_margin)

    def _vis_params_to_plot_params(self, vis_params: List[VisualizationParams]):
        params = []
        for vis_param_set in vis_params:
            param = {}
            param['color'] = vis_param_set.COLOR.lower()
            param['linestyle'] = vis_param_set.STYLE.lower() # ?
            param['markersize'] = vis_param_set.SIZE
            param['linewidth'] = vis_param_set.WIDTH
            params.append(param)
        return params
    

class AccountVisualization:
    def __init__(self):
        pass

if __name__ == '__main__':
    vis = Visualization(None)
    print("her")