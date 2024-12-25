import ctypes
import logging

from mpv import MPV, MpvRenderContext, MpvGlGetProcAddressFn, MpvEvent, MpvEventEndFile

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QOpenGLContext

logger = logging.getLogger(__name__)

class MPVPlayer(QObject):
    eof = pyqtSignal()
    trackListChanged = pyqtSignal(list, list)
    volumeChanged = pyqtSignal(int)
    playingChanged = pyqtSignal(bool)
    durationChanged = pyqtSignal(float)
    positionChanged = pyqtSignal(float)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.mpv = MPV()
        self.video_tracks = []
        self.audio_tracks = []
        self.volume = 100
        self.mpv['cache-secs'] = 10
        @self.mpv.property_observer('track-list')
        def on_track_list(_, track_list):
            logger.info(f'track list changed: {track_list}')
            self.video_tracks = []
            self.audio_tracks = []
            for track in track_list:
                match track['type']:
                    case 'video':
                        self.video_tracks.append(track)
                    case 'audio':
                        self.audio_tracks.append(track)
            self.trackListChanged.emit(self.video_tracks, self.audio_tracks)
        @self.mpv.event_callback('end_file')
        def on_end_file(event: MpvEvent):
            logger.info(f'end file: {event.data.reason}')
            if event.data.reason == MpvEventEndFile.EOF:
                self.eof.emit()
        @self.mpv.property_observer('volume')
        def on_volume(_, vol: float):
            if int(vol) != self.volume:
                self.volumeChanged.emit(int(vol))
        @self.mpv.event_callback('playback-restart')
        def on_playback_restart(_):
            self.playingChanged.emit(self.isPlaying())
            self.volume = int(self.mpv.volume)
            self.volumeChanged.emit(self.volume)
        @self.mpv.property_observer('pause')
        def on_pause(_, paused: bool):
            self.playingChanged.emit(not paused)
        @self.mpv.property_observer('duration')
        def on_duration(_, duration: int):
            if duration:
                self.durationChanged.emit(duration)
        @self.mpv.property_observer('time-pos')
        def on_time_pos(_, position: int):
            if position:
                self.positionChanged.emit(position)
    
    def gl_get_proc_addr(self, _, name):
        ctx = QOpenGLContext.globalShareContext()
        addr = ctx.getProcAddress(name)
        return ctypes.cast(int(addr), ctypes.c_void_p).value

    def init(self):
        self.ctx = MpvRenderContext(self.mpv, 'opengl', opengl_init_params={
            'get_proc_address': MpvGlGetProcAddressFn(self.gl_get_proc_addr),
        })
    
    def setMedia(self, url: str):
        self.mpv.play(url)
        self.mpv.pause = False
    
    def stop(self):
        self.mpv.command('stop')
    
    def pause(self):
        self.mpv.pause = True

    def play(self):
        self.mpv.pause = False
    
    def setActiveAudioTrack(self, id: int):
        self.mpv.aid = id
    
    def setVolume(self, vol: int):
        self.volume = vol
        self.mpv.volume = float(vol)
    
    def isPlaying(self) -> bool:
        return not self.mpv.pause

    def seek(self, pos: float):
        self.mpv.seek(pos, 'absolute', 'exact')
