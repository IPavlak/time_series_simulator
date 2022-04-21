import sys
from time import sleep

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


class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure() #figsize=(20,10), dpi=100
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # self.canvas = MplCanvas()
        self.canvas = Visualization(data)
        self.setCentralWidget(self.canvas)

        # self.ani = animation.FuncAnimation(self.canvas.fig, self.animate, range(55), interval=0, blit=True)

        self.show()

    def animate(self, i):
        sleep(0.2)
        n_data = 50
        self.xdata = list(range(n_data))
        self.ydata = [random.randint(0, 10) for i in range(n_data)]
        print(len(self.xdata), len(self.ydata))
        self.plot_ref[0].set_data(self.xdata, self.ydata)
        return self.plot_ref


app = QtWidgets.QApplication(sys.argv)
win = MainWindow()
sys.exit(app.exec_())
