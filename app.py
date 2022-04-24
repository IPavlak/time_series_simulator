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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # self.canvas = MplCanvas()
        self.vis = Visualization(data)
        self.setCentralWidget(self.vis)

        myDataLoop = threading.Thread(name = 'myDataLoop', target = self.run, daemon = True, args=(self.vis.start_sim, self.vis.stop_sim))
        myDataLoop.start()

        self.show()

    def run(self, start_vis, stop_vis):
        comm = Communicate()
        comm.start_vis_signal.connect(start_vis)
        comm.stop_vis_signal.connect(stop_vis)
        
        comm.start_vis_signal.emit()
        for i in range(8):
            self.vis.update_frame_idx(i)
            sleep(0.5)
        comm.start_vis_signal.emit()
        for i in range(8):
            self.vis.update_frame_idx(i)
            sleep(0.5)
        self.vis.stop_sim()

''' End Class'''

# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class Communicate(QtCore.QObject):
    start_vis_signal = QtCore.pyqtSignal()
    stop_vis_signal = QtCore.pyqtSignal()

''' End Class '''


app = QtWidgets.QApplication(sys.argv)
win = MainWindow()
sys.exit(app.exec_())
