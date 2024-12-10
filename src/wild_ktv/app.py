import os
import logging
import asyncio

from kivy.app import App
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.properties import ObjectProperty, ListProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

import wild_ktv.config as Config
from wild_ktv.utils.asyncio import call_async
from wild_ktv.uix.video import EnhancedVideo
from wild_ktv.uix.playlist import Playlist
from wild_ktv.provider import BaseProvider, Song
from wild_ktv.provider.igeba import IGebaProvider

logger = logging.getLogger(__name__)

LabelBase.register(DEFAULT_FONT, fn_regular=os.path.join(os.path.dirname(__file__), 'SourceHanSansSC-Regular.ttf'))

class WildKTVApp(App):
    screen_manager: ScreenManager = ObjectProperty(None)
    main_screen_manager: ScreenManager = ObjectProperty(None)
    playlist: list[Song] = ListProperty()
    orig = BooleanProperty(False)
    video: EnhancedVideo
    playlist_modal: Playlist
    provider: BaseProvider

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_stack = []
        self.video = EnhancedVideo(play=True, allow_stretch=True)
        self.video.bind(
            loaded=self.on_video_loaded,
            eos=self.on_video_eos,
        )
        self.provider = IGebaProvider()
        self.playing = None

    def build(self):
        Window.fullscreen = 'auto'
        self.screen_manager = self.root.ids.main_screen.ids.sm
        self.main_screen_manager = self.root
        self.playlist_modal = Playlist()
        return self.root
    
    def nav_push(self, screen: str):
        self.screen_stack.append(self.screen_manager.current)
        self.screen_manager.current = screen
    
    def nav_back(self):
        if len(self.screen_stack) > 1:
            self.screen_manager.current = self.screen_stack.pop()
        else:
            self.screen_manager.current = self.screen_manager.screen_names[0]

    def to_player(self):
        self.main_screen_manager.current = 'player'
    
    def to_main(self):
        self.main_screen_manager.current = 'main'

    def add_to_playlist(self, song: Song):
        self.playlist.append(song)
    
    def on_video_loaded(self, instance, value):
        if value:
            self.on_orig(self, self.orig)

    def on_video_eos(self, instance, value):
        logger.info(f'video eos {value}')
        self.playlist = self.playlist[1:]

    def on_orig(self, instance, value):
        # pos = self.video.position
        if len(self.playlist) == 0:
            return
        song = self.playlist[0]
        if value:
            logger.info('set audio to orig.')
            self.video.select_audio_track(song.orig_channel)
        else:
            logger.info('set audio to inst.')
            self.video.select_audio_track(song.inst_channel)
        # logger.info(f'pos {pos} duration {self.video.duration} pct {pos / self.video.duration}')
        # self.video.seek(pos / self.video.duration)
    
    def on_playlist(self, instance, value: list[Song]):
        logger.info(f'playlist changed: {value}')
        if len(value) > 0:
            if self.playing != value[0]:
                self.playing = value[0]
                call_async(self._play(value[0]))
        else:
            self.playing = None
            self.video.source = ''

    async def _play(self, song: Song):
        song = await self.provider.get_song(song)
        self.video.source = song.file_url