from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from core_simulator import Simulator
from ui.main_win import Ui_MainWindow
from visualizations import Visualization



class UI(QMainWindow, Ui_MainWindow):
    def __init__(self, sim : Simulator, vis: Visualization):
        super(UI, self).__init__()

        # simulator reference to interact with
        self.sim = sim
        # visualization reference
        self.vis = vis

        # set up user interface from generated code
        self.setupUi(self)

        # Fix icons using standard Qt style
        self.icon_play = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        self.icon_pause = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
        self.icon_stop = self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop)
        self.icon_forward = self.style().standardIcon(QtWidgets.QStyle.SP_MediaSeekForward)
        self.icon_backward = self.style().standardIcon(QtWidgets.QStyle.SP_MediaSeekBackward)
        self.icon_up = self.style().standardIcon(QtWidgets.QStyle.SP_ArrowUp)
        self.icon_down = self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown)

        self.playToggleButton.setIcon(self.icon_play)
        self.stopButton.setIcon(self.icon_stop)
        self.forwardButton.setIcon(self.icon_forward)
        self.backwardButton.setIcon(self.icon_backward)
        self.settingsToggleButton.setIcon(self.icon_down)

        # custom setup that cannot be done from QT designer
        self.horizontalLayout.addWidget(self.vis)
        self.settingsToggled = True

        self.playToggleButton.setShortcut("Space")
        self.forwardButton.setShortcut("Right")
        self.backwardButton.setShortcut("Left")
        self.stopButton.setShortcut("Ctrl+R")

        # remove focus option to stop "Space" shortcut
        self.playToggleButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.forwardButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.backwardButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.stopButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)


    @QtCore.pyqtSlot()
    def on_settingsToggleButton_clicked(self):
        if self.settingsToggled:
            self.settingToggleContext = { 'max_height': self.settingsHlay.maximumHeight() }
            self.settingsHlay.setMaximumHeight(self.settingTabs.tabBar().height())
            self.settingsToggleButton.setIcon(self.icon_up)
        else:
            self.settingsHlay.setMaximumHeight(self.settingToggleContext['max_height'])
            self.settingsToggleButton.setIcon(self.icon_down)

        self.settingsToggled = not self.settingsToggled

    @QtCore.pyqtSlot()
    def on_playToggleButton_clicked(self):
        if self.sim.running:
            self.sim.pause()
            self.playToggleButton.setIcon(self.icon_play)
        else:
            self.sim.start()
            self.playToggleButton.setIcon(self.icon_pause)

    @QtCore.pyqtSlot()
    def on_stopButton_clicked(self):
        self.sim.stop()
    
    @QtCore.pyqtSlot()
    def on_forwardButton_clicked(self):
        self.sim.step_forward()

    @QtCore.pyqtSlot()
    def on_backwardButton_clicked(self):
        self.sim.step_backward()
            
