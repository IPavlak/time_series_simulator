import threading
from time import time, sleep
from copy import deepcopy
from math import copysign
from os.path import exists

import data_manager as dm
from indicator_handler import IndicatorHandler
from trader_handler import TraderHandler
from visualizations import Visualization
from utils import *


class Simulator:
    # TODO: remove interval from init arguments
    def __init__(self, communication, visualization, interval = 0):
        self.interval = interval
        self.vis = visualization
        self.comm = communication
        self.control_event = threading.Event()
        self.frame_vis_event = threading.Event()
        self.frame_vis_event.set()

        self.data = dm.data
        self.tick_data = dm.tick_data
        self.start_time = None
        self.stop_time = None
        self.use_ticks = False
        self.tick_data_idx = -1
        self.is_input_valid = False
        self.frame_data = FrameData()

        self.indicator_handler = IndicatorHandler()
        self.trader_handler = TraderHandler(self.indicator_handler)

        self.sim_thread = threading.Thread(name = 'myDataLoop', target = self.run, daemon = True)
        self.sim_thread.start()

    @property
    def running(self):
        return self.control_event.is_set()

    def start(self):
        if not self.is_input_valid:
            print('[Simulator] Simulator cannot start, input parameters are invalid')
        elif self.running:
            print('[Simulator] Simulator cannot start, already running')
        else:
            self.control_event.set()

    def stop(self):
        self.control_event.clear()
        self.reset()

    def pause(self):
        self.control_event.clear()

    def step_forward(self):
        if not self.running and self.frame_data.time <= self.stop_time:
            self._update_frame_data()
            self.indicator_handler.update(self.frame_data)
            self.trader_handler.update(self.frame_data)
            self._draw_frame()

    def step_backward(self):
        if not self.running and self.frame_data.time >= self.start_time:
            self._update_frame_data(step=-1)
            self.indicator_handler.update(self.frame_data)
            self.trader_handler.update(self.frame_data)
            self._draw_frame()

    def reset(self):
        if self.running:
            print('[Simulator] Cannot reset simulator while running')
        else:
            self.frame_data.core_data_idx = get_idx_from_time(self.data, self.start_time)
            if self.use_ticks:
                self.tick_data_idx = get_idx_from_time(self.tick_data, self.start_time)
            self.frame_data.curr_candle = None
            # TODO: reset indicators and traders

    def setup_simulator(self, data_file, start_time, stop_time, interval, use_ticks, tick_data_file=None):
        if self.running:
            print('[Simulator] Cannot apply setup while running')
        else:
            # All input checks
            self.is_input_valid = False
            if data_file is None or start_time is None or stop_time is None or use_ticks is None:
                print('[Simulator] Missing some input parameters')
            elif not exists(data_file):
                print('[Simulator] Cannot find data file: %s' % data_file)
            elif start_time >= stop_time:
                print('[Simulator] Start or stop time is invalid')
            elif interval < 0:
                print('[Simulator] Interval parameter must be a positive number')
            elif use_ticks and tick_data_file is None:
                print('[Simulator] Missing tick data')
            elif not exists(tick_data_file):
                print('[Simulator] Cannot find tick data file: %s' % tick_data_file)
            else:
                self._load_data(data_file)
                self._set_start_time(start_time)
                self._set_stop_time(stop_time)
                self._set_interval(interval)
                self.use_ticks = use_ticks
                if self.use_ticks:
                    self._load_tick_data(tick_data_file)
                    self.tick_data_idx = get_idx_from_time(self.tick_data, self.start_time)

                self.frame_data.core_data_idx = get_idx_from_time(self.data, self.start_time, op='GREATER_OR_EQUAL')
                self.frame_data.time = self.start_time
                self.frame_data.curr_candle = None
                self.frame_data.reset = True

                self.is_input_valid = True

                self.indicator_handler.set_init_frame(self.frame_data.core_data_idx)
                self.trader_handler.set_init_frame(self.frame_data.core_data_idx)
                self.comm.init_frame_signal.emit(deepcopy(self.frame_data))
                self._draw_init_frame()
                    

    def _set_interval(self, interval):
        self.interval = interval

    def _load_tick_data(self, data_file):
        self.tick_data.load_data(data_file)
    
    def _load_data(self, data_file):
        self.data.load_data(data_file)

    def _set_start_time(self, time):
        ''' Time should have format yyyy-m[m]-d[d] hh:MM  - or pandas value '''
        self.start_time = time

    def _set_stop_time(self, time):
        ''' Time should have format yyyy-m[m]-d[d] hh:MM  - or pandas value '''
        self.stop_time = time


    def add_indicator(self, indicator_name: str, indicator: str, indicator_parameters={}):
        ind = self.indicator_handler.add_indicator(indicator_name, indicator, indicator_parameters)
        self.vis.add_plot(ind, ind.parameters.visualization)
        # self.comm.add_plot_signal.emit(ind, ind.parameters.visualization)
    
    def add_trader(self, trader_name: str, trader: str, trader_parameters={}):
        trader = self.trader_handler.add_trader(trader_name, trader, trader_parameters)
        self.vis.add_plot(trader.buy_orders_data_source, trader.get_buy_vis_params())
        self.vis.add_plot(trader.sell_orders_data_source, trader.get_sell_vis_params())
        self.vis.add_plot(trader.buy_pend_orders_data_source, trader.get_buy_vis_params())
        self.vis.add_plot(trader.sell_pend_orders_data_source, trader.get_sell_vis_params())

    def run(self):
        sleep(1.0) # wait for initialization to finish

        while True:
            # sleep if visualization event source is not running
            while not self.vis.is_running():
                sleep( max(0.05, self.interval) )

            self.control_event.wait()

            start_time = time()

            self._update_frame_data()

            self.indicator_handler.update(self.frame_data)
            self.trader_handler.update(self.frame_data)

            # draw frame
            self._draw_frame()

            # print("loop time", time()-start_time)
            sleep( max(0.0, self.interval-(time()-start_time) ) )

            if self.frame_data.core_data_idx+1 >= self.data.shape[0] or self.data.Date[self.frame_data.core_data_idx+1] >= self.stop_time:
                if not self.use_ticks or (self.tick_data_idx+1 >= self.tick_data.shape[0] or self.tick_data.Date[self.tick_data_idx+1] >= self.stop_time):
                    self.stop()

    def _draw_frame(self):
        self.frame_vis_event.wait()
        print(self.frame_data.core_data_idx)
        self.frame_vis_event.clear()
        self.comm.update_vis_signal.emit(self.frame_vis_event, deepcopy(self.frame_data)) # emit signal # TODO: make note about important paradigm when sending parameters in other threads
    
    # TODO: optimize (out) iloc
    def _update_frame_data(self, step=1):
        if self.use_ticks:
            prev_time = self.data.Date[self.frame_data.core_data_idx]
            next_time = self.data.Date[self.frame_data.core_data_idx + int(copysign(1, step))]     # step is always 1 for core data when using ticks
            self.tick_data_idx += step
            candle = self.tick_data.iloc[self.tick_data_idx]
            self.frame_data.time = candle.Date
            if (step > 0 and self.tick_data.Date[self.tick_data_idx] >= next_time) or \
               (step < 0 and self.tick_data.Date[self.tick_data_idx] <  prev_time):

                self.frame_data.core_data_idx += int(copysign(1, step))
                self.frame_data.curr_candle = self._calc_curr_candle(candle, step, True)
            else:
                self.frame_data.curr_candle = self._calc_curr_candle(candle, step)

        else:
            self.frame_data.core_data_idx += step
            self.frame_data.time = self.data.Date[self.frame_data.core_data_idx]

        self.frame_data.reset = False


    def _calc_curr_candle(self, tick_candle, step, new_frame=False):
        if step > 0:
            if self.frame_data.curr_candle is None or new_frame:
                return Candle(tick_candle.Date, tick_candle.Open, tick_candle.High, tick_candle.Low, tick_candle.Close)
            else:
                return Candle(tick_candle.Date, self.frame_data.curr_candle.Open, \
                                                max(self.frame_data.curr_candle.High, tick_candle.Close), \
                                                min(self.frame_data.curr_candle.Low, tick_candle.Close), \
                                                tick_candle.Close )
        else:
            prev_time = self.data.Date[self.frame_data.core_data_idx]
            next_time = self.data.Date[self.frame_data.core_data_idx + 1]

            # find tick idx of candle at prev_time
            tick_idx = self.tick_data_idx
            while self.tick_data.Date[tick_idx] > prev_time:
                tick_idx += step
            candle = Candle(self.tick_data.Date[tick_idx], self.tick_data.Open[tick_idx], self.tick_data.High[tick_idx],
                            self.tick_data.Low[tick_idx], self.tick_data.Close[tick_idx])

            # go through the candles from prev_time to current one and build a candle
            while tick_idx <= self.tick_data_idx:
                candle.High = max(candle.High, self.tick_data.Close[tick_idx])
                candle.Low = min(candle.Low, self.tick_data.Close[tick_idx])
                candle.Close = self.tick_data.Close[tick_idx]
                tick_idx -= step

            candle.Date = tick_candle.Date
            return candle


            
    def _draw_init_frame(self):
        frame_data = FrameData()
        frame_data.core_data_idx = get_idx_from_time(self.data, self.start_time)
        frame_data.time = self.start_time
        frame_data.curr_candle = None
        frame_data.reset = True

        self.frame_vis_event.wait()
        self.frame_vis_event.clear()
        self.comm.update_vis_signal.emit(self.frame_vis_event, deepcopy(frame_data))
