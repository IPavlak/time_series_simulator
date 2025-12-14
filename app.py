import sys
from time import sleep
import threading

import numpy as np
import pandas as pd

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# App
# from ui.main import *
from ui.main_win_backend import *
from visualizations import *
from core_simulator import *

########################################

# Data

data_file = 'data/EURUSD/EURUSD60.csv'
tick_data_file = 'data/EURUSD/EURUSD1.csv'

########################################


def testRun(start_vis, stop_vis):
    sleep(1) # wait for first draw to init animation

    frame_vis_event = threading.Event()
    frame_vis_event.set()
    
    # comm.start_vis_signal.emit()
    vis.start()
    for i in range(8):
        # print(i)
        # self.vis.update_frame_idx(i)
        frame_vis_event.wait()
        comm.update_vis_signal.emit(frame_vis_event, i+10)
        sleep(0.05) #TODO: check for 0.01 error
    # comm.start_vis_signal.emit()
    # for i in range(8):
    #     self.vis.update_frame_idx(i)
    #     sleep(0.5)
    vis.stop()



# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class Communicate(QtCore.QObject):
    update_vis_signal = QtCore.pyqtSignal(threading.Event, FrameData)

''' End Class '''


def runSim():
    start_time = pd.Timestamp('2019-1-3 00:00')
    stop_time = pd.Timestamp('2019-1-6 00:00')
    sim.setup_simulator(data_file, start_time, stop_time, interval=0.2, use_ticks=False, tick_data_file=tick_data_file)
    sim.add_indicator(indicator_name='indicator_ex1', indicator='indicators/indicator_example1.py')
    sim.add_trader(trader_name='trader_ex1', trader='traders/trader_example1.py')
    # sim.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    print("screen size ", QDesktopWidget().screenGeometry(-1), QDesktopWidget().availableGeometry())
    g = app.desktop().availableGeometry(-1)
    # print(g)
    # print(self.frameSize())


    ### Visualization
    # self.canvas = MplCanvas() -> maybe this is better, and I should send only Canvas to Visualization object ?
    vis = Visualization()

    ### Communication  (Slots and signals - Qt framework)
    comm = Communicate()
    comm.update_vis_signal.connect(vis.animation.event_source.call)

    ### Simulator
    sim = Simulator(comm, vis, 1.2)

    ### User Interface
    ui = UI(sim)

    runSim()

    ui.show()
    
    sys.exit(app.exec_())
