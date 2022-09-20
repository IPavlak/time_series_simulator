import sys
from time import sleep
import threading

import numpy as np
import pandas as pd

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QStyle, QMainWindow, QApplication

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# App
from visualizations import *
from core_simulator import *

########################################

# Reading from CSV

all_data = pd.read_csv('data/EURUSD/EURUSD60.csv', index_col=0, parse_dates=True)
all_tick_data = pd.read_csv('data/EURUSD/EURUSD1.csv', index_col=0, parse_dates=True)

# all_data.index.name = 'Date'
# print(daily.shape)
# print(daily.tail(3))

########################################

# Select data you want to use
data = all_data.loc['2019-1-1 00:00' : '2019-1-7 00:00']
tick_data = all_tick_data.loc['2019-1-1 00:00' : '2019-1-7 00:00']

# use plain integer as index => in order to remove time gaps and easier plot of indicators
data = data.reset_index(drop=False)
tick_data = tick_data.reset_index(drop=False)

# print(data)
# print(tick_data)
# exit()
########################################


def indicator_func(data):
    return [data.iloc[0].Close]

#######################################


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # self.canvas = MplCanvas() -> maybe this is better, and I should send only Canvas to Visualization object ?
        self.vis = Visualization(data)
        # self.setCentralWidget(self.vis)

        self.comm = Communicate()
        self.comm.update_vis_signal.connect(self.vis.animation.event_source.call)

        self.sim = Simulator(self.comm, self.vis, 1.2)


        widget = QWidget(self)
        vlay = QVBoxLayout(widget)
        hlay = QHBoxLayout()

        play_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaPlay')
        play_icon = self.style().standardIcon(pixmap)
        play_btn.setIcon(play_icon)
        play_btn.clicked.connect(self.sim.start)
        hlay.addWidget(play_btn)

        pause_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaPause')
        pause_icon = self.style().standardIcon(pixmap)
        pause_btn.setIcon(pause_icon)
        pause_btn.clicked.connect(self.sim.pause)
        hlay.addWidget(pause_btn)

        stop_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaStop')
        stop_icon = self.style().standardIcon(pixmap)
        stop_btn.setIcon(stop_icon)
        stop_btn.clicked.connect(self.sim.stop)
        hlay.addWidget(stop_btn)

        prev_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaSeekBackward')
        prev_icon = self.style().standardIcon(pixmap)
        prev_btn.setIcon(prev_icon)
        prev_btn.clicked.connect(self.sim.step_backward)
        hlay.addWidget(prev_btn)

        next_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaSeekForward')
        next_icon = self.style().standardIcon(pixmap)
        next_btn.setIcon(next_icon)
        next_btn.clicked.connect(self.sim.step_forward)
        hlay.addWidget(next_btn)

        vlay.addLayout(hlay)
        vlay.addWidget(self.vis)
        self.setCentralWidget(widget)
        

        # myDataLoop = threading.Thread(name = 'myDataLoop', target = self.run, daemon = True, args=(self.vis.start_sim, self.vis.stop_sim))
        # myDataLoop.start()
        self._run()

        self.show()

    def run(self, start_vis, stop_vis):
        sleep(1) # wait for first draw to init animation

        frame_vis_event = threading.Event()
        frame_vis_event.set()
        
        # comm.start_vis_signal.emit()
        self.vis.start()
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
        self.vis.stop()

    def _run(self):
        # sim = Simulator(self.comm, self.vis, 1.2)
        start_time = data.loc[data['Date'] >= '2019-1-3 00:00'].iloc[0].Date
        stop_time = data.loc[data['Date'] <= '2019-1-6 00:00'].iloc[-1].Date
        self.sim.setup_simulator(data, start_time, stop_time, 0.2, True, tick_data=tick_data)
        self.sim.add_indicator(indicator_func=indicator_func, init_func=indicator_func)
        self.sim.start()

''' End Class'''

# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class Communicate(QtCore.QObject):
    update_vis_signal = QtCore.pyqtSignal(threading.Event, FrameData)

''' End Class '''


app = QApplication(sys.argv)
win = MainWindow()
sys.exit(app.exec_())
