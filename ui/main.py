from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QStyle, QMainWindow, QApplication, QDesktopWidget

class UI():
    def setup_ui(self, main_window, vis_window):
        # set size
        # main_window.showMaximized()

        self.widget = QWidget(main_window)
        self.vlay = QVBoxLayout(self.widget)
        self.hlay = QHBoxLayout()

        self.play_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaPlay')
        play_icon = main_window.style().standardIcon(pixmap)
        self.play_btn.setIcon(play_icon)
        # self.play_btn.clicked.connect(main_window.sim.start)
        self.hlay.addWidget(self.play_btn)

        self.pause_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaPause')
        pause_icon = main_window.style().standardIcon(pixmap)
        self.pause_btn.setIcon(pause_icon)
        # self.pause_btn.clicked.connect(main_window.sim.pause)
        self.hlay.addWidget(self.pause_btn)

        self.stop_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaStop')
        stop_icon = main_window.style().standardIcon(pixmap)
        self.stop_btn.setIcon(stop_icon)
        # self.stop_btn.clicked.connect(main_window.sim.stop)
        self.hlay.addWidget(self.stop_btn)

        self.prev_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaSeekBackward')
        prev_icon = main_window.style().standardIcon(pixmap)
        self.prev_btn.setIcon(prev_icon)
        # self.prev_btn.clicked.connect(main_window.sim.step_backward)
        self.hlay.addWidget(self.prev_btn)

        self.next_btn = QPushButton()
        pixmap = getattr(QStyle, 'SP_MediaSeekForward')
        next_icon = main_window.style().standardIcon(pixmap)
        self.next_btn.setIcon(next_icon)
        # self.next_btn.clicked.connect(main_window.sim.step_forward)
        self.hlay.addWidget(self.next_btn)

        self.vlay.addLayout(self.hlay)


        self.vlay.addWidget(vis_window)
        main_window.setCentralWidget(self.widget)