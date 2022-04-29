import threading
from time import time, sleep

from indicator import SystemIndicator
from time_series_simulator.visualizations import Visualization

# class VisualizationControls:
#     start_vis = None
#     stop_vis = None

class Simulator:
    def __init__(self, visualization, interval = 0):
        self.interval = interval
        self.vis = visualization
        # self.vis_control = vis_control
        self.running = False
        self.control_event = threading.Event

        self.data = None
        self.data_idx = 0

        self.indicators = []

        self.sim_thread = threading.Thread(name = 'myDataLoop', target = self.run, daemon = True)
        self.sim_thread.start()

        # Communication to main thread
        # self.comm = Communicate()
        # self.comm.start_vis_signal.connect(self.vis_control.start_vis)
        # self.comm.stop_vis_signal.connect(self.vis_control.stop_vis)


    def start(self):
        if self.data:
            self.running = True
            self.control_event.set()
        else:
            print("[Simulator] Cannot start the simulation without data")

    def stop(self):
        self.running = False
        self.control_event.clear()

    def pause(self):
        self.control_event.clear()

    def set_interval(self, interval):
        self.interval = interval

    def set_data(self, data):
        if not self.running:
            self._set_data(data)
        else:
            print("[Simulator] Cannot set new data frame while running")

    def _set_data(self, data):
        self.data = data
        self.data_idx = 0
        self.vis.set_data(data)
        for indicator in self.indicators:
            indicator.set_input_data(data)


    def add_indicator(self, indicator_func, indicator_parameters={}):
        indicator = SystemIndicator(indicator_func, indicator_parameters)
        indicator.set_input_data(self.data)
        self.indicators.append(indicator)
        self.vis.add_plot(indicator)

    def run(self):
        while True:
            start_time = time()
            self.control_event.wait()

            # indicators update
            for indicator in self.indicators:
                indicator.calculate(self.data_idx)

            # draw frame
            self.vis.update_frame_idx(self.data_idx)

            self.data_idx += 1
            sleep( max(0.0, self.interval-(time()-start_time) ) )
            

