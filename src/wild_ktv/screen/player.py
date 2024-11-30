import os
import logging

from kivy.lang import Builder
from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.video import Video

from wild_ktv.config import Config

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'player.kv'))

class PlayerScreen(Screen):
    current_source = StringProperty()

    def on_kv_post(self, base_widget):
        app = App.get_running_app()
        app.bind(playlist=self.on_playlist_changed)
    
    def on_playlist_changed(self, instance, value):
        logger.info(f'playlist changed: {value}')
        if len(value) > 0 and self.current_source != value[0]:
            self.current_source = os.path.join(Config['data_root'], value[0].path)