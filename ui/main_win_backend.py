from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from core_simulator import Simulator
from ui.main_win import Ui_MainWindow



DOWN_ICON = QtGui.QIcon.fromTheme("go-down")
UP_ICON = QtGui.QIcon.fromTheme("go-up")
PLAY_ICON = QtGui.QIcon.fromTheme("media-playback-start")
PAUSE_ICON = QtGui.QIcon.fromTheme("media-playback-pause")

class UI(QMainWindow, Ui_MainWindow):
    def __init__(self, sim : Simulator):
        super(UI, self).__init__()

        # simulator reference to interact with
        self.sim = sim

        # set up user interface from generated code
        self.setupUi(self)

        # custom setup that cannot be done from QT designer
        self.settingsToggled = True

        self.playToggleButton.setShortcut("Space")
        self.forwardButton.setShortcut("Right")
        self.backwardButton.setShortcut("Left")
        self.stopButton.setShortcut("Ctrl+R")


    @QtCore.pyqtSlot()
    def on_settingsToggleButton_clicked(self):
        if self.settingsToggled:
            self.settingToggleContext = { 'max_height': self.settingsHlay.maximumHeight() }
            self.settingsHlay.setMaximumHeight(self.settingTabs.tabBar().height())
            self.settingsToggleButton.setIcon(UP_ICON)
        else:
            self.settingsHlay.setMaximumHeight(self.settingToggleContext['max_height'])
            self.settingsToggleButton.setIcon(DOWN_ICON)

        self.settingsToggled = not self.settingsToggled

    @QtCore.pyqtSlot()
    def on_playToggleButton_clicked(self):
        if self.sim.running:
            # self.sim.pause()
            self.playToggleButton.setIcon(PAUSE_ICON)
        else:
            # self.sim.start()
            self.playToggleButton.setIcon(PLAY_ICON)

    @QtCore.pyqtSlot()
    def on_stopButton_clicked(self):
        # self.sim.stop()
        print("clicked")
    
    @QtCore.pyqtSlot()
    def on_forwardButton_clicked(self):
        # self.sim.step_forward()
        pass

    @QtCore.pyqtSlot()
    def on_backwardButton_clicked(self):
        # self.sim.step_backward()
        pass
            
