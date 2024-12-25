import logging
import asyncio

from qasync import asyncSlot
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtWidgets import QWidget
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QOpenGLContext

from wild_ktv.provider import BaseProvider, Song
from wild_ktv.provider.igeba import IGebaProvider
from wild_ktv.provider.local import LocalProvider
from wild_ktv.player.mpv_player import MPVPlayer

logger = logging.getLogger(__name__)

class SharedContext(QObject):
    playlistChanged = pyqtSignal(list)
    origChanged = pyqtSignal(bool)
    playlist: list[Song]
    playing: Song|None

    def __init__(self):
        super().__init__()
        self.provider = IGebaProvider()
        # self.provider = LocalProvider()
        self.playlist = []
        self.playing = None
        self.playlistChanged.connect(self._playlist_changed)
        self.orig = False

        self.player = MPVPlayer()
        self.player.eof.connect(self._eof)
        self.player.playingChanged.connect(self._playingChanged)

    def add_song_to_playlist(self, song: Song):
        self.playlist.append(song)
        self.playlistChanged.emit(self.playlist)
    
    def set_orig(self, orig: bool):
        self.orig = orig
        if self.playing:
            if self.playing.orig_channel == 0:
                orig_channel = 1
                inst_channel = 2
            else:
                orig_channel = 2
                inst_channel = 1
            if orig:
                self.player.setActiveAudioTrack(orig_channel)
            else:
                self.player.setActiveAudioTrack(inst_channel)
    
    def next_song(self):
        if len(self.playlist) > 0:
            self.playlist.pop(0)
            self.playlistChanged.emit(self.playlist)
    
    @asyncSlot(list)
    async def _playlist_changed(self, playlist: list[Song]):
        if len(playlist) > 0:
            if self.playing != playlist[0]:
                await self._play(playlist[0])
        else:
            self._stop()
    
    def _playingChanged(self, playing):
        if playing:
            self.set_orig(self.orig)

    def _eof(self):
        self.playlist.pop(0)
        self.playlistChanged.emit(self.playlist)

    async def _play(self, song: Song):
        song = await self.provider.get_song(song)
        self.playing = song
        self.player.setMedia(song.file_url)

    def _stop(self):
        self.player.stop()
        self.playing = None

context: SharedContext

def init():
    global context
    context = SharedContext()
