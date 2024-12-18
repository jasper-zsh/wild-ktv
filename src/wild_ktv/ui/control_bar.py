from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt
from qfluentwidgets import PushButton, ToolButton, PrimaryToolButton, FluentIcon, Slider, SwitchButton, IconWidget

class ControlBar(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.mainBoxLayout = QHBoxLayout()
        self.vBoxLayout.addLayout(self.mainBoxLayout)

        self.btnPlayer = PushButton('播放器')
        self.mainBoxLayout.addWidget(self.btnPlayer)
        self.songLayout = QVBoxLayout()
        self.mainBoxLayout.addLayout(self.songLayout)
        self.lblSong = QLabel('请点歌')
        self.lblSong.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.songLayout.addWidget(self.lblSong)
        self.lblArtist = QLabel('歌手')
        self.lblArtist.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.songLayout.addWidget(self.lblArtist)
        self.btnPlay = PrimaryToolButton(FluentIcon.PLAY)
        self.mainBoxLayout.addWidget(self.btnPlay)
        self.btnSkip = ToolButton(FluentIcon.CHEVRON_RIGHT)
        self.mainBoxLayout.addWidget(self.btnSkip)
        iconVolume = IconWidget(FluentIcon.VOLUME)
        iconVolume.setFixedSize(20, 20)
        self.mainBoxLayout.addWidget(iconVolume)
        self.sliderVolume = Slider(Qt.Orientation.Horizontal)
        self.sliderVolume.setFixedWidth(100)
        self.mainBoxLayout.addWidget(self.sliderVolume)
        self.btnReplay = ToolButton(FluentIcon.ROTATE)
        self.mainBoxLayout.addWidget(self.btnReplay)
        self.btnPlaylist = ToolButton(FluentIcon.MENU)
        self.mainBoxLayout.addWidget(self.btnPlaylist)
        self.chkOrig = SwitchButton()
        self.chkOrig.setOffText('伴唱')
        self.chkOrig.setOnText('原唱')
        self.mainBoxLayout.addWidget(self.chkOrig)
        