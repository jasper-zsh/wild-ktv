import os
import logging

from kivy.lang import Builder
from kivy.app import App
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen

from wild_ktv.config import Config
from wild_ktv.uix.video import EnhancedVideo

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'player.kv'))

class PlayerScreen(Screen):
    current_source = StringProperty()
    orig = BooleanProperty(True)
    video: EnhancedVideo

    def on_kv_post(self, base_widget):
        app = App.get_running_app()
        self.video = app.video
        self.ids.container.add_widget(self.video, 1)
    