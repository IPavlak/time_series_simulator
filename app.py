import sys
from time import sleep
import threading

import numpy as np
import pandas as pd

from PyQt5 import QtWidgets, QtCore, QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

# App
from visualizations import *
from core_simulator import *

########################################

# Reading from CSV

all_data = pd.read_csv('data/EURUSD/EURUSD60.csv',index_col=0,parse_dates=True)
all_data.index.name = 'Date'
# print(daily.shape)
# print(daily.tail(3))

########################################

# Select data you want to use
data = all_data.loc['2019-1-1 00:00' : '2019-1-7 00:00']

# use plain integer as index => in order to remove time gaps and easier plot of indicators
data = data.reset_index(drop=False)

########################################


def indicator_func(data):
    return [data.iloc[0].Close]

#######################################


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # self.canvas = MplCanvas() -> maybe this is better, and I should send only Canvas to Visualization object ?
        self.vis = Visualization(data)
        self.setCentralWidget(self.vis)

        self.comm = Communicate()
        self.comm.update_vis_signal.connect(self.vis.animation.event_source.call)

        # myDataLoop = threading.Thread(name = 'myDataLoop', target = self.run, daemon = True, args=(self.vis.start_sim, self.vis.stop_sim))
        # myDataLoop.start()
        self._run()

        self.show()

    def run(self, start_vis, stop_vis):
        sleep(1) # wait for first draw to init animation

        frame_vis_event = threading.Event()
        frame_vis_event.set()
        
        # comm.start_vis_signal.emit()
        self.vis.start_sim()
        for i in range(8):
            # print(i)
            # self.vis.update_frame_idx(i)
            frame_vis_event.wait()
            self.comm.update_vis_signal.emit(frame_vis_event, i+10)
            sleep(0.05) #TODO: check for 0.01 error
        # comm.start_vis_signal.emit()
        # for i in range(8):
        #     self.vis.update_frame_idx(i)
        #     sleep(0.5)
        self.vis.stop_sim()

    def _run(self):
        sim = Simulator(self.comm, self.vis, 0.2)
        sim._set_data(data)
        sim.add_indicator(indicator_func=indicator_func)
        sim._set_start_time(data.loc[data['Date'] >= '2019-1-3 00:00'].iloc[0].Date)
        sim._set_stop_time(data.loc[data['Date'] <= '2019-1-6 00:00'].iloc[-1].Date)
        sim.start()

''' End Class'''

# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class Communicate(QtCore.QObject):
    update_vis_signal = QtCore.pyqtSignal(threading.Event, FrameData)

''' End Class '''


app = QtWidgets.QApplication(sys.argv)
win = MainWindow()
sys.exit(app.exec_())
