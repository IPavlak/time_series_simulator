import sys
from time import sleep
import threading

import numpy as np
import pandas as pd

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# App
from ui.main import *
from visualizations import *
from core_simulator import *

########################################

# Data

data_file = 'data/EURUSD/EURUSD60.csv'
tick_data_file = 'data/EURUSD/EURUSD1.csv'

########################################


def connectSimAndUI(ui, sim):
    ui.play_btn.clicked.connect(sim.start)
    ui.pause_btn.clicked.connect(sim.pause)
    ui.stop_btn.clicked.connect(sim.stop)
    ui.prev_btn.clicked.connect(sim.step_backward)
    ui.next_btn.clicked.connect(sim.step_forward)

class MainWindow():
    def __init__(self, main_window):

        # self.canvas = MplCanvas() -> maybe this is better, and I should send only Canvas to Visualization object ?
        self.vis = Visualization()
        # self.setCentralWidget(self.vis)

        self.comm = Communicate()
        self.comm.update_vis_signal.connect(self.vis.animation.event_source.call)

        self.sim = Simulator(self.comm, self.vis, 1.2)

        ui = UI()
        ui.setup_ui(main_window, self.vis)
        connectSimAndUI(ui, self.sim)


        # myDataLoop = threading.Thread(name = 'myDataLoop', target = self.run, daemon = True, args=(self.vis.start_sim, self.vis.stop_sim))
        # myDataLoop.start()
        self._run()

        main_window.show()

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
        self.sim.add_trader(trader_name='trader_ex1', trader='traders/trader_example1.py')
        # self.sim.start()

''' End Class'''

# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class Communicate(QtCore.QObject):
    update_vis_signal = QtCore.pyqtSignal(threading.Event, FrameData)

''' End Class '''


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = QMainWindow()

    print("screen size ", QDesktopWidget().screenGeometry(-1), QDesktopWidget().availableGeometry())
    g = app.desktop().availableGeometry(-1)
    # print(g)
    # print(self.frameSize())

    mw = MainWindow(win)
    
    sys.exit(app.exec_())
