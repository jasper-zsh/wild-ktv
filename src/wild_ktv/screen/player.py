import os
import logging

from kivy.lang import Builder
from kivy.app import App
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen

from wild_ktv.config import Config
from wild_ktv.uix.video import EnhancedVideo
from wild_ktv.uix.lrc import LyricsView
from wild_ktv.model import Song

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'player.kv'))

class PlayerScreen(Screen):
    current_source = StringProperty()
    orig = BooleanProperty(True)
    video: EnhancedVideo

    def on_kv_post(self, base_widget):
        app = App.get_running_app()
        self.video = app.video
        self.video.bind(
            loaded=self.on_video_loaded,
            position=self.on_position_updated,
        )
        self.ids.container.add_widget(self.video, 1)
        self.lrc = LyricsView()
    
    def on_position_updated(self, instance, value):
        self.lrc.position = value
    
    def on_video_loaded(self, instance, value):
        if not value:
            return
        self.ids.container.remove_widget(self.video)
        self.ids.container.remove_widget(self.lrc)
        if self.video.audio_only:
            logger.info('audio only, show lyrics')
            self.ids.container.add_widget(self.lrc, 1)
            app = App.get_running_app()
            if len(app.playlist) > 0 and app.playlist[0].lrc_path:
                self.lrc.file = app.playlist[0].lrc_path
            else:
                self.lrc.file = ''
        else:
            logger.info('has video, show video frame')
            self.ids.container.add_widget(self.video, 1)