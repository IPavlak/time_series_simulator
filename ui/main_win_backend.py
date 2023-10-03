from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtCore, QtGui
from ui.main_win import Ui_MainWindow


DOWN_ICON = QtGui.QIcon.fromTheme("go-down")
UP_ICON = QtGui.QIcon.fromTheme("go-up")

class UI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(UI, self).__init__()

        # set up user interface from generated code
        self.setupUi(self)

        # custom setup that cannot be done from QT designer
        self.settingsToggled = True

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
