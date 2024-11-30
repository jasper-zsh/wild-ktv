import os
from kivy.app import App
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.screenmanager import ScreenManager

from wild_ktv.model import Song

LabelBase.register(DEFAULT_FONT, fn_regular=os.path.join(os.path.dirname(__file__), 'SourceHanSansSC-Regular.ttf'))

class WildKTVApp(App):
    screen_manager: ScreenManager = ObjectProperty(None)
    main_screen_manager: ScreenManager = ObjectProperty(None)
    playlist: list[Song] = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_stack = []

    def build(self):
        self.screen_manager = self.root.ids.main_screen.ids.sm
        self.main_screen_manager = self.root
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