from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from qfluentwidgets import PushButton, ToolButton, PrimaryToolButton, FluentIcon, Slider, SwitchButton, IconWidget

from wild_ktv import share
from wild_ktv.provider import Song

class ControlBar(QWidget):
    togglePlayer = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.mainBoxLayout = QHBoxLayout()
        self.vBoxLayout.addLayout(self.mainBoxLayout)

        self.btnPlayer = PushButton('播放器')
        self.btnPlayer.clicked.connect(self._togglePlayer)
        self.mainBoxLayout.addWidget(self.btnPlayer)
        self.songLayout = QVBoxLayout()
        self.mainBoxLayout.addLayout(self.songLayout)
        self.lblSong = QLabel('请点歌')
        self.lblSong.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.songLayout.addWidget(self.lblSong)
        self.lblArtist = QLabel('')
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
        self.sliderVolume.setMaximum(100)
        self.sliderVolume.setMinimum(0)
        self.sliderVolume.setValue(int(share.context.audio_output.volume()*100))
        self.mainBoxLayout.addWidget(self.sliderVolume)
        self.btnReplay = ToolButton(FluentIcon.ROTATE)
        self.mainBoxLayout.addWidget(self.btnReplay)
        self.btnPlaylist = ToolButton(FluentIcon.MENU)
        self.mainBoxLayout.addWidget(self.btnPlaylist)
        self.chkOrig = SwitchButton()
        self.chkOrig.setOffText('伴唱')
        self.chkOrig.setOnText('原唱')
        self.mainBoxLayout.addWidget(self.chkOrig)

        share.context.playlistChanged.connect(self._playlistChanged)
        share.context.player.playingChanged.connect(self._playingChanged)
        share.context.audio_output.volumeChanged.connect(lambda v: self.sliderVolume.setValue(int(v*100)))
        self.sliderVolume.valueChanged.connect(lambda v: share.context.audio_output.setVolume(v/100.0))
        self.btnPlay.clicked.connect(self._playClicked)
        share.context.origChanged.connect(lambda orig: self.chkOrig.setChecked(orig))
        self.chkOrig.checkedChanged.connect(lambda orig: share.context.set_orig(orig))
        self.btnSkip.clicked.connect(lambda: share.context.next_song())
        self.btnReplay.clicked.connect(lambda: share.context.player.setPosition(0))
    
    def _togglePlayer(self):
        self.togglePlayer.emit()
    
    def _playingChanged(self, playing: bool):
        if playing:
            self.btnPlay.setIcon(FluentIcon.PAUSE)
        else:
            self.btnPlay.setIcon(FluentIcon.PLAY)
    
    def _playClicked(self):
        if share.context.player.isPlaying():
            share.context.player.pause()
        else:
            share.context.player.play()
    
    def _playlistChanged(self, playlist: list[Song]):
        if len(playlist) > 0:
            song = playlist[0]
            self.lblSong.setText(song.name)
            self.lblArtist.setText('/'.join([artist.name for artist in song.artists]))
        else:
            self.lblSong.setText('请点歌')
            self.lblArtist.setText('')