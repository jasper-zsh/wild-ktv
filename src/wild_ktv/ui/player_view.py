from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt6.QtMultimediaWidgets import QVideoWidget

from wild_ktv.ui.control_bar import ControlBar
from wild_ktv import share

class PlayerView(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)

        self.controlBar = ControlBar()

        self.videoWidget = QVideoWidget()
        share.context.player.setVideoOutput(self.videoWidget)

        self.vBoxLayout.addWidget(self.videoWidget)
        self.vBoxLayout.addWidget(self.controlBar)

        self.videoWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)