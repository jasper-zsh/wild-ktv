import os
import logging
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

logger = logging.getLogger(__name__)

Builder.load_file(os.path.join(os.path.dirname(__file__), 'controlbar.kv'))

class ControlBar(BoxLayout):
    main_screen_manager = ObjectProperty(None)
    player_screen_state = StringProperty('main')
    
    def on_main_screen_manager(self, receiver, value: ScreenManager):
        value.bind(current=self.on_main_sm_current_change)
    
    def on_main_sm_current_change(self, instance, value):
        logger.info(f'main screen changed to {value}')
        self.player_screen_state = value
