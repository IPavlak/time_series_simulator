import threading
from time import time, sleep
from copy import deepcopy
from math import copysign

from indicator import SystemIndicator
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

        self.data = None
        self.start_time = None
        self.stop_time = None
        self.use_ticks = False
        self.tick_data_idx = -1
        self.is_input_valid = False
        self.frame_data = FrameData()

        self.indicators = []

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
            # self.vis.start()
            self.control_event.set()

    def stop(self):
        self.control_event.clear()
        # self.vis.stop()
        self.reset()

    def pause(self):
        self.control_event.clear()

    def step_forward(self):
        if not self.running and self.frame_data.time <= self.stop_time:
            self._update_frame_data()
            self._draw_frame()

    def step_backward(self):
        if not self.running and self.frame_data.time >= self.start_time:
            self._update_frame_data(step=-1)
            self._draw_frame()

    def reset(self):
        if self.running:
            print('[Simulator] Cannot reset simulator while running')
        else:
            self.frame_data.core_data_idx = get_idx_from_time(self.data, self.start_time)
            if self.use_ticks:
                self.tick_data_idx = get_idx_from_time(self.tick_data, self.start_time)

    def setup_simulator(self, data, start_time, stop_time, interval, use_ticks, tick_data=None):
        if self.running:
            print('[Simulator] Cannot apply setup while running')
        else:
            # All input checks
            self.is_input_valid = False
            if data is None or start_time is None or stop_time is None or use_ticks is None:
                print('[Simulator] Missing some input parameters')
            elif start_time >= stop_time:
                print('[Simulator] Start or stop time is invalid')
            elif interval < 0:
                print('[Simulator] Interval parameter is not a positive number')
            elif use_ticks and tick_data is None:
                print('[Simulator] Missing tick data')
            else:
                self._set_data(data)
                self._set_start_time(start_time)
                self._set_stop_time(stop_time)
                self._set_interval(interval)
                self.use_ticks = use_ticks
                self._set_tick_data(tick_data)
                if self.use_ticks:
                    self.tick_data_idx = get_idx_from_time(self.tick_data, self.start_time)

                self.frame_data.core_data_idx = get_idx_from_time(self.data, self.start_time)
                self.frame_data.time = self.start_time
                self.frame_data.curr_candle = None
                self.frame_data.reset = True

                self.is_input_valid = True

                if self.vis.is_running():
                    self._draw_init_frame()
                else:
                    self.vis.set_init_frame(self.frame_data)

    def _set_interval(self, interval):
        self.interval = interval

    def _set_tick_data(self, data):
        self.tick_data = data

    def _set_data(self, data):
        self.data = data
        self.vis.set_data(data)
        for indicator in self.indicators:
            indicator.set_input_data(data)

    def _set_start_time(self, time):
        ''' Time should have format yyyy-m[m]-d[d] hh:MM  - or pandas value '''
        self.start_time = time

    def _set_stop_time(self, time):
        ''' Time should have format yyyy-m[m]-d[d] hh:MM  - or pandas value '''
        self.stop_time = time

    def add_indicator(self, indicator_func, indicator_parameters={}):
        indicator = SystemIndicator(indicator_func, indicator_parameters)
        indicator.set_input_data(self.data)
        self.indicators.append(indicator)
        self.vis.add_plot(indicator)

    def run(self):
        sleep(1.0) # wait for initialization to finish

        while True:
            # sleep if visualization event source is not running
            while not self.vis.is_running():
                sleep( max(0.05, self.interval) )

            self.control_event.wait()

            start_time = time()

            self._update_frame_data()
            # self.frame_data.core_data_idx += 1
            # self.frame_data.time = self.data.Date[self.frame_data.core_data_idx]
            # self.frame_data.reset = False

            # indicators update
            for indicator in self.indicators:
                indicator.calculate(self.frame_data)

            # draw frame
            self._draw_frame()
            # frame_vis_event.wait()
            # print(self.frame_data.core_data_idx)
            # frame_vis_event.clear()
            # self.comm.update_vis_signal.emit(frame_vis_event, deepcopy(self.frame_data)) # emit signal # TODO: make note about important paradigm when sending parameters in other threads

            # print("loop time", time()-start_time)
            sleep( max(0.0, self.interval-(time()-start_time) ) )

            if self.frame_data.core_data_idx >= self.data.shape[0] or self.data.loc[self.frame_data.core_data_idx].Date >= self.stop_time:
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
            if (step > 0 and self.tick_data.Date[self.tick_data_idx] >= next_time) or \
               (step < 0 and self.tick_data.Date[self.tick_data_idx] <= prev_time):

                self.frame_data.curr_candle = Candle(candle.Date, candle.Open, candle.High, candle.Low, candle.Close)
                self.frame_data.core_data_idx += int(copysign(1, step))
                self.frame_data.time = self.data.Date[self.frame_data.core_data_idx]
            else:
                if self.frame_data.curr_candle:
                    self.frame_data.curr_candle = Candle(candle.Date, self.frame_data.curr_candle.Open, \
                                                                      max(self.frame_data.curr_candle.High, candle.Close), \
                                                                      min(self.frame_data.curr_candle.Low, candle.Close), \
                                                                      candle.Close )
                else:
                    self.frame_data.curr_candle = Candle(candle.Date, candle.Open, candle.High, candle.Low, candle.Close)

        else:
            self.frame_data.core_data_idx += step
            self.frame_data.time = self.data.Date[self.frame_data.core_data_idx]

        self.frame_data.reset = False

            
    def _draw_init_frame(self):
        frame_data = FrameData()
        frame_data.core_data_idx = get_idx_from_time(self.data, self.start_time)
        frame_data.time = self.start_time
        frame_data.curr_candle = None
        frame_data.reset = True

        self.frame_vis_event.wait()
        self.frame_vis_event.clear()
        self.comm.update_vis_signal.emit(self.frame_vis_event, deepcopy(frame_data))
