import threading
from time import time, sleep

from indicator import SystemIndicator
from visualizations import Visualization


class Simulator:
    def __init__(self, communication, visualization, interval = 0):
        self.interval = interval
        self.vis = visualization
        self.comm = communication
        self.running = False
        self.control_event = threading.Event()

        self.data = None
        self.start_time = None
        self.stop_time = None
        self.use_ticks = False
        self.is_input_valid = False
        # TODO: FrameData
        self.data_idx = 0

        self.indicators = []

        self.sim_thread = threading.Thread(name = 'myDataLoop', target = self.run, daemon = True)
        self.sim_thread.start()


    def start(self):
        if not self.is_input_valid:
            print('[Simulator] Simulator cannot start, input parameters are invalid')
        elif self.running:
            print('[Simulator] Simulator cannot start, already running')
        else:
            self.vis.start_sim()
            self.data_idx = self.start_idx()
            self.running = True
            self.control_event.set()

    def stop(self):
        self.vis.stop_sim()
        self.running = False
        self.control_event.clear()

    def pause(self):
        self.control_event.clear()

    def setup_simulator(self, data, start_time, stop_time, interval, use_ticks, tick_data=None):
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
            self._set_tick_data = tick_data

            self.is_input_valid = True

    def _set_interval(self, interval):
        self.interval = interval

    def _set_tick_data(self, data):
        self.tick_data = data

    def _set_data(self, data):
        self.data = data
        self.data_idx = 0
        self.vis.set_data(data)
        for indicator in self.indicators:
            indicator.set_input_data(data)

    def _set_start_time(self, time):
        ''' Time should have format yyyy-m[m]-d[d] hh:MM  - or pandas value '''
        self.start_time = time

    def _set_stop_time(self, time):
        ''' Time should have format yyyy-m[m]-d[d] hh:MM  - or pandas value '''
        self.stop_time = time

    def start_idx(self):
        return self.data[self.data['Date'] == self.start_time].index.values[0]

    def stop_idx(self):
        return self.data[self.data['Date'] == self.stop_time].index.values[0]


    def add_indicator(self, indicator_func, indicator_parameters={}):
        indicator = SystemIndicator(indicator_func, indicator_parameters)
        indicator.set_input_data(self.data)
        self.indicators.append(indicator)
        self.vis.add_plot(indicator)

    def run(self):
        frame_vis_event = threading.Event()
        frame_vis_event.set()

        sleep(1.0) # wait for initialization to finish

        while True:
            start_time = time()

            # sleep if visualization event source is not running
            while not self.vis.animation.event_source.is_running():
                sleep( max(0.05, self.interval) )

            self.control_event.wait()

            # indicators update
            for indicator in self.indicators:
                indicator.calculate(self.data_idx)

            # draw frame
            frame_vis_event.wait()
            print(self.data_idx)
            frame_vis_event.clear()
            self.comm.update_vis_signal.emit(frame_vis_event, self.data_idx) # emit signal

            self.data_idx += 1
            # print("loop time", time()-start_time)
            sleep( max(0.0, self.interval-(time()-start_time) ) )

            if self.data_idx >= self.data.shape[0] or self.data.loc[self.data_idx].Date >= self.stop_time:
                self.stop()
            

