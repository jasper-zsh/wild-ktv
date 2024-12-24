import logging

from qasync import asyncSlot
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QIODevice, QFile

from wild_ktv.provider import BaseProvider, Song
from wild_ktv.provider.igeba import IGebaProvider
from wild_ktv.provider.local import LocalProvider

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
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.orig = False

        self.player.mediaStatusChanged.connect(self._mediaStateChanged)
        # self.player.errorOccurred.connect(self._mediaError)

    def add_song_to_playlist(self, song: Song):
        self.playlist.append(song)
        self.playlistChanged.emit(self.playlist)
    
    def set_orig(self, orig: bool):
        self.orig = orig
        if self.playing:
            orig_channel = self.playing.orig_channel
            if orig_channel == 0:
                inst_channel = 1
            else:
                inst_channel = 0
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

    def _mediaError(self, error, error_string):
        logger.error(f'error when play: {error_string}')

    def _mediaStateChanged(self, mediaState: QMediaPlayer.MediaStatus):
        logger.info(f'media state changed: {mediaState}')
        match mediaState:
            case QMediaPlayer.MediaStatus.EndOfMedia:
                self.playlist.pop(0)
                self.playlistChanged.emit(self.playlist)
            case QMediaPlayer.MediaStatus.LoadedMedia:
                self.player.play()
                self.set_orig(self.orig)

    async def _play(self, song: Song):
        song = await self.provider.get_song(song)
        self.playing = song
        if 'tcp:' in song.file_url:
            url = QUrl(song.file_url)
        else:
            url = QUrl.fromLocalFile(song.file_url)
        self.player.setSource(url)
        # dev = QFile(song.file_url)
        # if not dev.open(QIODevice.OpenModeFlag.ReadOnly):
        #     logger.error(f'failed to open file {song.file_url}')
        # self.player.setSourceDevice(dev)

    def _stop(self):
        self.player.stop()
        self.player.setSource(QUrl())
        self.playing = None

context: SharedContext

def init():
    global context
    context = SharedContext()
