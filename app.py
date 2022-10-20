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

# Data

data_file = 'data/EURUSD/EURUSD60.csv'
tick_data_file = 'data/EURUSD/EURUSD1.csv'

########################################

def indicator_func(data):
    return [data.iloc[0].Close]

#######################################


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # self.canvas = MplCanvas() -> maybe this is better, and I should send only Canvas to Visualization object ?
        self.vis = Visualization()
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
        start_time = pd.Timestamp('2019-1-3 00:00')
        stop_time = pd.Timestamp('2019-1-6 00:00')
        self.sim.setup_simulator(data_file, start_time, stop_time, interval=0.2, use_ticks=True, tick_data_file=tick_data_file)
        self.sim.add_indicator(indicator_name='indicator_ex1', indicator='indicators/indicator_example1.py')
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
